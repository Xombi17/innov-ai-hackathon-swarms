"""
Availability Mapper Worker Agent.

Converts real-world food availability into feasible meal options.
Handles hostel mess menus, cafeteria options, and local availability.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from wellsync_ai.agents.base_agent import WellnessAgent


class AvailabilityMapper(WellnessAgent):
    """
    Food availability mapping worker agent.
    
    Converts real-world availability constraints into feasible options:
    - Hostel/mess menu parsing
    - Cafeteria/restaurant options
    - Local market availability
    - Cooking access considerations
    """
    
    SYSTEM_PROMPT = """You are an Availability Mapper for a nutrition planning system.

Your role is to convert real-world food availability into actionable meal options.
You ONLY suggest meals that are actually feasible given the user's access constraints.

## Your Responsibilities:
1. Parse and understand available food sources (mess, cafeteria, local shops)
2. Generate feasible meal candidates based on ACTUAL availability
3. Consider cooking access and time constraints
4. Never suggest "fantasy recipes" that require unavailable ingredients

## Output Format (STRICT JSON):
{
    "available_sources": [
        {
            "source_type": "mess|cafeteria|restaurant|home_cooking|delivery",
            "name": "<string>",
            "available_items": ["<item1>", "<item2>"],
            "timing": {"open": "<HH:MM>", "close": "<HH:MM>"},
            "accessible": true|false
        }
    ],
    "feasible_meals": [
        {
            "meal_time": "breakfast|lunch|dinner|snack",
            "options": [
                {
                    "name": "<meal name>",
                    "source": "<source name>",
                    "items": ["<item1>", "<item2>"],
                    "estimated_cost": <number>,
                    "prep_time_minutes": <number>,
                    "nutritional_estimate": {
                        "calories": <number>,
                        "protein_g": <number>,
                        "carbs_g": <number>,
                        "fats_g": <number>
                    },
                    "feasibility_score": <0.0-1.0>
                }
            ]
        }
    ],
    "unavailable_constraints": [
        "<reason why certain options are not feasible>"
    ],
    "cooking_access": {
        "has_kitchen": true|false,
        "available_equipment": ["<equipment>"],
        "time_available_minutes": <number>
    },
    "confidence": <0.0-1.0>,
    "reasoning": "<summary of availability analysis>"
}

## Rules:
- NEVER suggest meals requiring ingredients not listed as available
- Prioritize ready-to-eat options when cooking access is limited
- Consider meal timing with source availability windows
- Include multiple options for each meal slot when possible
- Be realistic about prep time estimates
"""

    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize AvailabilityMapper."""
        super().__init__(
            agent_name="AvailabilityMapper",
            system_prompt=self.SYSTEM_PROMPT,
            domain="nutrition_availability",
            confidence_threshold=confidence_threshold
        )
        
        # Default meal templates for common scenarios
        self.default_meal_templates = {
            "hostel_mess": {
                "breakfast": ["idli_sambar", "poha", "upma", "bread_omelette", "paratha"],
                "lunch": ["rice_dal", "roti_sabzi", "biryani", "thali"],
                "dinner": ["chapati_curry", "rice_rasam", "pulao"]
            },
            "college_cafeteria": {
                "breakfast": ["sandwich", "dosa", "tea_biscuit"],
                "lunch": ["combo_meal", "fried_rice", "noodles", "thali"],
                "snack": ["samosa", "vada_pav", "bhel"],
                "dinner": ["wrap", "rice_curry", "pasta"]
            },
            "home_cooking": {
                "breakfast": ["oats", "eggs", "smoothie", "toast"],
                "lunch": ["meal_prep", "salad", "wrap"],
                "dinner": ["protein_rice", "stir_fry", "soup"]
            }
        }
        
        # Nutritional estimates per meal type (kcal, protein_g, carbs_g, fats_g)
        self.nutrition_estimates = {
            "idli_sambar": (250, 8, 45, 4),
            "poha": (280, 6, 50, 5),
            "bread_omelette": (350, 18, 30, 16),
            "rice_dal": (450, 15, 75, 8),
            "roti_sabzi": (380, 12, 55, 10),
            "biryani": (550, 20, 70, 18),
            "thali": (650, 22, 85, 18),
            "sandwich": (300, 10, 35, 12),
            "oats": (280, 10, 45, 6),
            "eggs": (200, 14, 2, 14),
            "default": (400, 12, 50, 12)
        }

    def build_wellness_prompt(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build availability mapping prompt."""
        
        # Extract availability information
        availability = user_data.get('food_availability', {})
        location_type = user_data.get('location_type', 'hostel')  # hostel, home, office
        cooking_access = user_data.get('cooking_access', False)
        cooking_time = constraints.get('cooking_time_minutes', 30)
        
        # Get today's menu if available
        todays_menu = availability.get('todays_menu', {})
        nearby_options = availability.get('nearby_options', [])
        
        # Current time for meal timing
        current_hour = datetime.now().hour
        upcoming_meal = self._get_upcoming_meal(current_hour)
        
        prompt = f"""
## User's Food Access Context
- Location Type: {location_type}
- Has Kitchen Access: {cooking_access}
- Available Cooking Time: {cooking_time} minutes
- Current Time: {datetime.now().strftime('%H:%M')}
- Next Meal: {upcoming_meal}

## Today's Available Options
### Mess/Cafeteria Menu (if applicable):
{json.dumps(todays_menu, indent=2) if todays_menu else "Not provided - use typical options for " + location_type}

### Nearby Food Sources:
{json.dumps(nearby_options, indent=2) if nearby_options else "Standard options for " + location_type + " setting"}

## User Constraints
- Dietary Restrictions: {user_data.get('dietary_restrictions', [])}
- Budget per Meal: ₹{constraints.get('meal_budget', 100)}
- Time Constraints: {constraints.get('time_constraints', 'flexible')}

## Previous Meals Today (avoid repetition):
{json.dumps(shared_state.get('meals_today', []) if shared_state else [], indent=2)}

## Task
Map the available food options and generate feasible meal candidates for {upcoming_meal}.
For each meal, consider:
1. What's actually available right now
2. Timing constraints (is the source open?)
3. Budget constraints
4. Prep time if cooking
5. Avoid items eaten recently

Respond with strict JSON format as specified in your system prompt.
"""
        return prompt

    def _get_upcoming_meal(self, hour: int) -> str:
        """Determine the upcoming meal based on time of day."""
        if hour < 10:
            return "breakfast"
        elif hour < 14:
            return "lunch"
        elif hour < 18:
            return "snack"
        else:
            return "dinner"

    def get_feasible_options(self, location_type: str, meal_time: str) -> List[Dict[str, Any]]:
        """Get feasible meal options based on location and time."""
        templates = self.default_meal_templates.get(location_type, self.default_meal_templates["hostel_mess"])
        meal_options = templates.get(meal_time, templates.get("lunch", []))
        
        feasible = []
        for meal in meal_options:
            nutrition = self.nutrition_estimates.get(meal, self.nutrition_estimates["default"])
            feasible.append({
                "name": meal,
                "source": location_type,
                "nutritional_estimate": {
                    "calories": nutrition[0],
                    "protein_g": nutrition[1],
                    "carbs_g": nutrition[2],
                    "fats_g": nutrition[3]
                }
            })
        return feasible


def create_availability_mapper(confidence_threshold: float = 0.7) -> AvailabilityMapper:
    """Factory function to create AvailabilityMapper instance."""
    return AvailabilityMapper(confidence_threshold=confidence_threshold)
