
import asyncio
import uuid
from wellsync_ai.workflows.wellness_orchestrator import WellnessWorkflowOrchestrator
from wellsync_ai.data.shared_state import SharedStateManager
from wellsync_ai.utils.error_manager import get_error_manager

async def test_error_handling():
    print("Initializing test...")
    state_manager = SharedStateManager()
    shared_state = state_manager.create_shared_state(user_id="test_user_error")
    
    # Mock user profile
    shared_state.update_user_profile({
        "user_id": "test_user_error",
        "name": "Test User",
        "age": 30,
        "goals": {"fitness": "improve_cardio"}
    })
    
    orchestrator = WellnessWorkflowOrchestrator()
    
    # MONKEY PATCH: Force FitnessAgent to fail
    original_run_agents = orchestrator._run_agents
    
    # We'll spy on the real method or just inject a failure if we can't easily patch the agent instance
    # Since _run_agents calls process_wellness_request on instances in self.agents
    
    class FailingAgent:
        def process_wellness_request(self, *args, **kwargs):
            raise ValueError("Simulated API Error for Testing")

    # Inject failing agent
    orchestrator.agents['FitnessAgent'] = FailingAgent()
    
    print("Running workflow with simulated failure in FitnessAgent...")
    try:
        result = await orchestrator.execute_workflow(shared_state.state_id)
        
        print("\nWorkflow completed!")
        print(f"Success: {result['success']}")
        
        fitness_result = result['plan'].get('fitness_plan', {})
        # Note: The coordinator might filter out failed agents or include them. 
        # We need to check the raw proposals in shared state to confirm the error was captured.
        
        # Refresh state from storage to get updates made by orchestrator
        from wellsync_ai.data.shared_state import get_shared_state
        shared_state = get_shared_state(shared_state.state_id)
        
        state_data = shared_state.get_state_data()
        recent = state_data.get('recent_data', {})
        proposals_wrapper = recent.get('agent_proposals', {})
        proposals = proposals_wrapper.get('data', {})
        
        print(f"Proposals keys found: {list(proposals.keys())}")
        
        if 'FitnessAgent' in proposals:
            print("\nFitnessAgent Proposal Status:")
            print(proposals['FitnessAgent'])
            
            if proposals['FitnessAgent'].get('is_error'):
                print("VERIFICATION PASSED: FitnessAgent error was captured and handled gracefully.")
            else:
                print("VERIFICATION FAILED: FitnessAgent error was NOT captured as expected.")
        else:
            print("VERIFICATION FAILED: FitnessAgent proposal missing entirely.")
            
    except Exception as e:
        print(f"VERIFICATION FAILED: Workflow crashed with {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_error_handling())
