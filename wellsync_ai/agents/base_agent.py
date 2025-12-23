"""
Base agent architecture for WellSync AI system.

Implements the WellnessAgent base class that extends Swarms Agent
with wellness-specific functionality, memory integration, and
domain constraint handling.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod

from swarms import Agent
from swarms import LiteLLM

from wellsync_ai.utils.config import get_config
from wellsync_ai.data.database import get_database_manager
from wellsync_ai.data.redis_client import get_redis_manager


class MemoryStore:
    """Memory management for wellness agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.db_manager = get_database_manager()
        self.redis_manager = get_redis_manager()
        
        # Memory types
        self.episodic_memory = []  # Specific interactions and outcomes
        self.semantic_memory = {}  # Domain knowledge and patterns
        self.working_memory = {}   # Current reasoning state
    
    def store_episodic_memory(self, session_id: str, data: Dict[str, Any]) -> int:
        """Store episodic memory (specific user interactions)."""
        return self.db_manager.store_agent_memory(
            self.agent_name, 
            "episodic", 
            data, 
            session_id
        )
    
    def store_semantic_memory(self, knowledge_type: str, data: Dict[str, Any]) -> int:
        """Store semantic memory (domain knowledge)."""
        return self.db_manager.store_agent_memory(
            self.agent_name,
            f"semantic_{knowledge_type}",
            data
        )
    
    def update_working_memory(self, data: Dict[str, Any]) -> bool:
        """Update working memory in Redis for real-time access."""
        self.working_memory.update(data)
        return self.redis_manager.set_agent_working_memory(
            self.agent_name,
            self.working_memory
        )
    
    def get_episodic_memory(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent episodic memories."""
        return self.db_manager.get_agent_memory(
            self.agent_name,
            "episodic",
            limit
        )
    
    def get_semantic_memory(self, knowledge_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve semantic memory by type."""
        return self.db_manager.get_agent_memory(
            self.agent_name,
            f"semantic_{knowledge_type}",
            limit
        )
    
    def get_working_memory(self) -> Dict[str, Any]:
        """Get current working memory from Redis."""
        redis_memory = self.redis_manager.get_agent_working_memory(self.agent_name)
        if redis_memory:
            self.working_memory = redis_memory
        return self.working_memory
    
    def clear_working_memory(self) -> bool:
        """Clear working memory."""
        self.working_memory = {}
        return self.redis_manager.set_agent_working_memory(
            self.agent_name,
            {}
        )


class WellnessAgent(Agent, ABC):
    """
    Base class for all wellness agents in the WellSync AI system.
    
    Extends Swarms Agent with wellness-specific functionality including:
    - Memory store integration for episodic, semantic, and working memory
    - Domain constraint handling and validation
    - Wellness-specific prompt building and response parsing
    - Structured communication protocols
    """
    
    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        domain: str,
        confidence_threshold: float = 0.7,
        **kwargs
    ):
        """
        Initialize WellnessAgent with Swarms AI integration.
        
        Args:
            agent_name: Unique identifier for the agent
            system_prompt: Domain-specific system prompt
            domain: Wellness domain (fitness, nutrition, sleep, mental_wellness, coordinator)
            confidence_threshold: Minimum confidence for proposals
            **kwargs: Additional arguments passed to Swarms Agent
        """
        config = get_config()
        
        # Select API key based on provider
        api_key = None
        if config.llm_provider == "openai":
            api_key = config.openai_api_key
        elif config.llm_provider == "gemini":
            api_key = config.gemini_api_key
        elif config.llm_provider == "groq":
            api_key = config.groq_api_key
            
        # Initialize LLM for the agent
        model = LiteLLM(
            model_name=config.llm_model,
            temperature=config.agent_temperature,
            max_tokens=config.agent_max_tokens,
            api_key=api_key,
        )
        
        # Initialize Swarms Agent
        super().__init__(
            agent_name=agent_name,
            system_prompt=system_prompt,
            llm=model,
            max_loops=1,
            autosave=False,
            dashboard=False,
            verbose=True,
            dynamic_temperature_enabled=True,
            saved_state_path=f"data/agent_states/{agent_name}_state.json",
            user_name="wellsync_system",
            retry_attempts=config.agent_retry_attempts,
            context_length=200000,
            **kwargs
        )
        
        # Wellness-specific attributes
        self.domain = domain
        self.confidence_threshold = confidence_threshold
        self.memory = MemoryStore(agent_name)
        
        # Initialize Learning Manager
        from wellsync_ai.agents.learning_manager import LearningManager
        self.learning_manager = LearningManager(agent_name, domain)
        
        self.domain_constraints = {}
        self.session_id = None
        
        # Initialize working memory
        self.memory.update_working_memory({
            'agent_name': agent_name,
            'domain': domain,
            'initialized_at': datetime.now().isoformat(),
            'active_constraints': {},
            'current_reasoning_state': {}
        })
    
    def start_session(self, user_data: Dict[str, Any]) -> str:
        """Start a new wellness planning session."""
        self.session_id = str(uuid.uuid4())
        
        # Store session start in episodic memory
        session_data = {
            'session_id': self.session_id,
            'session_type': 'wellness_planning',
            'user_data': user_data,
            'started_at': datetime.now().isoformat()
        }
        
        self.memory.store_episodic_memory(self.session_id, session_data)
        
        # Update working memory with session context
        self.memory.update_working_memory({
            'current_session_id': self.session_id,
            'session_context': user_data,
            'session_started_at': datetime.now().isoformat()
        })
        
        return self.session_id
    
    def process_wellness_request(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a wellness request and generate a structured proposal.
        
        Args:
            user_data: User profile and current data
            constraints: Real-world constraints (budget, time, etc.)
            shared_state: Current shared state from other agents
            
        Returns:
            Structured proposal with confidence, reasoning, and constraints
        """
        try:
            # Update domain constraints
            self.domain_constraints.update(constraints)
            
            # Get learning context (fatigue, compliance, etc.)
            learning_context = {}
            if user_data.get('user_id'):
                learning_context = self.learning_manager.get_learning_context(user_data['user_id'])
            
            # Build wellness-specific prompt with learning context
            # We pass learning_context as part of user_data or a separate arg depending on implementation
            # For backward compatibility, we'll inject it into kwargs-like structure or modify user_data
            user_data_with_learning = user_data.copy()
            user_data_with_learning['learning_context'] = learning_context
            
            prompt = self.build_wellness_prompt(user_data_with_learning, constraints, shared_state)
            
            # Generate response using Swarms Agent
            response = self.run(prompt)
            
            # Parse and validate response
            parsed_response = self.parse_wellness_response(response)
            
            # Store interaction in memory
            self._store_interaction(user_data, constraints, parsed_response)
            
            return parsed_response
            
        except Exception as e:
            # Use ErrorManager for standardized handling
            from wellsync_ai.utils.error_manager import get_error_manager
            
            # Context for the error
            error_context = {
                'user_id': user_data.get('user_id'),
                'domain': self.domain,
                'session_id': self.session_id,
                'input_constraints': constraints
            }
            
            # Process error
            error_info = get_error_manager().handle_error(e, f"Agent-{self.agent_name}", error_context)
            
            # Return standardized error proposal
            return {
                'agent_name': self.agent_name,
                'domain': self.domain,
                'is_error': True,
                'error_details': error_info,
                'error': error_info['message'],
                'confidence': 0.0,
                'proposal': None,
                'timestamp': datetime.now().isoformat(),
                'reasoning': f"Agent {self.agent_name} encountered an error: {error_info['message']}"
            }
    
    @abstractmethod
    def build_wellness_prompt(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build domain-specific wellness prompt.
        
        Must be implemented by each domain agent to create
        appropriate prompts for their wellness domain.
        """
        pass
    
    def parse_wellness_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured wellness proposal.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Structured proposal dictionary
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                parsed = json.loads(response)
            else:
                # Extract JSON from response if embedded in text
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                else:
                    # Fallback: create structured response from text
                    parsed = {
                        'proposal': response,
                        'confidence': 0.5,
                        'reasoning': 'Unstructured response parsed as text'
                    }
            
            # Add required metadata
            parsed.update({
                'agent_name': self.agent_name,
                'domain': self.domain,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id
            })
            
            # Validate required fields
            self._validate_proposal_structure(parsed)
            
            return parsed
            
        except json.JSONDecodeError as e:
            # Return fallback structure for invalid JSON
            import structlog
            logger = structlog.get_logger()
            logger.error(f"Agent {self.agent_name} JSON parse failed", raw_response=response, error=str(e))
            
            return {
                'agent_name': self.agent_name,
                'domain': self.domain,
                'error': f"JSON parsing failed: {str(e)}",
                'confidence': 0.0,
                'proposal': {}, # Return empty dict to prevent AttributeError
                'timestamp': datetime.now().isoformat(),
                'reasoning': 'Failed to parse structured response'
            }
    
    def _validate_proposal_structure(self, proposal: Dict[str, Any]) -> None:
        """Validate that proposal has required structure."""
        required_fields = ['confidence', 'reasoning']
        
        for field in required_fields:
            if field not in proposal:
                proposal[field] = self._get_default_field_value(field)
        
        # Validate confidence is in valid range
        if 'confidence' in proposal:
            confidence = proposal['confidence']
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                proposal['confidence'] = 0.5
    
    def _get_default_field_value(self, field: str) -> Any:
        """Get default value for missing required fields."""
        defaults = {
            'confidence': 0.5,
            'reasoning': 'No reasoning provided',
            'constraints_used': [],
            'dependencies': []
        }
        return defaults.get(field, None)
    
    def _store_interaction(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any], 
        response: Dict[str, Any]
    ) -> None:
        """Store the interaction in agent memory."""
        interaction_data = {
            'interaction_type': 'wellness_request',
            'user_data': user_data,
            'constraints': constraints,
            'agent_response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.session_id:
            self.memory.store_episodic_memory(self.session_id, interaction_data)
        
        # Update working memory with latest interaction
        self.memory.update_working_memory({
            'last_interaction': interaction_data,
            'last_response_confidence': response.get('confidence', 0.0),
            'active_constraints': constraints
        })
    
    def update_domain_knowledge(self, knowledge_type: str, data: Dict[str, Any]) -> None:
        """Update semantic memory with domain knowledge."""
        self.memory.store_semantic_memory(knowledge_type, {
            'knowledge_type': knowledge_type,
            'data': data,
            'updated_at': datetime.now().isoformat(),
            'agent_domain': self.domain
        })
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and health information."""
        working_memory = self.memory.get_working_memory()
        
        return {
            'agent_name': self.agent_name,
            'domain': self.domain,
            'status': 'active',
            'confidence_threshold': self.confidence_threshold,
            'current_session_id': self.session_id,
            'working_memory_size': len(working_memory),
            'domain_constraints_count': len(self.domain_constraints),
            'last_activity': working_memory.get('last_interaction', {}).get('timestamp'),
            'health_check_timestamp': datetime.now().isoformat()
        }
    
    def reset_agent_state(self) -> None:
        """Reset agent to clean state."""
        self.session_id = None
        self.domain_constraints = {}
        self.memory.clear_working_memory()
        
        # Log reset event
        db_manager = get_database_manager()
        db_manager.log_system_event(
            'INFO',
            f"Agent {self.agent_name} state reset",
            self.agent_name
        )


class AgentMessage:
    """Structured message for inter-agent communication."""
    
    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
        message_id: Optional[str] = None
    ):
        self.message_id = message_id or str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.payload = payload
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_type': self.message_type,
            'payload': self.payload,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            message_type=data['message_type'],
            payload=data['payload'],
            message_id=data.get('message_id')
        )


def create_wellness_agent(
    agent_name: str,
    domain: str,
    system_prompt: str,
    confidence_threshold: float = 0.7,
    **kwargs
) -> WellnessAgent:
    """
    Factory function to create wellness agents.
    
    This is a placeholder that would be used by domain-specific
    agent implementations that inherit from WellnessAgent.
    """
    # This would be implemented by specific agent classes
    # that inherit from WellnessAgent
    raise NotImplementedError(
        "Use domain-specific agent classes that inherit from WellnessAgent"
    )