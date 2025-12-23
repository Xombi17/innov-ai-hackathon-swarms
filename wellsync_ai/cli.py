#!/usr/bin/env python3
"""
Command Line Interface for WellSync AI system.

Provides commands to run the Flask application, initialize
the database, and perform system maintenance tasks.
"""

import sys
import argparse
from wellsync_ai.utils.config import get_config, validate_config, create_directories
from wellsync_ai.data.database import initialize_database
from wellsync_ai.data.redis_client import test_redis_connection
from wellsync_ai.api.flask_app import run_flask_app


def init_system():
    """Initialize the WellSync AI system."""
    print("Initializing WellSync AI system...")
    
    # Validate configuration
    print("Validating configuration...")
    if not validate_config():
        print("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    print("✓ Configuration validated")
    
    # Create directories
    print("Creating directories...")
    create_directories()
    print("✓ Directories created")
    
    # Initialize database
    print("Initializing database...")
    initialize_database()
    print("✓ Database initialized")
    
    # Test Redis connection
    print("Testing Redis connection...")
    if test_redis_connection():
        print("✓ Redis connection successful")
    else:
        print("⚠ Redis connection failed - some features may not work")
    
    print("System initialization complete!")


def run_server():
    """Run the Flask web server."""
    print("Starting WellSync AI Flask server...")
    
    # Validate configuration first
    if not validate_config():
        print("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    # Run Flask app
    run_flask_app()


def health_check():
    """Perform system health check."""
    print("Performing WellSync AI health check...")
    
    config = get_config()
    
    # Check configuration
    config_valid = validate_config()
    print(f"Configuration: {'✓ Valid' if config_valid else '✗ Invalid'}")
    
    # Check database
    try:
        from wellsync_ai.data.database import get_database_manager
        db_manager = get_database_manager()
        db_healthy = db_manager.health_check()
        print(f"Database: {'✓ Healthy' if db_healthy else '✗ Unhealthy'}")
    except Exception as e:
        print(f"Database: ✗ Error - {e}")
        db_healthy = False
    
    # Check Redis
    redis_healthy = test_redis_connection()
    print(f"Redis: {'✓ Healthy' if redis_healthy else '✗ Unhealthy'}")
    
    # Overall status
    overall_healthy = config_valid and db_healthy and redis_healthy
    print(f"\nOverall Status: {'✓ Healthy' if overall_healthy else '✗ Unhealthy'}")
    
    if not overall_healthy:
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="WellSync AI Command Line Interface")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize the WellSync AI system')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the Flask web server')
    run_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    run_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    run_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Health command
    subparsers.add_parser('health', help='Perform system health check')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_system()
    elif args.command == 'run':
        # Update config with CLI arguments if provided
        config = get_config()
        if args.host != '127.0.0.1':
            config.flask_host = args.host
        if args.port != 5000:
            config.flask_port = args.port
        if args.debug:
            config.debug_mode = True
        
        run_server()
    elif args.command == 'health':
        health_check()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()