"""
Nutrition Agent for WellSync AI system.

Implements NutritionAgent with nutritional optimization prompts,
budget constraint handling, food substitution algorithms, and
nutrient adequacy validation and meal timing optimization.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from wellsync_ai.agents.base_agent import WellnessAgent
from wellsync_ai.data.database import get_database_manager


class NutritionAgent(WellnessAgent):
    """
    Nutrition expert agent for meal planning under constraints.
    
    Specializes in creating meal plans that meet nutritional needs
    within budget constraints, handle food availability and dietary
    restrictions, and coordinate energy demands with fitness goals.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize NutritionAgent with domain-specific configuration."""
        
        system_prompt = """You are a nutrition expert agent in the WellSync AI system.
Your role is to create meal plans that meet nutritional needs within real-world constraints.

CORE RESPONSIBILITIES:
- Design nutritionally adequate meal plans within budget constraints
- Handle food availability, dietary restrictions, and preparation time limits
- Coordinate energy and nutrient timing with fitness demands
- Provide food substitutions when preferred items are unavailable or too expensive
- Adapt meal plans dynamically based on missed meals and changing constraints

CONSTRAINTS YOU MUST RESPECT:
- Budget limitations (never exceed available food budget)
- Food availability and seasonal variations
- Dietary restrictions (allergies, intolerances, ethical preferences)
- Meal preparation time limits
- Energy demands from Fitness Agent (pre/post workout nutrition)
- Kitchen equipment and cooking skill limitations

NUTRITIONAL ADEQUACY RULES:
- Meet daily caloric needs based on activity level and goals
- Ensure adequate protein (0.8-2.2g per kg body weight based on activity)
- Include essential fatty acids (omega-3, omega-6)
- Meet micronutrient needs through diverse food sources
- Balance macronutrients appropriately for goals (weight loss/gain/maintenance)
- Time nutrients around workouts when relevant

BUDGET OPTIMIZATION STRATEGIES:
- Prioritize nutrient-dense, cost-effective foods (eggs, legumes, seasonal produce)
- Suggest bulk cooking and meal prep to reduce costs
- Provide cheaper alternatives for expensive ingredients
- Consider frozen/canned alternatives when fresh is too expensive
- Optimize portion sizes to minimize waste

MEAL TIMING PRINCIPLES:
- Pre-workout: easily digestible carbs 30-60 minutes before
- Post-workout: protein + carbs within 2 hours for recovery
- Distribute protein throughout the day (20-30g per meal)
- Time larger meals when user has more time for preparation
- Consider work schedule and meal break timing

OUTPUT FORMAT: Always respond with valid JSON containing:
{
    "meal_plan": {
        "daily_meals": [...],
        "weekly_schedule": {...},
        "shopping_list": [...],
        "prep_instructions": [...]
    },
    "confidence": 0.0-1.0,
    "nutritional_adequacy": "low/medium/high",
    "budget_utilization": 0.0-1.0,
    "energy_coordination": {...},
    "constraints_used": [...],
    "dependencies": [...],
    "reasoning": "detailed explanation of meal planning decisions"
}

