import asyncio
import time
from wellsync_ai.workflows.wellness_orchestrator import WellnessWorkflowOrchestrator
from wellsync_ai.data.shared_state import SharedStateManager
from wellsync_ai.utils.cache_manager import get_cache_manager

async def verify_caching():
    print("Initializing Caching Verification...")
    
    # Setup state
    state_manager = SharedStateManager()
    shared_state = state_manager.create_shared_state(user_id="test_cache_user")
    shared_state.update_user_profile({
        "user_id": "test_cache_user",
        "name": "Cache Test User",
        "age": 28,
        "goals": {"sleep": "improve_quality"}
    })
    
    orchestrator = WellnessWorkflowOrchestrator()
    cache_manager = get_cache_manager()
    
    # Invalidate potential old keys
    print("Clearing cache for test user...")
    cache_manager.invalidate_pattern("agent_proposal:*")
    
    # First Run - Should be slow (MISS)
    print("\n--- First Run (Cold Cache) ---")
    start_time = time.time()
    result1 = await orchestrator.execute_workflow(shared_state.state_id)
    duration1 = time.time() - start_time
    print(f"First run duration: {duration1:.2f}s")
    
    # Second Run - Should be fast (HIT)
    print("\n--- Second Run (Warm Cache) ---")
    start_time = time.time()
    result2 = await orchestrator.execute_workflow(shared_state.state_id)
    duration2 = time.time() - start_time
    print(f"Second run duration: {duration2:.2f}s")
    
    # Verification Logic
    # The orchestrator has a 5s sleep per agent x 4 agents = ~20s min wait time sequentially
    # With caching, it should be near instant.
    
    print("\n--- Verification Results ---")
    if duration2 < duration1 and duration2 < 5:
        print("SUCCESS: Cache HIT significantly reduced execution time.")
        print(f"Speedup: {duration1/duration2:.1f}x")
    else:
        print("FAILURE: Cache HIT did not execute fast enough or Cold Cache was too fast.")
        print(f"Cold: {duration1}s, Warm: {duration2}s")

if __name__ == "__main__":
    asyncio.run(verify_caching())
