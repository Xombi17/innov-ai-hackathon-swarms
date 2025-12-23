"""
Flask application for WellSync AI system.

Implements Flask web framework with wellness planning endpoints,
request validation, response formatting, and comprehensive error
handling and logging for API operations.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import structlog

from wellsync_ai.utils.config import get_config
from wellsync_ai.data.database import get_database_manager
from wellsync_ai.data.shared_state import create_shared_state, get_shared_state
from wellsync_ai.data.redis_client import get_redis_manager


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class WellnessAPIError(Exception):
    """Custom exception for wellness API errors."""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "WELLNESS_API_ERROR"


def create_flask_app() -> Flask:
    """
    Create and configure Flask application for WellSync AI.
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    config = get_config()
    
    # Configure Flask app
    app.config['SECRET_KEY'] = config.flask_secret_key
    app.config['DEBUG'] = config.debug_mode
    app.config['TESTING'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS for cross-origin requests
    CORS(app, origins=config.allowed_origins)
    
    # Configure logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize database and Redis connections
    db_manager = get_database_manager()
    redis_manager = get_redis_manager()
    
    # Request context setup
    @app.before_request
    def before_request():
        """Set up request context and logging."""
        g.request_id = request.headers.get('X-Request-ID', f"req_{datetime.now().timestamp()}")
        g.start_time = datetime.now()
        
        # Log request start
        logger.info(
            "Request started",
            request_id=g.request_id,
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown')
        )
    
    @app.after_request
    def after_request(response):
        """Log request completion and add headers."""
        duration_ms = (datetime.now() - g.start_time).total_seconds() * 1000
        
        # Add response headers
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
        
        # Log request completion
        logger.info(
            "Request completed",
            request_id=g.request_id,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
    
    # Error handlers
    @app.errorhandler(WellnessAPIError)
    def handle_wellness_api_error(error: WellnessAPIError):
        """Handle custom wellness API errors."""
        logger.error(
            "Wellness API error",
            request_id=g.get('request_id'),
            error_code=error.error_code,
            message=error.message,
            status_code=error.status_code
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.message,
                'timestamp': datetime.now().isoformat()
            },
            'request_id': g.get('request_id')
        }), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors."""
        logger.error(
            "Bad request",
            request_id=g.get('request_id'),
            error=str(error)
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Invalid request format or parameters',
                'timestamp': datetime.now().isoformat()
            },
            'request_id': g.get('request_id')
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors."""
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Endpoint not found',
                'timestamp': datetime.now().isoformat()
            },
            'request_id': g.get('request_id')
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors."""
        logger.error(
            "Internal server error",
            request_id=g.get('request_id'),
            error=str(error),
            traceback=traceback.format_exc()
        )
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An internal server error occurred',
                'timestamp': datetime.now().isoformat()
            },
            'request_id': g.get('request_id')
        }), 500
    
    # Validation decorators
    def validate_json_request(required_fields: Optional[list] = None):
        """Decorator to validate JSON request format and required fields."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Check content type
                if not request.is_json:
                    raise WellnessAPIError(
                        "Request must be JSON format",
                        status_code=400,
                        error_code="INVALID_CONTENT_TYPE"
                    )
                
                # Get JSON data
                try:
                    data = request.get_json()
                    if data is None:
                        raise WellnessAPIError(
                            "Invalid JSON in request body",
                            status_code=400,
                            error_code="INVALID_JSON"
                        )
                except Exception as e:
                    raise WellnessAPIError(
                        f"JSON parsing error: {str(e)}",
                        status_code=400,
                        error_code="JSON_PARSE_ERROR"
                    )
                
                # Validate required fields
                if required_fields:
                    missing_fields = []
                    for field in required_fields:
                        if field not in data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        raise WellnessAPIError(
                            f"Missing required fields: {', '.join(missing_fields)}",
                            status_code=400,
                            error_code="MISSING_REQUIRED_FIELDS"
                        )
                
                # Add validated data to kwargs
                kwargs['request_data'] = data
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def validate_user_data(f):
        """Decorator to validate user data structure."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request_data = kwargs.get('request_data', {})
            
            # Validate user profile structure
            user_profile = request_data.get('user_profile', {})
            if not isinstance(user_profile, dict):
                raise WellnessAPIError(
                    "user_profile must be a dictionary",
                    status_code=400,
                    error_code="INVALID_USER_PROFILE"
                )
            
            # Validate constraints structure
            constraints = request_data.get('constraints', {})
            if not isinstance(constraints, dict):
                raise WellnessAPIError(
                    "constraints must be a dictionary",
                    status_code=400,
                    error_code="INVALID_CONSTRAINTS"
                )
            
            # Validate recent_data structure if present
            recent_data = request_data.get('recent_data', {})
            if recent_data and not isinstance(recent_data, dict):
                raise WellnessAPIError(
                    "recent_data must be a dictionary",
                    status_code=400,
                    error_code="INVALID_RECENT_DATA"
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    # API Routes
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        try:
            # Check database connection
            db_status = db_manager.health_check()
            
            # Check Redis connection
            redis_status = redis_manager.health_check()
            
            health_status = {
                'status': 'healthy' if db_status and redis_status else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'database': 'healthy' if db_status else 'unhealthy',
                    'redis': 'healthy' if redis_status else 'unhealthy'
                },
                'version': '0.1.0'
            }
            
            status_code = 200 if health_status['status'] == 'healthy' else 503
            
            return jsonify(health_status), status_code
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 503
    
    @app.route('/wellness-plan', methods=['POST'])
    @validate_json_request(required_fields=['user_profile', 'constraints'])
    @validate_user_data
    def generate_wellness_plan(request_data: Dict[str, Any]):
        """
        Generate wellness plan endpoint.
        
        Accepts user data and constraints, returns a comprehensive
        wellness plan coordinated across all domains.
        """
        try:
            logger.info(
                "Wellness plan generation started",
                request_id=g.request_id,
                user_id=request_data.get('user_profile', {}).get('user_id', 'anonymous')
            )
            
            # Extract and validate input data
            user_profile = request_data['user_profile']
            constraints = request_data['constraints']
            recent_data = request_data.get('recent_data', {})
            goals = request_data.get('goals', {})
            
            # Create or get shared state
            state_id = request_data.get('state_id')
            if state_id:
                shared_state = get_shared_state(state_id)
                if not shared_state:
                    raise WellnessAPIError(
                        f"Shared state not found: {state_id}",
                        status_code=404,
                        error_code="STATE_NOT_FOUND"
                    )
            else:
                shared_state = create_shared_state(user_profile.get('user_id'))
            
            # Update shared state with request data
            shared_state.update_user_profile({
                **user_profile,
                'goals': goals,
                'constraints': constraints
            })
            
            if recent_data:
                for data_type, data in recent_data.items():
                    shared_state.update_recent_data(data_type, data)
            
            # Log request
            db_manager.log_api_request(
                endpoint='/wellness-plan',
                method='POST',
                request_data=request_data,
                request_id=g.request_id,
                user_id=user_profile.get('user_id', 'anonymous')
            )
            
            # EXECUTE WORKFLOW
            # We import here to avoid circular dependencies if any
            from wellsync_ai.workflows.wellness_orchestrator import WellnessWorkflowOrchestrator
            import asyncio
            
            orchestrator = WellnessWorkflowOrchestrator()
            
            # Run async workflow in sync context
            # Note: In production, consider using Quart or async-native Flask patterns
            # For now, we use asyncio.run() or a new loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(orchestrator.execute_workflow(shared_state.state_id))
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'state_id': shared_state.state_id,
                'status': 'completed',
                'plan': result.get('plan'),
                'metadata': result.get('metadata')
            }
            
            logger.info(
                "Wellness plan generated successfully",
                request_id=g.request_id,
                state_id=shared_state.state_id
            )
            
            return jsonify(response_data), 200
            
        except WellnessAPIError:
            raise
        except Exception as e:
            logger.error(
                "Wellness plan generation failed",
                request_id=g.request_id,
                error=str(e),
                traceback=traceback.format_exc()
            )
            
            raise WellnessAPIError(
                f"Wellness plan generation failed: {str(e)}",
                status_code=500,
                error_code="WELLNESS_PLAN_GENERATION_FAILED"
            )
    
    @app.route('/wellness-plan/<state_id>', methods=['GET'])
    def get_wellness_plan_status(state_id: str):
        """
        Get wellness plan status by state ID.
        
        Returns the current status and results of a wellness plan
        generation request.
        """
        try:
            logger.info(
                "Wellness plan status requested",
                request_id=g.request_id,
                state_id=state_id
            )
            
            # Get shared state
            shared_state = get_shared_state(state_id)
            if not shared_state:
                raise WellnessAPIError(
                    f"Wellness plan not found: {state_id}",
                    status_code=404,
                    error_code="WELLNESS_PLAN_NOT_FOUND"
                )
            
            # Get state data
            state_data = shared_state.get_state_data()
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'state_id': state_id,
                'status': state_data.get('workflow_status', 'unknown'),
                'user_profile': state_data.get('user_profile'),
                'current_plans': state_data.get('current_plans', {}),
                'constraint_violations': state_data.get('constraint_violations', []),
                'last_updated': state_data.get('metadata', {}).get('last_updated'),
                'state_summary': shared_state.get_state_summary()
            }
            
            return jsonify(response_data), 200
            
        except WellnessAPIError:
            raise
        except Exception as e:
            logger.error(
                "Get wellness plan status failed",
                request_id=g.request_id,
                state_id=state_id,
                error=str(e)
            )
            
            raise WellnessAPIError(
                f"Failed to get wellness plan status: {str(e)}",
                status_code=500,
                error_code="GET_STATUS_FAILED"
            )
    
    @app.route('/wellness-plan/<state_id>/feedback', methods=['POST'])
    @validate_json_request(required_fields=['feedback'])
    def submit_wellness_plan_feedback(state_id: str, request_data: Dict[str, Any]):
        """
        Submit feedback for a wellness plan.
        
        Accepts user feedback on wellness plan recommendations
        for learning and adaptation.
        """
        try:
            logger.info(
                "Wellness plan feedback submitted",
                request_id=g.request_id,
                state_id=state_id
            )
            
            # Get shared state
            shared_state = get_shared_state(state_id)
            if not shared_state:
                raise WellnessAPIError(
                    f"Wellness plan not found: {state_id}",
                    status_code=404,
                    error_code="WELLNESS_PLAN_NOT_FOUND"
                )
            
            feedback = request_data['feedback']
            
            # Validate feedback structure
            if not isinstance(feedback, dict):
                raise WellnessAPIError(
                    "feedback must be a dictionary",
                    status_code=400,
                    error_code="INVALID_FEEDBACK"
                )
            
            # Update shared state with feedback
            shared_state.update_recent_data('user_feedback', {
                'feedback': feedback,
                'submitted_at': datetime.now().isoformat(),
                'request_id': g.request_id
            })
            
            # Store feedback in database
            db_manager.store_user_feedback(
                state_id=state_id,
                feedback=feedback,
                request_id=g.request_id
            )
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'state_id': state_id,
                'message': 'Feedback received and stored successfully',
                'feedback_summary': {
                    'domains_covered': list(feedback.keys()),
                    'total_items': len(feedback)
                }
            }
            
            return jsonify(response_data), 200
            
        except WellnessAPIError:
            raise
        except Exception as e:
            logger.error(
                "Submit wellness plan feedback failed",
                request_id=g.request_id,
                state_id=state_id,
                error=str(e)
            )
            
            raise WellnessAPIError(
                f"Failed to submit feedback: {str(e)}",
                status_code=500,
                error_code="SUBMIT_FEEDBACK_FAILED"
            )
    
    @app.route('/agents/status', methods=['GET'])
    def get_agents_status():
        """
        Get status of all wellness agents.
        
        Returns health and status information for all agents
        in the system.
        """
        try:
            logger.info(
                "Agents status requested",
                request_id=g.request_id
            )
            
            # This will be implemented when agents are integrated
            # For now, return placeholder status
            agents_status = {
                'FitnessAgent': {'status': 'not_implemented', 'health': 'unknown'},
                'NutritionAgent': {'status': 'not_implemented', 'health': 'unknown'},
                'SleepAgent': {'status': 'not_implemented', 'health': 'unknown'},
                'MentalWellnessAgent': {'status': 'not_implemented', 'health': 'unknown'},
                'CoordinatorAgent': {'status': 'not_implemented', 'health': 'unknown'}
            }
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'agents': agents_status,
                'total_agents': len(agents_status),
                'healthy_agents': 0,
                'message': 'Agent integration will be completed in subsequent tasks'
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(
                "Get agents status failed",
                request_id=g.request_id,
                error=str(e)
            )
            
            raise WellnessAPIError(
                f"Failed to get agents status: {str(e)}",
                status_code=500,
                error_code="GET_AGENTS_STATUS_FAILED"
            )
    
    return app


def run_flask_app():
    """Run the Flask application."""
    app = create_flask_app()
    config = get_config()
    
    logger.info(
        "Starting WellSync AI Flask application",
        host=config.flask_host,
        port=config.flask_port,
        debug=config.debug_mode
    )
    
    app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=config.debug_mode,
        threaded=True
    )


if __name__ == '__main__':
    run_flask_app()