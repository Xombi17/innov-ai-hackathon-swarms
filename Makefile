# WellSync AI Development Makefile

.PHONY: help install init test lint format clean run health

# Default target
help:
	@echo "WellSync AI Development Commands"
	@echo "================================"
	@echo "install    - Install dependencies"
	@echo "init       - Initialize project (create venv, install deps, setup db)"
	@echo "test       - Run test suite"
	@echo "lint       - Run code linting"
	@echo "format     - Format code with black"
	@echo "clean      - Clean up generated files"
	@echo "run        - Run development server"
	@echo "health     - System health check"

# Install dependencies
install:
	pip install -r requirements.txt

# Full project initialization
init:
	python init_project.py

# Run tests
test:
	python -m pytest tests/ -v --tb=short

# Run linting
lint:
	flake8 wellsync_ai/ --max-line-length=88 --extend-ignore=E203,W503
	mypy wellsync_ai/ --ignore-missing-imports

# Format code
format:
	black wellsync_ai/ tests/ --line-length=88
	isort wellsync_ai/ tests/ --profile black

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/

# Run development server
run:
	python -m wellsync_ai.cli server --debug

# System health check
health:
	python -m wellsync_ai.cli health

# Development setup (one-time)
dev-setup: init
	@echo "Development environment ready!"
	@echo "Next steps:"
	@echo "1. Edit .env with your API keys"
	@echo "2. Start Redis: redis-server"
	@echo "3. Run server: make run"