"""
WellSync AI API Entry Point

This script serves as the entry point for the Flask application.
It can be used for local development or by the Docker container.
"""

import os
import structlog
from wellsync_ai.api.flask_app import create_flask_app

# Create the application instance
app = create_flask_app()

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info("Starting WellSync AI API", port=port, debug=debug)
    
    # Check if we need to run on a specific host (e.g., 0.0.0.0 for Docker)
    app.run(host="0.0.0.0", port=port, debug=debug)
