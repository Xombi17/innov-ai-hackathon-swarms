from pydantic import BaseModel
from typing import List, Optional

class FoodItem(BaseModel):
    name: str
    cost: float
    prep_time: int  # in minutes
    calories: int
    protein: int  # in grams
    tags: List[str] = []
    meal_type: str # e.g., "breakfast", "lunch", "dinner", "snack"

    def __str__(self):
        return f"{self.name} (${self.cost}, {self.prep_time}m, {self.calories}kcal)"
