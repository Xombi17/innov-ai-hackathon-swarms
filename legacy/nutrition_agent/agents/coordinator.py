from nutrition_agent.agents.nutrition_agent import NutritionAgent
from nutrition_agent.agents.fitness_agent import FitnessAgent
from nutrition_agent.models.user_profile import UserContext

class CoordinatorAgent:
    """
    The Orchestrator.
    Manages the flow between User, Fitness, and Nutrition agents.
    """
    def __init__(self):
        self.nutrition_agent = NutritionAgent()
        self.fitness_agent = FitnessAgent()
        self.user_context = None

    def initialize_day(self, budget: float, time_available: int, workout_intensity: str):
        """
        Sets up the daily plan.
        """
        self.user_context = UserContext(
            daily_budget=budget,
            time_available=time_available
        )
        
        # 1. Get Goals from Fitness Agent
        goals = self.fitness_agent.get_daily_goals(workout_intensity)
        print(f"[Coordinator] Day Goals: {goals}")
        
        # 2. Plan Meals (Simple Sequential for now)
        # In a real swarm, this would be a negotiation loop.
        plan = {}
        
        # Breakfast
        # Assuming morning is rushed, usually less time? 
        # For simplicity, we pass global time_available, but normally we'd allocate per meal slot.
        # Let's say we split budget/time heuristically for now.
        
        # Meal 1: Breakfast
        breakfast = self.nutrition_agent.plan_meal("breakfast", self.user_context)
        if breakfast:
            self.user_context.add_meal(breakfast)
            plan["breakfast"] = breakfast

        # Meal 2: Lunch
        lunch = self.nutrition_agent.plan_meal("lunch", self.user_context)
        if lunch:
            self.user_context.add_meal(lunch)
            plan["lunch"] = lunch

        # Meal 3: Dinner (Remaining budget)
        dinner = self.nutrition_agent.plan_meal("dinner", self.user_context)
        if dinner:
            self.user_context.add_meal(dinner)
            plan["dinner"] = dinner

        return plan, self.user_context

    def handle_exception(self, event_type: str, user_context: UserContext):
        """
        Handles "Missed Lunch" or "Budget Cut".
        Returns a revised plan/message.
        """
        if event_type == "missed_lunch":
            print("[Coordinator] Handling Missed Lunch...")
            # Logic: Lunch was skipped. User is likely hungrier, and we have extra budget (saved from lunch).
            # However, we shouldn't just stuff them with calories at dinner if it's late.
            
            # 1. Update State
            # We assume lunch was NOT added to 'meals_had' or we remove it?
            # For simplicity, let's say the prompt implies we are *reacting* to the news.
            
            print(f"[Coordinator] Detected constraint violation: Missed Meal. Triggering Re-plan.")
            
            # 2. Re-plan Dinner
            # Use the "saved" budget to perhaps get a better dinner, but watch calories.
            # OR simple logic: Call nutrition agent again with updated context.
            
            new_dinner = self.nutrition_agent.plan_meal("dinner", user_context)
            if new_dinner:
                return f"⚠️ **RECOVERY PLAN ACTIVATED**: Since you missed lunch, I've updated your dinner to **{new_dinner.name}**. It has {new_dinner.protein}g protein to help hit your target."
            else:
                return "⚠️ **Alert**: Could not find a suitable dinner even with re-planning."
        
        return "Unknown Event"
