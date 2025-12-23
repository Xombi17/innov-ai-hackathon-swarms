#!/usr/bin/env python3
"""
Project initialization script for WellSync AI system.

This script sets up the complete development environment including:
- Directory creation
- Database initialization  
- Configuration validation
- Dependency verification
"""

import os
import sys
import subprocess
from pathlib import Path

def create_virtual_environment():
    """Create Python virtual environment."""
    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
    
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary project directories."""
    print("Creating project directories...")
    
    directories = [
        "data/databases",
        "data/agent_states",
        "logs",
        "wellsync_ai/agents",
        "wellsync_ai/workflows", 
        "wellsync_ai/data",
        "wellsync_ai/api",
        "wellsync_ai/memory",
        "wellsync_ai/utils",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {directory}")
    
    return True

def setup_environment_file():
    """Set up environment configuration file."""
    print("Setting up environment configuration...")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Created .env from .env.example")
            print("⚠ Please edit .env with your API keys and configuration")
        else:
            print("✗ .env.example not found")
            return False
    else:
        print("✓ .env file already exists")
    
    return True

def initialize_database():
    """Initialize the SQLite database."""
    print("Initializing database...")
    
    try:
        # Import after ensuring dependencies are installed
        from wellsync_ai.utils.config import create_directories
        from wellsync_ai.data.database import initialize_database
        
        create_directories()
        initialize_database()
        print("✓ Database initialized successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import modules: {e}")
        print("  Make sure dependencies are installed and virtual environment is activated")
        return False
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False

def test_redis_connection():
    """Test Redis connection."""
    print("Testing Redis connection...")
    
    try:
        from wellsync_ai.data.redis_client import test_redis_connection
        
        if test_redis_connection():
            print("✓ Redis connection successful")
            return True
        else:
            print("⚠ Redis connection failed - make sure Redis server is running")
            print("  Install Redis: https://redis.io/download")
            return False
    except ImportError as e:
        print(f"✗ Failed to import Redis client: {e}")
        return False
    except Exception as e:
        print(f"⚠ Redis test failed: {e}")
        return False

def validate_configuration():
    """Validate system configuration."""
    print("Validating configuration...")
    
    try:
        from wellsync_ai.utils.config import validate_config
        
        if validate_config():
            print("✓ Configuration validation passed")
            return True
        else:
            print("✗ Configuration validation failed")
            print("  Please check your .env file and API keys")
            return False
    except ImportError as e:
        print(f"✗ Failed to import configuration: {e}")
        return False
    except Exception as e:
        print(f"✗ Configuration validation error: {e}")
        return False

def main():
    """Main initialization function."""
    print("🚀 Initializing WellSync AI Project")
    print("=" * 50)
    
    steps = [
        ("Creating directories", create_directories),
        ("Setting up environment file", setup_environment_file),
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Initializing database", initialize_database),
        ("Testing Redis connection", test_redis_connection),
        ("Validating configuration", validate_configuration),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if step_func():
            success_count += 1
        else:
            print(f"Step failed: {step_name}")
    
    print("\n" + "=" * 50)
    print(f"Initialization complete: {success_count}/{len(steps)} steps successful")
    
    if success_count == len(steps):
        print("🎉 Project setup completed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment:")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Edit .env with your API keys")
        print("3. Start Redis server: redis-server")
        print("4. Run the application: python -m wellsync_ai.api.app")
    else:
        print("⚠ Some steps failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())