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
from wellsync_ai.api.utils import WellnessAPIError

# Import Blueprints
from wellsync_ai.api.routes.health import health_bp
from wellsync_ai.api.routes.wellness import wellness_bp
from wellsync_ai.api.routes.chat import chat_bp
from wellsync_ai.api.routes.nutrition import nutrition_bp
from wellsync_ai.api.routes.feedback import feedback_bp


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
    allowed = config.get_allowed_origins()
    CORS(app, origins=allowed if allowed != ["*"] else "*", supports_credentials=True)
    
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
            {"name": "Chat", "description": "AI Wellness Coach chat"},
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
    
    # Register Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(wellness_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(feedback_bp)
    
    return app