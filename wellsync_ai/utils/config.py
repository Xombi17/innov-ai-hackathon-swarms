"""
Configuration management for WellSync AI system.

Handles environment variables, API keys, and system settings
with validation and default values.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class WellSyncConfig(BaseSettings):
    """Configuration settings for WellSync AI system."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    
    # LLM Configuration
    llm_provider: str = Field("gemini", env="LLM_PROVIDER")
    llm_model: str = Field("gemini/gemini-3.0-flash", env="LLM_MODEL") 
    
    # Recommended Model Options (2025):
    # - Gemini: gemini/gemini-3.0-flash (Fastest), gemini/gemini-3.0-pro (Reasoning)
    # - Groq: groq/llama-3-70b-8192 (Open Source alternative)
    # - OpenAI: gpt-4o (High precision)
    
    # Database Configuration
    database_url: str = Field("sqlite:///data/databases/wellsync.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Flask Configuration
    flask_env: str = Field("development", env="FLASK_ENV")
    flask_debug: bool = Field(True, env="FLASK_DEBUG")
    flask_secret_key: str = Field("dev-secret-key-change-in-production", env="FLASK_SECRET_KEY")
    flask_host: str = Field("127.0.0.1", env="FLASK_HOST")
    flask_port: int = Field(5000, env="FLASK_PORT")
    debug_mode: bool = Field(True, env="DEBUG_MODE")
    allowed_origins: list = Field(["http://localhost:3000", "http://127.0.0.1:3000"], env="ALLOWED_ORIGINS")
    
    # Agent Configuration
    agent_temperature: float = Field(0.1, env="AGENT_TEMPERATURE")
    agent_max_tokens: int = Field(2000, env="AGENT_MAX_TOKENS")
    agent_retry_attempts: int = Field(3, env="AGENT_RETRY_ATTEMPTS")
    
    # System Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_concurrent_agents: int = Field(4, env="MAX_CONCURRENT_AGENTS")
    workflow_timeout_seconds: int = Field(300, env="WORKFLOW_TIMEOUT_SECONDS")
    
    # Memory Configuration
    memory_retention_days: int = Field(90, env="MEMORY_RETENTION_DAYS")
    redis_memory_ttl_seconds: int = Field(3600, env="REDIS_MEMORY_TTL_SECONDS")
    
    # Safety and Limits
    max_workout_intensity: float = Field(0.9, env="MAX_WORKOUT_INTENSITY")
    min_sleep_hours: int = Field(6, env="MIN_SLEEP_HOURS")
    max_daily_calories: int = Field(4000, env="MAX_DAILY_CALORIES")
    min_daily_calories: int = Field(1200, env="MIN_DAILY_CALORIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global configuration instance
config = WellSyncConfig()


def get_config() -> WellSyncConfig:
    """Get the global configuration instance."""
    return config


def validate_config() -> bool:
    """Validate that all required configuration is present."""
    try:
        # Check required API keys
        # Check required API keys based on provider
        if config.llm_provider == "openai":
            if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        elif config.llm_provider == "gemini":
            if not config.gemini_api_key or config.gemini_api_key == "your_gemini_api_key_here":
                raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        elif config.llm_provider == "groq":
            if not config.groq_api_key:
                raise ValueError("GROQ_API_KEY is required for Groq provider")
        
        # Validate numeric ranges
        if not 0.0 <= config.agent_temperature <= 2.0:
            raise ValueError("AGENT_TEMPERATURE must be between 0.0 and 2.0")
        
        if config.agent_max_tokens < 100:
            raise ValueError("AGENT_MAX_TOKENS must be at least 100")
        
        if config.max_workout_intensity < 0.1 or config.max_workout_intensity > 1.0:
            raise ValueError("MAX_WORKOUT_INTENSITY must be between 0.1 and 1.0")
        
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


def create_directories():
    """Create necessary directories for the application."""
    directories = [
        "data/databases",
        "data/agent_states", 
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")