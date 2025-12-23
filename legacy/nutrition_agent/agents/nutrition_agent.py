from typing import List, Optional
from nutrition_agent.models.food_item import FoodItem
from nutrition_agent.models.user_profile import UserContext
from nutrition_agent.data.mock_db import get_foods
import random

class NutritionAgent:
    """
    The Architect.
    Decides 'what is the best possible meal' given constraints.
    """
    def __init__(self):
        self.name = "Nutrition Agent"

    def plan_meal(self, meal_type: str, user_context: UserContext) -> Optional[FoodItem]:
        """
        Selects a meal based on:
        1. Remaining Budget
        2. Time Availability
        3. Protein Needs
        """
        # 1. Calculate Constraints
        remaining_budget = user_context.daily_budget - user_context.budget_spent
        
        # Heuristic: Allocate budget per meal type if early in day? 
        # For now, simple logic: Try to find something that fits.
        
        candidates = get_foods(meal_type=meal_type, max_cost=remaining_budget, max_time=user_context.time_available)

        if not candidates:
            # Fallback logic: "The Failure Recovery"
            # If no candidates fit strict budget/time, we need to relax constraints or return None (Meal Skip)
            # Alternatively, find the "least bad" option
            print(f"[{self.name}] No optimal {meal_type} found for ${remaining_budget} in {user_context.time_available}m.")
            return None

        # 2. Score Candidates
        # Score = (Protein * 2) - (Cost * 5) - (PrepTime * 0.5)
        # We want high protein, low cost, low time.
        
        best_meal = None
        best_score = -float('inf')

        for food in candidates:
            score = (food.protein * 2) - (food.cost * 5) - (food.prep_time * 0.5)
            
            # Boost score if we are behind on protein
            if user_context.protein_consumed < 50: # Arbitrary daily goal half
                 score += food.protein * 1.5

            if score > best_score:
                best_score = score
                best_meal = food
        
        print(f"[{self.name}] Selected {best_meal.name} (Score: {best_score:.1f})")
        return best_meal

    def replan(self, user_context: UserContext, failed_meal_type: str):
        """
        Called when a plan fails (e.g. user skips lunch).
        Adjusts strategy for remaining meals.
        """
        # Logic: If lunch skipped, maybe bigger dinner or cheaper dinner if budget was the issue?
        pass 