CRITICAL: Never exceed budget constraints. Always provide substitutions for unavailable foods."""

        super().__init__(
            agent_name="NutritionAgent",
            system_prompt=system_prompt,
            domain="nutrition",
            confidence_threshold=confidence_threshold
        )
        
        # Nutrition-specific attributes
        self.food_database = self._initialize_food_database()
        self.nutrient_targets = self._initialize_nutrient_targets()
        self.substitution_matrix = self._initialize_substitution_matrix()
        self.seasonal_availability = self._initialize_seasonal_data()
        
        # Budget optimization parameters
        self.cost_efficiency_threshold = 0.8  # Minimum cost efficiency for food choices
        self.budget_buffer = 0.1  # Keep 10% budget buffer for price variations
        self.bulk_discount_factor = 0.85  # 15% savings for bulk purchases
    
    def build_wellness_prompt(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build nutrition-specific wellness prompt."""
        
        # Extract relevant data
        nutrition_history = user_data.get('nutrition_history', {})
        dietary_preferences = user_data.get('dietary_preferences', {})
        goals = user_data.get('goals', {}).get('nutrition', {})
        budget_constraints = constraints.get('budget', {})
        time_constraints = constraints.get('meal_prep_time', {})
        
        # Get fitness energy demands from shared state
        fitness_demands = {}
        if shared_state:
            fitness_proposal = shared_state.get('agent_proposals', {}).get('FitnessAgent', {})
            if fitness_proposal:
                fitness_demands = {
                    'energy_demand': fitness_proposal.get('energy_demand', 'medium'),
                    'workout_schedule': fitness_proposal.get('workout_plan', {}).get('weekly_schedule', []),
                    'training_load': fitness_proposal.get('training_load_score', 50)
                }
        
        # Calculate nutritional needs
        nutritional_needs = self._calculate_nutritional_needs(user_data, fitness_demands)
        budget_analysis = self._analyze_budget_constraints(budget_constraints, nutritional_needs)
        
        # Build comprehensive prompt
        prompt = f"""
MEAL PLANNING REQUEST

USER PROFILE:
- Dietary preferences: {json.dumps(dietary_preferences, indent=2)}
- Nutrition goals: {json.dumps(goals, indent=2)}
- Recent nutrition history: {json.dumps(nutrition_history, indent=2)}

CONSTRAINTS TO RESPECT:
- Budget available: {json.dumps(budget_constraints, indent=2)}
- Meal prep time: {json.dumps(time_constraints, indent=2)}
- Dietary restrictions: {dietary_preferences.get('restrictions', [])}
- Food allergies: {dietary_preferences.get('allergies', [])}

NUTRITIONAL REQUIREMENTS:
{json.dumps(nutritional_needs, indent=2)}

FITNESS COORDINATION:
{json.dumps(fitness_demands, indent=2)}

BUDGET ANALYSIS:
{json.dumps(budget_analysis, indent=2)}

FOOD AVAILABILITY:
{self._get_seasonal_availability_info()}

TASK: Design a nutritionally adequate meal plan that:
1. Meets all nutritional requirements within budget constraints
2. Respects dietary preferences and restrictions
3. Coordinates with fitness energy demands and workout timing
4. Fits within available meal preparation time
5. Provides cost-effective food substitutions when needed
6. Optimizes nutrient timing for performance and recovery

Consider seasonal food availability, bulk purchasing opportunities, and meal prep efficiency.
Explain your reasoning for food choices, portion sizes, and meal timing decisions.
"""
        
        return prompt
    
    def _calculate_nutritional_needs(self, user_data: Dict[str, Any], fitness_demands: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate daily nutritional needs based on user profile and activity.
        
        Args:
            user_data: User profile and biometric data
            fitness_demands: Energy demands from fitness agent
            
        Returns:
            Nutritional requirements dictionary
        """
        # Basic user metrics
        weight_kg = user_data.get('weight_kg', 70)
        height_cm = user_data.get('height_cm', 170)
        age = user_data.get('age', 30)
        sex = user_data.get('sex', 'male')
        activity_level = fitness_demands.get('energy_demand', 'medium')
        
        # Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor equation
        if sex.lower() == 'male':
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        
        # Activity multipliers
        activity_multipliers = {
            'low': 1.2,
            'medium': 1.55,
            'high': 1.9
        }
        
        # Calculate Total Daily Energy Expenditure (TDEE)
        tdee = bmr * activity_multipliers.get(activity_level, 1.55)
        
        # Adjust for goals
        goals = user_data.get('goals', {}).get('nutrition', {})
        goal_type = goals.get('type', 'maintenance')
        
        if goal_type == 'weight_loss':
            calorie_target = tdee - 500  # 1 lb/week loss
        elif goal_type == 'weight_gain':
            calorie_target = tdee + 300  # Lean gain
        else:
            calorie_target = tdee
        
        # Calculate macronutrient needs
        protein_per_kg = self._get_protein_needs(activity_level, goal_type)
        protein_calories = weight_kg * protein_per_kg * 4  # 4 cal/g protein
        
        # Fat: 25-35% of calories
        fat_calories = calorie_target * 0.30
        fat_grams = fat_calories / 9  # 9 cal/g fat
        
        # Carbs: remaining calories
        carb_calories = calorie_target - protein_calories - fat_calories
        carb_grams = carb_calories / 4  # 4 cal/g carbs
        
        return {
            'calories': round(calorie_target),
            'protein_g': round(weight_kg * protein_per_kg),
            'carbs_g': round(carb_grams),
            'fat_g': round(fat_grams),
            'fiber_g': round(calorie_target / 1000 * 14),  # 14g per 1000 calories
            'water_ml': round(weight_kg * 35),  # 35ml per kg body weight
            'micronutrients': self._get_micronutrient_targets(age, sex)
        }
    
    def _get_protein_needs(self, activity_level: str, goal_type: str) -> float:
        """Get protein needs in g/kg body weight."""
        base_needs = {
            'low': 0.8,
            'medium': 1.2,
            'high': 1.6
        }
        
        protein_per_kg = base_needs.get(activity_level, 1.2)
        
        # Adjust for goals
        if goal_type == 'weight_loss':
            protein_per_kg *= 1.2  # Higher protein for muscle preservation
        elif goal_type == 'muscle_gain':
            protein_per_kg = max(protein_per_kg, 1.6)
        
        return min(protein_per_kg, 2.2)  # Cap at 2.2g/kg
    
    def _get_micronutrient_targets(self, age: int, sex: str) -> Dict[str, float]:
        """Get micronutrient targets based on RDA."""
        # Simplified RDA targets (would be more comprehensive in production)
        base_targets = {
            'vitamin_c_mg': 90 if sex.lower() == 'male' else 75,
            'vitamin_d_iu': 600 if age < 70 else 800,
            'calcium_mg': 1000 if age < 50 else 1200,
            'iron_mg': 8 if sex.lower() == 'male' else 18,
            'magnesium_mg': 400 if sex.lower() == 'male' else 310,
            'potassium_mg': 3500,
            'sodium_mg': 2300  # Upper limit
        }
        
        return base_targets
    
    def _analyze_budget_constraints(self, budget_constraints: Dict[str, Any], nutritional_needs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze budget constraints against nutritional needs.
        
        Args:
            budget_constraints: Available budget information
            nutritional_needs: Required nutritional targets
            
        Returns:
            Budget analysis with recommendations
        """
        weekly_budget = budget_constraints.get('weekly_food_budget', 100)
        daily_budget = weekly_budget / 7
        
        # Estimate cost per calorie for different food categories
        cost_per_calorie = {
            'grains': 0.002,  # $0.002 per calorie
            'legumes': 0.003,
            'vegetables': 0.008,
            'fruits': 0.006,
            'proteins': 0.012,
            'dairy': 0.005,
            'fats': 0.004
        }
        
        # Estimate minimum cost to meet nutritional needs
        estimated_daily_cost = (
            nutritional_needs['calories'] * 0.006  # Average cost per calorie
        )
        
        budget_adequacy = daily_budget / estimated_daily_cost if estimated_daily_cost > 0 else 1.0
        
        return {
            'daily_budget': daily_budget,
            'estimated_daily_cost': estimated_daily_cost,
            'budget_adequacy': budget_adequacy,
            'budget_status': 'adequate' if budget_adequacy >= 1.0 else 'tight',
            'cost_optimization_needed': budget_adequacy < 1.2,
            'recommendations': self._get_budget_recommendations(budget_adequacy)
        }
    
    def _get_budget_recommendations(self, budget_adequacy: float) -> List[str]:
        """Get budget optimization recommendations."""
        recommendations = []
        
        if budget_adequacy < 0.8:
            recommendations.extend([
                "Focus on cost-effective protein sources (eggs, legumes, canned fish)",
                "Buy seasonal produce and frozen vegetables",
                "Consider bulk purchases of grains and legumes",
                "Minimize processed and convenience foods"
            ])
        elif budget_adequacy < 1.2:
            recommendations.extend([
                "Look for sales and seasonal produce",
                "Consider generic/store brands",
                "Plan meals around affordable staples"
            ])
        else:
            recommendations.append("Budget allows for diverse, high-quality food choices")
        
        return recommendations
    
    def _get_seasonal_availability_info(self) -> str:
        """Get current seasonal food availability information."""
        current_month = datetime.now().month
        
        # Simplified seasonal availability (Northern Hemisphere)
        seasonal_foods = {
            'spring': ['asparagus', 'peas', 'strawberries', 'spinach'],
            'summer': ['tomatoes', 'zucchini', 'berries', 'corn'],
            'fall': ['apples', 'squash', 'sweet_potatoes', 'brussels_sprouts'],
            'winter': ['citrus', 'root_vegetables', 'cabbage', 'stored_grains']
        }
        
        if current_month in [3, 4, 5]:
            season = 'spring'
        elif current_month in [6, 7, 8]:
            season = 'summer'
        elif current_month in [9, 10, 11]:
            season = 'fall'
        else:
            season = 'winter'
        
        in_season = seasonal_foods.get(season, [])
        
        return f"Current season: {season}. In-season foods: {', '.join(in_season)}"
    
    def _initialize_food_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize food database with nutritional and cost information."""
        return {
            # Proteins
            'eggs': {
                'category': 'protein',
                'calories_per_100g': 155,
                'protein_g': 13,
                'carbs_g': 1,
                'fat_g': 11,
                'cost_per_100g': 0.50,
                'shelf_life_days': 21,
                'prep_time_minutes': 5
            },
            'chicken_breast': {
                'category': 'protein',
                'calories_per_100g': 165,
                'protein_g': 31,
                'carbs_g': 0,
                'fat_g': 3.6,
                'cost_per_100g': 2.50,
                'shelf_life_days': 3,
                'prep_time_minutes': 20
            },
            'lentils': {
                'category': 'protein',
                'calories_per_100g': 116,
                'protein_g': 9,
                'carbs_g': 20,
                'fat_g': 0.4,
                'cost_per_100g': 0.30,
                'shelf_life_days': 365,
                'prep_time_minutes': 25
            },
            
            # Carbohydrates
            'brown_rice': {
                'category': 'grain',
                'calories_per_100g': 123,
                'protein_g': 2.6,
                'carbs_g': 23,
                'fat_g': 0.9,
                'cost_per_100g': 0.25,
                'shelf_life_days': 180,
                'prep_time_minutes': 30
            },
            'oats': {
                'category': 'grain',
                'calories_per_100g': 389,
                'protein_g': 16.9,
                'carbs_g': 66,
                'fat_g': 6.9,
                'cost_per_100g': 0.40,
                'shelf_life_days': 365,
                'prep_time_minutes': 10
            },
            
            # Vegetables
            'broccoli': {
                'category': 'vegetable',
                'calories_per_100g': 34,
                'protein_g': 2.8,
                'carbs_g': 7,
                'fat_g': 0.4,
                'cost_per_100g': 1.20,
                'shelf_life_days': 7,
                'prep_time_minutes': 10
            },
            'spinach': {
                'category': 'vegetable',
                'calories_per_100g': 23,
                'protein_g': 2.9,
                'carbs_g': 3.6,
                'fat_g': 0.4,
                'cost_per_100g': 2.00,
                'shelf_life_days': 5,
                'prep_time_minutes': 5
            }
            # Additional foods would be added here
        }
    
    def _initialize_nutrient_targets(self) -> Dict[str, Dict[str, float]]:
        """Initialize nutrient targets for different demographics."""
        return {
            'adult_male': {
                'calories': 2500,
                'protein_g': 56,
                'fiber_g': 38,
                'vitamin_c_mg': 90,
                'calcium_mg': 1000,
                'iron_mg': 8
            },
            'adult_female': {
                'calories': 2000,
                'protein_g': 46,
                'fiber_g': 25,
                'vitamin_c_mg': 75,
                'calcium_mg': 1000,
                'iron_mg': 18
            }
        }
    
    def _initialize_substitution_matrix(self) -> Dict[str, List[str]]:
        """Initialize food substitution matrix for alternatives."""
        return {
            'chicken_breast': ['turkey_breast', 'fish_fillet', 'tofu', 'tempeh'],
            'beef': ['ground_turkey', 'lentils', 'black_beans', 'mushrooms'],
            'milk': ['almond_milk', 'soy_milk', 'oat_milk', 'coconut_milk'],
            'wheat_flour': ['almond_flour', 'coconut_flour', 'rice_flour', 'oat_flour'],
            'butter': ['olive_oil', 'avocado_oil', 'coconut_oil', 'nut_butter'],
            'sugar': ['honey', 'maple_syrup', 'stevia', 'dates']
        }
    
    def _initialize_seasonal_data(self) -> Dict[str, List[str]]:
        """Initialize seasonal food availability data."""
        return {
            'spring': ['asparagus', 'peas', 'strawberries', 'spinach', 'lettuce'],
            'summer': ['tomatoes', 'zucchini', 'berries', 'corn', 'peaches'],
            'fall': ['apples', 'squash', 'sweet_potatoes', 'brussels_sprouts', 'pears'],
            'winter': ['citrus', 'root_vegetables', 'cabbage', 'kale', 'pomegranates']
        }
    
    def calculate_meal_cost(self, meal_plan: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate total cost of a meal plan.
        
        Args:
            meal_plan: Meal plan with ingredients and quantities
            
        Returns:
            Cost breakdown dictionary
        """
        total_cost = 0.0
        cost_breakdown = {}
        
        for meal in meal_plan.get('daily_meals', []):
            meal_cost = 0.0
            
            for ingredient in meal.get('ingredients', []):
                food_name = ingredient.get('food')
                quantity_g = ingredient.get('quantity_g', 0)
                
                if food_name in self.food_database:
                    food_data = self.food_database[food_name]
                    cost_per_100g = food_data.get('cost_per_100g', 0)
                    ingredient_cost = (quantity_g / 100) * cost_per_100g
                    meal_cost += ingredient_cost
            
            cost_breakdown[meal.get('name', 'unnamed_meal')] = meal_cost
            total_cost += meal_cost
        
        cost_breakdown['total_daily_cost'] = total_cost
        return cost_breakdown
    
    def optimize_for_budget(self, meal_plan: Dict[str, Any], budget_limit: float) -> Dict[str, Any]:
        """
        Optimize meal plan to fit within budget constraints.
        
        Args:
            meal_plan: Original meal plan
            budget_limit: Maximum daily budget
            
        Returns:
            Optimized meal plan within budget
        """
        current_cost = self.calculate_meal_cost(meal_plan)['total_daily_cost']
        
        if current_cost <= budget_limit:
            return meal_plan  # Already within budget
        
        # Strategy: Replace expensive ingredients with cheaper alternatives
        optimized_plan = meal_plan.copy()
        
        for meal in optimized_plan.get('daily_meals', []):
            for ingredient in meal.get('ingredients', []):
                food_name = ingredient.get('food')
                
                # Find cheaper substitutions
                if food_name in self.substitution_matrix:
                    alternatives = self.substitution_matrix[food_name]
                    
                    # Find cheapest alternative
                    cheapest_alternative = None
                    lowest_cost = float('inf')
                    
                    for alt in alternatives:
                        if alt in self.food_database:
                            alt_cost = self.food_database[alt].get('cost_per_100g', float('inf'))
                            if alt_cost < lowest_cost:
                                lowest_cost = alt_cost
                                cheapest_alternative = alt
                    
                    # Replace if significantly cheaper
                    original_cost = self.food_database.get(food_name, {}).get('cost_per_100g', 0)
                    if cheapest_alternative and lowest_cost < original_cost * 0.8:
                        ingredient['food'] = cheapest_alternative
                        ingredient['substitution_reason'] = f"Budget optimization: replaced {food_name}"
        
        return optimized_plan
    
    def validate_nutritional_adequacy(self, meal_plan: Dict[str, Any], targets: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate meal plan against nutritional targets.
        
        Args:
            meal_plan: Meal plan to validate
            targets: Nutritional targets to meet
            
        Returns:
            Validation results with adequacy scores
        """
        totals = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'fiber_g': 0
        }
        
        # Calculate totals from meal plan
        for meal in meal_plan.get('daily_meals', []):
            for ingredient in meal.get('ingredients', []):
                food_name = ingredient.get('food')
                quantity_g = ingredient.get('quantity_g', 0)
                
                if food_name in self.food_database:
                    food_data = self.food_database[food_name]
                    multiplier = quantity_g / 100
                    
                    totals['calories'] += food_data.get('calories_per_100g', 0) * multiplier
                    totals['protein_g'] += food_data.get('protein_g', 0) * multiplier
                    totals['carbs_g'] += food_data.get('carbs_g', 0) * multiplier
                    totals['fat_g'] += food_data.get('fat_g', 0) * multiplier
        
        # Calculate adequacy scores
        adequacy_scores = {}
        for nutrient, target in targets.items():
            if nutrient in totals and target > 0:
                adequacy_scores[nutrient] = min(totals[nutrient] / target, 2.0)  # Cap at 200%
        
        # Overall adequacy score
        overall_adequacy = sum(adequacy_scores.values()) / len(adequacy_scores) if adequacy_scores else 0
        
        return {
            'totals': totals,
            'targets': targets,
            'adequacy_scores': adequacy_scores,
            'overall_adequacy': overall_adequacy,
            'adequacy_level': 'high' if overall_adequacy >= 0.9 else 'medium' if overall_adequacy >= 0.7 else 'low',
            'deficiencies': [k for k, v in adequacy_scores.items() if v < 0.8],
            'excesses': [k for k, v in adequacy_scores.items() if v > 1.5]
        }


def create_nutrition_agent(confidence_threshold: float = 0.7) -> NutritionAgent:
    """
    Factory function to create a NutritionAgent instance.
    
    Args:
        confidence_threshold: Minimum confidence for proposals
        
    Returns:
        Configured NutritionAgent instance
    """
    return NutritionAgent(confidence_threshold=confidence_threshold)