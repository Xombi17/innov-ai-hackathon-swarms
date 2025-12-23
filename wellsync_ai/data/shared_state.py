"""
Shared state management for WellSync AI system.

Implements the SharedState class for inter-agent communication,
Redis integration for real-time state sharing, and SQLite 
persistence for historical data storage.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

from wellsync_ai.data.database import get_database_manager
from wellsync_ai.data.redis_client import get_redis_manager
from wellsync_ai.utils.config import get_config


class StateType(Enum):
    """Types of shared state data."""
    USER_PROFILE = "user_profile"
    RECENT_DATA = "recent_data"
    CURRENT_PLANS = "current_plans"
    CONSTRAINT_VIOLATIONS = "constraint_violations"
    AGENT_PROPOSALS = "agent_proposals"
    WORKFLOW_STATUS = "workflow_status"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation in the system."""
    constraint_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_domains: List[str]
    detected_at: str
    resolved: bool = False
    resolution_strategy: Optional[str] = None


@dataclass
class UserProfile:
    """User profile data structure."""
    user_id: str
    goals: Dict[str, Any]
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]
    baseline_metrics: Dict[str, float]
    created_at: str
    updated_at: str


@dataclass
class AgentProposal:
    """Agent proposal data structure."""
    agent_id: str
    proposal_type: str
    content: Dict[str, Any]
    confidence: float
    constraints_used: List[str]
    dependencies: List[str]
    reasoning: str
    timestamp: str
    session_id: Optional[str] = None


