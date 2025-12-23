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
    async def _run_agents(
        self, 
        user_profile: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Run all domain agents sequentially with Caching."""
        
        from wellsync_ai.utils.cache_manager import get_cache_manager
        cache_manager = get_cache_manager()
        proposals = {}
        
        # Prepare tasks for parallel execution
        tasks = []
        agent_names = []
        
        for name, agent in self.agents.items():
            # Generate cache key
            cache_data = {
                'agent': name,
                'user_id': user_profile.get('user_id'),
                'profile_age': user_profile.get('age'),
                'constraints': constraints,
                'domain': agent.domain
            }
            cache_key = cache_manager.generate_key(f"agent_proposal:{name}", cache_data)
            
            # Check cache
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache HIT for agent: {name}")
                proposals[name] = cached_result
                continue
                
            logger.info(f"Cache MISS for agent: {name}. Queueing for execution...")
            tasks.append(self._execute_single_agent(name, agent, user_profile, constraints, shared_state_data, cache_manager, cache_key))
            agent_names.append(name)

        if tasks:
            logger.info(f"Executing {len(tasks)} agents in parallel...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(agent_names, results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {name} crashed unrecoverably", error=str(result))
                    # Fallback for catastrophic failure
                    proposals[name] = {
                        'agent_name': name,
                        'is_error': True,
                        'error': str(result),
                        'confidence': 0.0,
                        'proposal': {}
                    }
                else:
                    proposals[name] = result
                    
        return proposals

    async def _execute_single_agent(self, name, agent, user_profile, constraints, shared_state_data, cache_manager, cache_key):
        """Helper to run a single agent with error handling and caching."""
        try:
            # Random jitter to avoid exact simultaneous requests if uncached
            import random
            await asyncio.sleep(random.uniform(0.1, 2.0))
            
            logger.info(f"Running agent: {name}")
            
            result = await asyncio.to_thread(
                agent.process_wellness_request,
                user_profile,
                constraints,
                shared_state_data
            )
            
            # Store successful results in cache (TTL 1 hour)
            if result and not result.get('is_error'):
                cache_manager.set(cache_key, result, ttl=3600)
            
            return result
        except Exception as e:
            # Use ErrorManager for standardized handling
            from wellsync_ai.utils.error_manager import get_error_manager
            error_context = {'user_id': user_profile.get('user_id'), 'state_id': shared_state_data.get('state_id')}
            error_info = get_error_manager().handle_error(e, f"Agent-{name}", error_context)
            
            logger.error(f"Agent {name} failed", error=error_info['message'])
            
            return {
                'agent_name': name,
                'is_error': True,
                'error_details': error_info,
                'confidence': 0.0,
                'reasoning': f"Agent execution failed: {error_info['message']}",
                'proposal': {} 
            }
                
        return proposals