"""
Test suite for WellSync AI project setup verification.

Tests that all core components are properly configured
and can be imported without errors.
"""

import pytest
import os
from pathlib import Path


def test_project_structure():
    """Test that all required directories exist."""
    required_dirs = [
        "wellsync_ai",
        "wellsync_ai/agents",
        "wellsync_ai/workflows",
        "wellsync_ai/data",
        "wellsync_ai/api",
        "wellsync_ai/memory",
        "wellsync_ai/utils",
        "tests",
        "data/databases",
        "data/agent_states",
        "logs"
    ]
    
    for directory in required_dirs:
        assert Path(directory).exists(), f"Directory {directory} should exist"


def test_required_files():
    """Test that all required files exist."""
    required_files = [
        "requirements.txt",
        "setup.py",
        "README.md",
        ".env.example",
        ".gitignore",
        "Makefile",
        "init_project.py",
        "wellsync_ai/__init__.py",
        "wellsync_ai/cli.py",
        "wellsync_ai/utils/config.py",
        "wellsync_ai/data/database.py",
        "wellsync_ai/data/redis_client.py"
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"File {file_path} should exist"


def test_config_import():
    """Test that configuration module can be imported."""
    from wellsync_ai.utils.config import WellSyncConfig, get_config
    
    config = get_config()
    assert isinstance(config, WellSyncConfig)
    assert hasattr(config, 'openai_api_key')
    assert hasattr(config, 'database_url')
    assert hasattr(config, 'redis_url')


def test_database_import():
    """Test that database module can be imported."""
    from wellsync_ai.data.database import DatabaseManager, get_database_manager
    
    db_manager = get_database_manager()
    assert isinstance(db_manager, DatabaseManager)
    assert hasattr(db_manager, 'initialize_database')
    assert hasattr(db_manager, 'get_connection')


def test_redis_import():
    """Test that Redis module can be imported."""
    from wellsync_ai.data.redis_client import RedisManager, get_redis_manager
    
    redis_manager = get_redis_manager()
    assert isinstance(redis_manager, RedisManager)
    assert hasattr(redis_manager, 'test_connection')
    assert hasattr(redis_manager, 'set_shared_state')


def test_cli_import():
    """Test that CLI module can be imported."""
    from wellsync_ai.cli import main
    
    assert callable(main)


def test_database_file_exists():
    """Test that database file was created."""
    db_path = Path("data/databases/wellsync.db")
    assert db_path.exists(), "Database file should be created"
    assert db_path.stat().st_size > 0, "Database file should not be empty"


def test_environment_file():
    """Test that environment configuration is set up."""
    env_example = Path(".env.example")
    assert env_example.exists(), ".env.example should exist"
    
    # Check if .env was created
    env_file = Path(".env")
    if env_file.exists():
        # If .env exists, it should have content
        assert env_file.stat().st_size > 0, ".env file should not be empty"


def test_virtual_environment():
    """Test that virtual environment was created."""
    venv_dir = Path("venv")
    assert venv_dir.exists(), "Virtual environment directory should exist"
    
    # Check for key venv files
    if os.name == 'nt':  # Windows
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    assert python_exe.exists(), "Python executable should exist in venv"
    assert pip_exe.exists(), "Pip executable should exist in venv"


def test_package_structure():
    """Test that Python package structure is correct."""
    # Check that all package directories have __init__.py
    package_dirs = [
        "wellsync_ai",
        "wellsync_ai/agents",
        "wellsync_ai/workflows", 
        "wellsync_ai/data",
        "wellsync_ai/api",
        "wellsync_ai/memory",
        "wellsync_ai/utils",
        "tests"
    ]
    
    for package_dir in package_dirs:
        init_file = Path(package_dir) / "__init__.py"
        assert init_file.exists(), f"{package_dir} should have __init__.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])