class SharedState:
    """
    Manages shared state across all wellness agents.
    
    Provides real-time state sharing via Redis and persistent
    storage via SQLite for inter-agent communication and
    coordination.
    """
    
    def __init__(self, state_id: Optional[str] = None):
        """
        Initialize SharedState manager.
        
        Args:
            state_id: Optional state identifier, generates new if None
        """
        self.state_id = state_id or str(uuid.uuid4())
        self.db_manager = get_database_manager()
        self.redis_manager = get_redis_manager()
        self.config = get_config()
        
        # Initialize state structure
        self._state_data = {
            'state_id': self.state_id,
            'timestamp': datetime.now().isoformat(),
            'user_profile': None,
            'recent_data': {},
            'current_plans': {},
            'constraint_violations': [],
            'agent_proposals': {},
            'workflow_status': 'initialized',
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': 1
            }
        }
        
        # Load existing state if state_id provided
        if state_id:
            self._load_state()
    
    def update_user_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Update user profile in shared state.
        
        Args:
            profile_data: User profile information
            
        Returns:
            Success status
        """
        try:
            # Create UserProfile object
            user_profile = UserProfile(
                user_id=profile_data.get('user_id', 'default_user'),
                goals=profile_data.get('goals', {}),
                constraints=profile_data.get('constraints', {}),
                preferences=profile_data.get('preferences', {}),
                baseline_metrics=profile_data.get('baseline_metrics', {}),
                created_at=profile_data.get('created_at', datetime.now().isoformat()),
                updated_at=datetime.now().isoformat()
            )
            
            # Update state
            self._state_data['user_profile'] = asdict(user_profile)
            self._update_metadata()
            
            # Persist to both Redis and SQLite
            self._persist_state()
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to update user profile: {str(e)}")
            return False
    
    def update_recent_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        """
        Update recent user data (last 7 days).
        
        Args:
            data_type: Type of data (fitness, nutrition, sleep, etc.)
            data: Recent data to store
            
        Returns:
            Success status
        """
        try:
            if 'recent_data' not in self._state_data:
                self._state_data['recent_data'] = {}
            
            self._state_data['recent_data'][data_type] = {
                'data': data,
                'updated_at': datetime.now().isoformat()
            }
            
            self._update_metadata()
            self._persist_state()
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to update recent data: {str(e)}")
            return False
    
    def update_current_plans(self, domain: str, plan_data: Dict[str, Any]) -> bool:
        """
        Update current active plans for a domain.
        
        Args:
            domain: Wellness domain (fitness, nutrition, sleep, mental_wellness)
            plan_data: Current plan information
            
        Returns:
            Success status
        """
        try:
            if 'current_plans' not in self._state_data:
                self._state_data['current_plans'] = {}
            
            self._state_data['current_plans'][domain] = {
                'plan': plan_data,
                'updated_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self._update_metadata()
            self._persist_state()
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to update current plans: {str(e)}")
            return False
    
    def add_constraint_violation(self, violation: ConstraintViolation) -> bool:
        """
        Add a constraint violation to shared state.
        
        Args:
            violation: ConstraintViolation object
            
        Returns:
            Success status
        """
        try:
            if 'constraint_violations' not in self._state_data:
                self._state_data['constraint_violations'] = []
            
            violation_dict = asdict(violation)
            self._state_data['constraint_violations'].append(violation_dict)
            
            # Keep only recent violations (last 30 days)
            self._cleanup_old_violations()
            
            self._update_metadata()
            self._persist_state()
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to add constraint violation: {str(e)}")
            return False
    
    def add_agent_proposal(self, proposal: AgentProposal) -> bool:
        """
        Add agent proposal to shared state.
        
        Args:
            proposal: AgentProposal object
            
        Returns:
            Success status
        """
        try:
            if 'agent_proposals' not in self._state_data:
                self._state_data['agent_proposals'] = {}
            
            proposal_dict = asdict(proposal)
            self._state_data['agent_proposals'][proposal.agent_id] = proposal_dict
            
            self._update_metadata()
            self._persist_state()
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to add agent proposal: {str(e)}")
            return False
    
    def update_workflow_status(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update workflow execution status.
        
        Args:
            status: Workflow status (initialized, running, completed, failed)
            metadata: Optional metadata about the status
            
        Returns:
            Success status
        """
        try:
            self._state_data['workflow_status'] = status
            
            if metadata:
                if 'workflow_metadata' not in self._state_data:
                    self._state_data['workflow_metadata'] = {}
                self._state_data['workflow_metadata'].update(metadata)
            
            self._update_metadata()
            self._persist_state()
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to update workflow status: {str(e)}")
            return False
    
    def get_state_data(self, state_type: Optional[StateType] = None) -> Dict[str, Any]:
        """
        Get shared state data.
        
        Args:
            state_type: Optional specific state type to retrieve
            
        Returns:
            State data dictionary
        """
        if state_type:
            return self._state_data.get(state_type.value, {})
        return self._state_data.copy()
    
    def get_user_profile(self) -> Optional[UserProfile]:
        """Get user profile from shared state."""
        profile_data = self._state_data.get('user_profile')
        if profile_data:
            return UserProfile(**profile_data)
        return None
    
    def get_recent_data(self, data_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recent user data.
        
        Args:
            data_type: Optional specific data type to retrieve
            
        Returns:
            Recent data dictionary
        """
        recent_data = self._state_data.get('recent_data', {})
        if data_type:
            return recent_data.get(data_type, {})
        return recent_data
    
    def get_current_plans(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current active plans.
        
        Args:
            domain: Optional specific domain to retrieve
            
        Returns:
            Current plans dictionary
        """
        current_plans = self._state_data.get('current_plans', {})
        if domain:
            return current_plans.get(domain, {})
        return current_plans
    
    def get_constraint_violations(self, resolved: Optional[bool] = None) -> List[ConstraintViolation]:
        """
        Get constraint violations.
        
        Args:
            resolved: Optional filter by resolution status
            
        Returns:
            List of ConstraintViolation objects
        """
        violations_data = self._state_data.get('constraint_violations', [])
        violations = [ConstraintViolation(**v) for v in violations_data]
        
        if resolved is not None:
            violations = [v for v in violations if v.resolved == resolved]
        
        return violations
    
    def get_agent_proposals(self, agent_id: Optional[str] = None) -> Dict[str, AgentProposal]:
        """
        Get agent proposals.
        
        Args:
            agent_id: Optional specific agent ID to retrieve
            
        Returns:
            Dictionary of AgentProposal objects
        """
        proposals_data = self._state_data.get('agent_proposals', {})
        
        if agent_id:
            proposal_data = proposals_data.get(agent_id)
            if proposal_data:
                return {agent_id: AgentProposal(**proposal_data)}
            return {}
        
        return {
            agent_id: AgentProposal(**proposal_data)
            for agent_id, proposal_data in proposals_data.items()
        }
    
    def clear_agent_proposals(self) -> bool:
        """Clear all agent proposals from shared state."""
        try:
            self._state_data['agent_proposals'] = {}
            self._update_metadata()
            self._persist_state()
            return True
        except Exception as e:
            self._log_error(f"Failed to clear agent proposals: {str(e)}")
            return False
    
    def resolve_constraint_violation(self, violation_index: int, resolution_strategy: str) -> bool:
        """
        Mark a constraint violation as resolved.
        
        Args:
            violation_index: Index of violation in the list
            resolution_strategy: Description of how it was resolved
            
        Returns:
            Success status
        """
        try:
            violations = self._state_data.get('constraint_violations', [])
            if 0 <= violation_index < len(violations):
                violations[violation_index]['resolved'] = True
                violations[violation_index]['resolution_strategy'] = resolution_strategy
                
                self._update_metadata()
                self._persist_state()
                return True
            return False
            
        except Exception as e:
            self._log_error(f"Failed to resolve constraint violation: {str(e)}")
            return False
    
    def _load_state(self) -> None:
        """Load existing state from Redis or SQLite."""
        try:
            # Try Redis first for real-time data
            redis_state = self.redis_manager.get_shared_state(self.state_id)
            if redis_state:
                self._state_data.update(redis_state)
                return
            
            # Fallback to SQLite for persistent data
            db_state = self.db_manager.get_latest_shared_state()
            if db_state and db_state.get('state_id') == self.state_id:
                self._state_data.update(db_state)
                
        except Exception as e:
            self._log_error(f"Failed to load state: {str(e)}")
    
    def _persist_state(self) -> None:
        """Persist state to both Redis and SQLite."""
        try:
            # Store in Redis for real-time access
            self.redis_manager.set_shared_state(
                self.state_id,
                self._state_data,
                ttl=self.config.redis_memory_ttl_seconds
            )
            
            # Store in SQLite for persistence
            self.db_manager.store_shared_state(self._state_data)
            
        except Exception as e:
            self._log_error(f"Failed to persist state: {str(e)}")
    
    def _update_metadata(self) -> None:
        """Update state metadata."""
        self._state_data['timestamp'] = datetime.now().isoformat()
        self._state_data['metadata']['last_updated'] = datetime.now().isoformat()
        self._state_data['metadata']['version'] += 1
    
    def _cleanup_old_violations(self) -> None:
        """Remove constraint violations older than 30 days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            violations = self._state_data.get('constraint_violations', [])
            
            filtered_violations = []
            for violation in violations:
                detected_at = datetime.fromisoformat(violation['detected_at'])
                if detected_at > cutoff_date:
                    filtered_violations.append(violation)
            
            self._state_data['constraint_violations'] = filtered_violations
            
        except Exception as e:
            self._log_error(f"Failed to cleanup old violations: {str(e)}")
    
    def _log_error(self, message: str) -> None:
        """Log error to system logs."""
        self.db_manager.log_system_event(
            'ERROR',
            message,
            'SharedState',
            {'state_id': self.state_id}
        )
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current shared state."""
        return {
            'state_id': self.state_id,
            'timestamp': self._state_data['timestamp'],
            'user_profile_exists': self._state_data.get('user_profile') is not None,
            'recent_data_types': list(self._state_data.get('recent_data', {}).keys()),
            'active_plans': list(self._state_data.get('current_plans', {}).keys()),
            'constraint_violations_count': len(self._state_data.get('constraint_violations', [])),
            'agent_proposals_count': len(self._state_data.get('agent_proposals', {})),
            'workflow_status': self._state_data.get('workflow_status'),
            'version': self._state_data.get('metadata', {}).get('version', 1)
        }


class SharedStateManager:
    """
    Manager for multiple shared states and state lifecycle.
    """
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.redis_manager = get_redis_manager()
        self._active_states = {}
    
    def create_shared_state(self, user_id: Optional[str] = None) -> SharedState:
        """
        Create a new shared state.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            New SharedState instance
        """
        state = SharedState()
        
        if user_id:
            # Initialize with user context
            state.update_user_profile({
                'user_id': user_id,
                'goals': {},
                'constraints': {},
                'preferences': {},
                'baseline_metrics': {}
            })
        
        self._active_states[state.state_id] = state
        return state
    
    def get_shared_state(self, state_id: str) -> Optional[SharedState]:
        """
        Get existing shared state by ID.
        
        Args:
            state_id: State identifier
            
        Returns:
            SharedState instance or None
        """
        if state_id in self._active_states:
            return self._active_states[state_id]
        
        # Try to load from storage
        try:
            state = SharedState(state_id)
            self._active_states[state_id] = state
            return state
        except Exception:
            return None
    
    def cleanup_expired_states(self) -> int:
        """
        Clean up expired shared states.
        
        Returns:
            Number of states cleaned up
        """
        cleaned_count = 0
        expired_states = []
        
        for state_id, state in self._active_states.items():
            state_data = state.get_state_data()
            last_updated = datetime.fromisoformat(
                state_data.get('metadata', {}).get('last_updated', datetime.now().isoformat())
            )
            
            # Remove states older than retention period
            if datetime.now() - last_updated > timedelta(days=7):
                expired_states.append(state_id)
        
        for state_id in expired_states:
            del self._active_states[state_id]
            cleaned_count += 1
        
        return cleaned_count
    
    def get_active_states_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all active shared states."""
        return [
            state.get_state_summary()
            for state in self._active_states.values()
        ]


# Global shared state manager
shared_state_manager = SharedStateManager()


def get_shared_state_manager() -> SharedStateManager:
    """Get the global shared state manager."""
    return shared_state_manager


def create_shared_state(user_id: Optional[str] = None) -> SharedState:
    """Create a new shared state."""
    return shared_state_manager.create_shared_state(user_id)


def get_shared_state(state_id: str) -> Optional[SharedState]:
    """Get existing shared state by ID."""
    return shared_state_manager.get_shared_state(state_id)