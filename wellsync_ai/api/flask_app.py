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
from flasgger import Swagger, swag_from
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
    
    # Configure Swagger/OpenAPI documentation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "WellSync AI API",
            "description": "Multi-Agent Wellness System API - Generates personalized wellness plans using AI agents for Fitness, Nutrition, Sleep, and Mental Wellness.",
            "version": "1.0.0",
            "contact": {
                "name": "WellSync AI Team",
                "url": "https://wellsync.ai"
            }
        },
        "basePath": "/",
        "schemes": ["http", "https"],
        "tags": [
            {"name": "Health", "description": "API health and status endpoints"},
            {"name": "Wellness Plan", "description": "Generate and manage wellness plans"},
            {"name": "Agents", "description": "AI Agent status and management"},
            {"name": "Nutrition", "description": "Nutrition-specific endpoints"}
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
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
    @app.route('/', methods=['GET'])
    def index():
        """
        API Root
        ---
        tags:
          - Health
        summary: Get API information
        description: Returns basic API info and available endpoints
        responses:
          200:
            description: API info returned successfully
            schema:
              type: object
              properties:
                success:
                  type: boolean
                service:
                  type: string
                version:
                  type: string
                status:
                  type: string
                endpoints:
                  type: object
        """
        return jsonify({
            'success': True,
            'service': 'WellSync AI API',
            'version': '1.0.0',
            'status': 'active',
            'message': 'Welcome to the WellSync AI Multi-Agent Wellness API',
            'endpoints': {
                'health': '/health',
                'wellness_plan': '/wellness-plan (POST)',
                'agents_status': '/agents/status',
                'docs': '/docs'
            }
        }), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health Check
        ---
        tags:
          - Health
        summary: Check API health status
        description: Returns health status of API and connected services (database, Redis)
        responses:
          200:
            description: API is healthy
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [healthy, unhealthy]
                timestamp:
                  type: string
                version:
                  type: string
                services:
                  type: object
          503:
            description: API is unhealthy
        """
        try:
            # Check database connection
            db_status = db_manager.health_check()
            
            # Check Redis connection
            redis_status = redis_manager.health_check()
            
            health_status = {
                'status': 'healthy' if db_status and redis_status else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.1',
                'services': {
                    'database': {
                        'status': 'healthy' if db_status else 'unhealthy',
                        'type': 'supabase' if db_manager.use_supabase else 'sqlite'
                    },
                    'redis': 'healthy' if redis_status else 'fallback'
                }
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
        Generate Wellness Plan
        ---
        tags:
          - Wellness Plan
        summary: Generate a personalized wellness plan
        description: Uses multi-agent AI system to create coordinated fitness, nutrition, sleep, and mental wellness recommendations
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - user_profile
                - constraints
              properties:
                user_profile:
                  type: object
                  description: User profile data
                  properties:
                    user_id:
                      type: string
                    age:
                      type: integer
                    weight:
                      type: number
                    height:
                      type: number
                    fitness_level:
                      type: string
                      enum: [beginner, intermediate, advanced]
                constraints:
                  type: object
                  description: User constraints and limitations
                  properties:
                    time_available:
                      type: string
                    budget:
                      type: number
                    dietary_restrictions:
                      type: array
                      items:
                        type: string
                goals:
                  type: object
                  description: User wellness goals
        responses:
          200:
            description: Wellness plan generated successfully
            schema:
              type: object
              properties:
                success:
                  type: boolean
                plan:
                  type: object
                state_id:
                  type: string
          400:
            description: Invalid request data
          500:
            description: Plan generation failed
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
            # Using asyncio.run() ensures a fresh loop for each request, preventing thread threading issues
            result = asyncio.run(orchestrator.execute_workflow(shared_state.state_id))

            if not result:
                raise WellnessAPIError(
                    "Workflow execution returned no result",
                    status_code=500,
                    error_code="WORKFLOW_EXECUTION_FAILED"
                )

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
        Get Wellness Plan Status
        ---
        tags:
          - Wellness Plan
        summary: Get status of a wellness plan by state ID
        description: Returns current status and results of a wellness plan generation request
        parameters:
          - name: state_id
            in: path
            type: string
            required: true
            description: The state ID returned from plan generation
        responses:
          200:
            description: Plan status retrieved successfully
            schema:
              type: object
              properties:
                success:
                  type: boolean
                state_id:
                  type: string
                status:
                  type: string
                current_plans:
                  type: object
          404:
            description: Plan not found
          500:
            description: Failed to get status
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
        Submit Wellness Plan Feedback
        ---
        tags:
          - Wellness Plan
        summary: Submit feedback for a wellness plan
        description: Accepts user feedback on plan recommendations for learning and adaptation
        parameters:
          - name: state_id
            in: path
            type: string
            required: true
            description: The state ID of the plan
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - feedback
              properties:
                feedback:
                  type: object
                  description: User feedback data
                  properties:
                    rating:
                      type: integer
                    comments:
                      type: string
                    accepted:
                      type: boolean
        responses:
          200:
            description: Feedback submitted successfully
          400:
            description: Invalid feedback data
          404:
            description: Plan not found
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
        Get Agents Status
        ---
        tags:
          - Agents
        summary: Get status of all AI agents
        description: Returns health and status information for all wellness agents in the system
        responses:
          200:
            description: Agent status returned successfully
            schema:
              type: object
              properties:
                success:
                  type: boolean
                agents:
                  type: object
                  description: Status of each agent
                total_agents:
                  type: integer
                healthy_agents:
                  type: integer
                swarm_architecture:
                  type: string
          500:
            description: Failed to get agent status
        """
        try:
            logger.info(
                "Agents status requested",
                request_id=g.request_id
            )
            
            # Import agents and get real status
            from wellsync_ai.agents.fitness_agent import FitnessAgent
            from wellsync_ai.agents.nutrition_agent import NutritionAgent
            from wellsync_ai.agents.sleep_agent import SleepAgent
            from wellsync_ai.agents.mental_wellness_agent import MentalWellnessAgent
            from wellsync_ai.agents.coordinator_agent import CoordinatorAgent
            
            agents_status = {}
            healthy_count = 0
            
            # Check each agent type
            agent_classes = {
                'FitnessAgent': FitnessAgent,
                'NutritionAgent': NutritionAgent,
                'SleepAgent': SleepAgent,
                'MentalWellnessAgent': MentalWellnessAgent,
                'CoordinatorAgent': CoordinatorAgent
            }
            
            for name, agent_class in agent_classes.items():
                try:
                    # Agents are healthy if they can be instantiated
                    agent = agent_class()
                    status_info = agent.get_agent_status()
                    agents_status[name] = {
                        'status': 'active',
                        'health': 'healthy',
                        'domain': status_info.get('domain', 'unknown'),
                        'confidence_threshold': status_info.get('confidence_threshold', 0.7)
                    }
                    healthy_count += 1
                except Exception as e:
                    agents_status[name] = {
                        'status': 'error',
                        'health': 'unhealthy',
                        'error': str(e)
                    }
            
            # Add nutrition swarm agents
            try:
                from wellsync_ai.agents.nutrition_swarm import (
                    NutritionManager,
                    ConstraintBudgetAnalyst,
                    AvailabilityMapper,
                    PreferenceFatigueModeler,
                    RecoveryTimingAdvisor
                )
                
                swarm_agents = {
                    'NutritionManager': NutritionManager,
                    'ConstraintBudgetAnalyst': ConstraintBudgetAnalyst,
                    'AvailabilityMapper': AvailabilityMapper,
                    'PreferenceFatigueModeler': PreferenceFatigueModeler,
                    'RecoveryTimingAdvisor': RecoveryTimingAdvisor
                }
                
                for name, agent_class in swarm_agents.items():
                    try:
                        agent = agent_class()
                        agents_status[name] = {
                            'status': 'active',
                            'health': 'healthy',
                            'type': 'nutrition_swarm',
                            'role': 'manager' if name == 'NutritionManager' else 'worker'
                        }
                        healthy_count += 1
                    except Exception as e:
                        agents_status[name] = {
                            'status': 'error',
                            'health': 'unhealthy',
                            'error': str(e)
                        }
            except ImportError:
                pass  # Swarm not yet fully integrated
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'agents': agents_status,
                'total_agents': len(agents_status),
                'healthy_agents': healthy_count,
                'swarm_architecture': 'hierarchical'
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
    
    @app.route('/nutrition/state/<user_id>', methods=['GET'])
    def get_nutrition_state(user_id: str):
        """
        Get Nutrition State
        ---
        tags:
          - Nutrition
        summary: Get current nutrition state for a user
        description: Returns budget, availability, meal history, and nutrition targets
        parameters:
          - name: user_id
            in: path
            type: string
            required: true
            description: User ID
        responses:
          200:
            description: Nutrition state retrieved successfully
            schema:
              type: object
              properties:
                success:
                  type: boolean
                user_id:
                  type: string
                state:
                  type: object
                decision_context:
                  type: object
          500:
            description: Failed to get nutrition state
        """
        try:
            logger.info(
                "Nutrition state requested",
                request_id=g.request_id,
                user_id=user_id
            )
            
            from wellsync_ai.data.nutrition_state import get_nutrition_state as get_state
            
            state = get_state(user_id)
            context = state.get_decision_context()
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'user_id': user_id,
                'state': state.to_dict(),
                'decision_context': context
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(
                "Get nutrition state failed",
                request_id=g.request_id,
                user_id=user_id,
                error=str(e)
            )
            
            raise WellnessAPIError(
                f"Failed to get nutrition state: {str(e)}",
                status_code=500,
                error_code="GET_NUTRITION_STATE_FAILED"
            )
    
    @app.route('/nutrition/decision', methods=['POST'])
    @validate_json_request(required_fields=['user_profile'])
    def trigger_nutrition_decision(request_data: Dict[str, Any]):
        """
        Trigger Nutrition Decision
        ---
        tags:
          - Nutrition
        summary: Trigger a nutrition decision using hierarchical swarm
        description: Runs the full decision loop with all nutrition worker agents
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - user_profile
              properties:
                user_profile:
                  type: object
                  description: User profile data
                constraints:
                  type: object
                  description: User constraints
                shared_state:
                  type: object
                  description: Shared state data
        responses:
          200:
            description: Nutrition decision generated successfully
            schema:
              type: object
              properties:
                success:
                  type: boolean
                decision:
                  type: object
          400:
            description: Invalid request data
          500:
            description: Nutrition decision failed
        """
        try:
            logger.info(
                "Nutrition decision requested",
                request_id=g.request_id,
                user_id=request_data.get('user_profile', {}).get('user_id')
            )
            
            from wellsync_ai.agents.nutrition_swarm import NutritionManager
            import asyncio
            
            user_profile = request_data['user_profile']
            constraints = request_data.get('constraints', {})
            shared_state = request_data.get('shared_state', {})
            
            # Run hierarchical decision
            manager = NutritionManager()
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                manager.run_hierarchical_decision(user_profile, constraints, shared_state)
            )
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'decision': result
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(
                "Nutrition decision failed",
                request_id=g.request_id,
                error=str(e),
                traceback=traceback.format_exc()
            )
            
            raise WellnessAPIError(
                f"Nutrition decision failed: {str(e)}",
                status_code=500,
                error_code="NUTRITION_DECISION_FAILED"
            )
    
    @app.route('/nutrition/feedback', methods=['POST'])
    @validate_json_request(required_fields=['user_id', 'feedback'])
    def submit_nutrition_feedback(request_data: Dict[str, Any]):
        """
        Submit Nutrition Feedback
        ---
        tags:
          - Nutrition
        summary: Submit nutrition feedback and preferences
        description: Updates user preference state for future meal decisions
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - user_id
                - feedback
              properties:
                user_id:
                  type: string
                  description: User ID
                feedback:
                  type: object
                  description: Feedback data
                  properties:
                    rejected_items:
                      type: array
                      items:
                        type: object
                    meal_consumed:
                      type: object
                    expense:
                      type: object
        responses:
          200:
            description: Feedback processed successfully
          400:
            description: Invalid feedback data
          500:
            description: Failed to process feedback
        """
        try:
            logger.info(
                "Nutrition feedback submitted",
                request_id=g.request_id,
                user_id=request_data.get('user_id')
            )
            
            from wellsync_ai.data.nutrition_state import get_nutrition_state
            
            user_id = request_data['user_id']
            feedback = request_data['feedback']
            
            state = get_nutrition_state(user_id)
            
            # Process feedback
            if 'rejected_items' in feedback:
                for item in feedback['rejected_items']:
                    state.history.add_rejection(
                        item.get('name', item),
                        item.get('reason', '')
                    )
            
            if 'meal_consumed' in feedback:
                state.history.add_meal(feedback['meal_consumed'])
            
            if 'expense' in feedback:
                state.budget.add_expense(
                    feedback['expense'].get('amount', 0),
                    feedback['expense'].get('description', '')
                )
            
            # Recalculate fatigue
            state.history.calculate_fatigue()
            
            # Save updated state
            state.save()
            
            response_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'request_id': g.request_id,
                'user_id': user_id,
                'message': 'Nutrition feedback processed successfully',
                'updated_context': state.get_decision_context()
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(
                "Submit nutrition feedback failed",
                request_id=g.request_id,
                error=str(e)
            )
            
            raise WellnessAPIError(
                f"Failed to submit nutrition feedback: {str(e)}",
                status_code=500,
                error_code="SUBMIT_NUTRITION_FEEDBACK_FAILED"
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