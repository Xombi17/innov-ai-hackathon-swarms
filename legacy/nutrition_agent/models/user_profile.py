from pydantic import BaseModel
from typing import List, Dict
from nutrition_agent.models.constraints import Constraint

class UserContext(BaseModel):
    daily_budget: float
    time_available: int  # in minutes for the day/meal
    preferences: List[str] = []
    dietary_restrictions: List[str] = []
    
    # Dynamic State
    calories_consumed: int = 0
    protein_consumed: int = 0
    budget_spent: float = 0.0
    meals_had: List[str] = [] # List of meal names consumed
    
    def add_meal(self, meal):
        self.calories_consumed += meal.calories
        self.protein_consumed += meal.protein
        self.budget_spent += meal.cost
        self.meals_had.append(meal.name)
