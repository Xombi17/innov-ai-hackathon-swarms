"""
Error Manager for WellSync AI system.

Provides unified error handling, classification, and logging 
to ensure system resilience and graceful degradation.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import enum
import traceback

from wellsync_ai.data.database import get_database_manager

class ErrorSeverity(enum.Enum):
    RECOVERABLE = "RECOVERABLE"  # Transient, can retry
    DEGRADED = "DEGRADED"        # Feature failed, but system continues
    CRITICAL = "CRITICAL"        # System cannot function

class WellnessError(Exception):
    """Base class for known wellness system errors."""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.DEGRADED, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.severity = severity
        self.context = context or {}
        super().__init__(message)

class ErrorManager:
    """
    Centralized error handling and recovery management.
    """
    
    def __init__(self):
        self.db_manager = get_database_manager()

    def handle_error(self, error: Exception, component: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an error: log it, determine severity, and return a safe error response.
        
        Args:
            error: The exception that occurred.
            component: Name of the component where error happened (e.g., 'FitnessAgent').
            context: Additional context data (e.g., user_id, input params).
            
        Returns:
            A standardized error dictionary safe for API responses or internal state.
        """
        severity = ErrorSeverity.CRITICAL
        message = str(error)
        
        # Determine known severity
        if isinstance(error, WellnessError):
            severity = error.severity
        elif "rate limit" in message.lower() or "timeout" in message.lower():
            severity = ErrorSeverity.RECOVERABLE
        elif isinstance(error, (ValueError, KeyError, TypeError)):
            # Usually input data issues, degraded functionality for that specific part
            severity = ErrorSeverity.DEGRADED
            
        # Log to database
        self.db_manager.log_system_event(
            level=severity.value,
            message=f"{component} error: {message}",
            component=component,
            data={
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc(),
                "context": context or {}
            }
        )
        
        # Return standardized error object
        return {
            "error": True,
            "message": message,
            "code": type(error).__name__,
            "severity": severity.value,
            "component": component,
            "timestamp": datetime.now().isoformat()
        }

# Global instance
_error_manager = ErrorManager()

def get_error_manager() -> ErrorManager:
    return _error_manager
