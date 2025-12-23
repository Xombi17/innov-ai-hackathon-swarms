"""
Constraint & Budget Analyst Worker Agent.

Computes budget utilization, cost-per-nutrient heuristics,
and produces constraint feasibility reports with recommended substitutions.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from wellsync_ai.agents.base_agent import WellnessAgent


class ConstraintBudgetAnalyst(WellnessAgent):
    """
    Budget and constraint analysis worker agent.
    
    Analyzes:
    - Daily/weekly budget utilization
    - Cost-per-protein and cost-per-calorie metrics
    - Budget constraint violations
    - Recommends substitutions for budget optimization
    """
    
    SYSTEM_PROMPT = """You are a Budget & Constraint Analyst for a nutrition planning system.

Your role is to analyze financial constraints against nutritional requirements and provide
actionable budget optimization recommendations.

## Your Responsibilities:
1. Calculate budget utilization (spent vs remaining)
2. Compute cost-per-nutrient heuristics (cost per gram of protein, per calorie, etc.)
3. Identify budget constraint violations
4. Recommend cost-effective substitutions that maintain nutritional value

## Output Format (STRICT JSON):
{
    "budget_analysis": {
        "daily_budget": <number>,
        "spent_today": <number>,
        "remaining_today": <number>,
        "weekly_budget": <number>,
        "spent_this_week": <number>,
        "utilization_percent": <number>
    },
    "cost_heuristics": {
        "cost_per_gram_protein": <number>,
        "cost_per_100_calories": <number>,
        "cost_per_meal_average": <number>
    },
    "constraint_violations": [
        {
            "type": "budget_exceeded|near_limit|inefficient_spending",
            "severity": "low|medium|high",
            "description": "<string>"
        }
    ],
    "substitution_recommendations": [
        {
            "current_item": "<string>",
            "substitute": "<string>",
            "savings": <number>,
            "nutritional_comparison": "<string>"
        }
    ],
    "feasibility_score": <0.0-1.0>,
    "reasoning": "<brief analysis summary>"
}

## Rules:
- Always prioritize protein-per-rupee when budget is tight
- Never recommend nutritionally inferior substitutions without noting trade-offs
- Consider bulk buying and seasonal availability for cost optimization
- Be specific with numbers and concrete recommendations
"""

    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize ConstraintBudgetAnalyst."""
        super().__init__(
            agent_name="ConstraintBudgetAnalyst",
            system_prompt=self.SYSTEM_PROMPT,
            domain="nutrition_budget",
            confidence_threshold=confidence_threshold
        )
        
        # Cost database for common foods (INR per 100g)
        self.food_costs = {
            # Proteins
            "chicken_breast": 28,
            "eggs": 8,
            "paneer": 35,
            "dal": 12,
            "soya_chunks": 15,
            "fish": 40,
            "whey_protein": 80,
            # Carbs
            "rice": 5,
            "wheat_flour": 4,
            "oats": 18,
            "bread": 8,
            # Vegetables
            "seasonal_vegetables": 4,
            "spinach": 6,
            "broccoli": 25,
            # Fats
            "cooking_oil": 15,
            "ghee": 55,
            "peanuts": 18
        }
        
        # Protein content per 100g
        self.protein_content = {
            "chicken_breast": 31,
            "eggs": 13,
            "paneer": 18,
            "dal": 24,
            "soya_chunks": 52,
            "fish": 22,
            "whey_protein": 80
        }

    def build_wellness_prompt(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build budget analysis prompt."""
        
        budget_info = constraints.get('budget', {})
        daily_budget = budget_info.get('daily', constraints.get('daily_budget', 500))
        weekly_budget = daily_budget * 7
        
        # Calculate spending history if available
        spending_history = user_data.get('spending_history', [])
        spent_today = sum(s.get('amount', 0) for s in spending_history if s.get('date') == datetime.now().strftime('%Y-%m-%d'))
        spent_this_week = sum(s.get('amount', 0) for s in spending_history[-7:])
        
        # Get nutritional targets
        protein_target = user_data.get('protein_target', 100)  # grams
        calorie_target = user_data.get('calorie_target', 2000)  # kcal
        
        # Calculate cost-per-nutrient for available budget
        remaining = daily_budget - spent_today
        
        prompt = f"""
## Current Budget State
- Daily Budget: ₹{daily_budget}
- Spent Today: ₹{spent_today}
- Remaining Today: ₹{remaining}
- Weekly Budget: ₹{weekly_budget}
- Spent This Week: ₹{spent_this_week}

## Nutritional Targets
- Daily Protein Target: {protein_target}g
- Daily Calorie Target: {calorie_target} kcal
- Activity Level: {user_data.get('activity_level', 'moderate')}

## User Preferences
- Dietary Restrictions: {user_data.get('dietary_restrictions', [])}
- Food Allergies: {user_data.get('allergies', [])}

## Available Food Options (if provided)
{json.dumps(shared_state.get('available_foods', []) if shared_state else [], indent=2)}

## Task
Analyze the budget constraints and provide:
1. Budget utilization analysis
2. Cost-per-nutrient heuristics for optimizing spending
3. Any constraint violations or risks
4. Substitution recommendations if budget is tight
5. Overall feasibility score (0.0 to 1.0) for meeting nutritional goals within budget

Respond with strict JSON format as specified in your system prompt.
"""
        return prompt

    def calculate_cost_per_protein(self, food_item: str) -> float:
        """Calculate cost per gram of protein for a food item."""
        cost = self.food_costs.get(food_item, 20)
        protein = self.protein_content.get(food_item, 10)
        if protein == 0:
            return float('inf')
        return cost / protein

    def get_budget_efficient_alternatives(self, current_foods: List[str], budget_limit: float) -> List[Dict[str, Any]]:
        """Get budget-efficient alternatives for current food choices."""
        alternatives = []
        
        for food in current_foods:
            current_cost = self.food_costs.get(food, 20)
            current_cpp = self.calculate_cost_per_protein(food)
            
            # Find cheaper alternatives with similar or better protein efficiency
            for alt_food, alt_cost in self.food_costs.items():
                if alt_food != food and alt_cost < current_cost:
                    alt_cpp = self.calculate_cost_per_protein(alt_food)
                    if alt_cpp <= current_cpp * 1.2:  # Allow 20% worse efficiency
                        alternatives.append({
                            'current': food,
                            'alternative': alt_food,
                            'savings_per_100g': current_cost - alt_cost,
                            'protein_efficiency_ratio': current_cpp / alt_cpp if alt_cpp > 0 else 0
                        })
        
        return sorted(alternatives, key=lambda x: x['savings_per_100g'], reverse=True)


def create_constraint_budget_analyst(confidence_threshold: float = 0.7) -> ConstraintBudgetAnalyst:
    """Factory function to create ConstraintBudgetAnalyst instance."""
    return ConstraintBudgetAnalyst(confidence_threshold=confidence_threshold)
