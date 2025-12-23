import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

import structlog

from wellsync_ai.data.shared_state import get_shared_state, SharedState
from wellsync_ai.agents.fitness_agent import FitnessAgent
from wellsync_ai.agents.nutrition_agent import NutritionAgent
from wellsync_ai.agents.sleep_agent import SleepAgent
from wellsync_ai.agents.mental_wellness_agent import MentalWellnessAgent
from wellsync_ai.agents.coordinator_agent import CoordinatorAgent

logger = structlog.get_logger()

class WellnessWorkflowOrchestrator:
    """
    Orchestrates the 8-step wellness planning workflow.
    Manages parallel agent execution, state updates, and coordination.
    """
    
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        # Lazily instantiate other agents or instantiate here
        # Assuming agents are stateless per request or handle their own state via session_id
        # For this implementation, we re-instantiate or reuse. 
        # Ideally, we should have a registry. For now, instantiating directly.
        
        # Note: In a real system, these might injected or loaded from config
        self.agents = {
            'FitnessAgent': FitnessAgent(),
            'NutritionAgent': NutritionAgent(),
            'SleepAgent': SleepAgent(),
            'MentalWellnessAgent': MentalWellnessAgent()
        }

    async def execute_workflow(self, state_id: str) -> Dict[str, Any]:
        """
        Execute the full wellness planning workflow.
        
        Args:
            state_id: ID of the shared state containing user profile and constraints
            
        Returns:
            The final coordinated wellness plan
        """
        logger.info("Starting wellness workflow execution", state_id=state_id)
        
        # 1. Retrieve State
        shared_state = get_shared_state(state_id)
        if not shared_state:
            raise ValueError(f"Shared state {state_id} not found")
            
        state_data = shared_state.get_state_data()
        user_profile = state_data.get('user_profile', {})
        constraints = state_data.get('constraints', {})
        
        # 2. Phase 1: Sequential Agent Analysis
        # We run domain agents sequentially to avoid rate limits
        agent_proposals = await self._run_agents(user_profile, constraints, state_data)
        
        # Update state with proposals
        shared_state.update_recent_data('agent_proposals', agent_proposals)
        
        # 3. Phase 2: Coordination & Conflict Resolution
        # Coordinator analyzes proposals and constraints
        unified_plan = self.coordinator.coordinate_agent_proposals(
            agent_proposals, 
            constraints, 
            state_data
        )
        
        # 4. Phase 3: Finalization & Response
        # Format the final response
        final_response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'state_id': state_id,
            'plan': unified_plan,
            'metadata': {
                'agents_involved': list(agent_proposals.keys()),
                'coordination_confidence': unified_plan.get('confidence', 0.0)
            }
        }
        
        # Update shared state with final result
        shared_state.update_recent_data('unified_plan', unified_plan)
        
        logger.info("Wellness workflow execution completed", state_id=state_id)
        return final_response

    async def _run_agents(
        self, 
        user_profile: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Run all domain agents sequentially to avoid rate limits."""
        
        proposals = {}
        
        for name, agent in self.agents.items():
            try:
                # specific delay to respect rate limits (Groq free tier TPM)
                await asyncio.sleep(5) 
                
                logger.info(f"Running agent: {name}")
                
                # Run agent in thread
                result = await asyncio.to_thread(
                    agent.process_wellness_request,
                    user_profile,
                    constraints,
                    shared_state_data
                )
                
                proposals[name] = result
                
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                     error_msg += f" Response: {e.response.text}"
                
                logger.error(f"Agent {name} failed", error=error_msg)
                
                proposals[name] = {
                    'agent_name': name,
                    'error': error_msg,
                    'confidence': 0.0,
                    'reasoning': 'Agent execution failed',
                    'proposal': {} # Valid empty structure
                }
                
        return proposals