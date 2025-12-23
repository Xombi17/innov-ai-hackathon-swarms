"""
Data management module for WellSync AI system.

Contains data models, storage interfaces, and state management
for agent coordination and persistence.
"""

from .database import DatabaseManager, get_database_manager, initialize_database
from .redis_client import RedisManager, get_redis_manager, test_redis_connection
from .shared_state import (
    SharedState, 
    SharedStateManager, 
    UserProfile, 
    AgentProposal, 
    ConstraintViolation,
    StateType,
    get_shared_state_manager,
    create_shared_state,
    get_shared_state
)

__all__ = [
    'DatabaseManager', 'get_database_manager', 'initialize_database',
    'RedisManager', 'get_redis_manager', 'test_redis_connection',
    'SharedState', 'SharedStateManager', 'UserProfile', 'AgentProposal', 
    'ConstraintViolation', 'StateType', 'get_shared_state_manager',
    'create_shared_state', 'get_shared_state'
]