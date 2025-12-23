"""
Preference & Fatigue Modeler Worker Agent.

Tracks food repetition, user rejections, preference drift,
and outputs penalties, cooldown lists, and safe defaults.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict

from wellsync_ai.agents.base_agent import WellnessAgent


class PreferenceFatigueModeler(WellnessAgent):
    """
    Preference and fatigue tracking worker agent.
    
    Manages:
    - Food repetition tracking and fatigue scores
    - User rejection history and pattern detection
    - Preference drift over time
    - Cooldown lists and safe default recommendations
    """
    
    SYSTEM_PROMPT = """You are a Preference & Fatigue Modeler for a nutrition planning system.

Your role is to track user food preferences, detect fatigue from repetition,
and maintain cooldown lists to ensure meal variety and user satisfaction.

## Your Responsibilities:
1. Track food repetition frequency and compute fatigue scores
2. Record and analyze rejected items with rejection reasons
3. Maintain cooldown lists (items to avoid for N days)
4. Identify safe defaults (items user consistently accepts)
5. Detect preference drift over time

## Output Format (STRICT JSON):
{
    "fatigue_analysis": {
        "high_fatigue_items": [
            {
                "item": "<food item>",
                "times_in_last_7_days": <number>,
                "fatigue_score": <0.0-1.0>,
                "recommended_cooldown_days": <number>
            }
        ],
        "moderate_fatigue_items": [...],
        "fresh_items": ["<items not eaten recently>"]
    },
    "rejection_patterns": {
        "recently_rejected": [
            {
                "item": "<food item>",
                "rejection_date": "<YYYY-MM-DD>",
                "reason": "<if known>",
                "cooldown_until": "<YYYY-MM-DD>"
            }
        ],
        "frequently_rejected": ["<items rejected multiple times>"],
        "rejection_categories": {
            "<category>": <count>
        }
    },
    "safe_defaults": [
        {
            "item": "<food item>",
            "acceptance_rate": <0.0-1.0>,
            "last_eaten": "<YYYY-MM-DD>",
            "can_suggest_today": true|false
        }
    ],
    "preference_drift": {
        "trending_up": ["<items user is accepting more>"],
        "trending_down": ["<items user is rejecting more>"],
        "stable_favorites": ["<consistently liked items>"]
    },
    "cooldown_list": ["<items to avoid today>"],
    "penalty_adjustments": {
        "<item>": <penalty_multiplier 0.0-2.0>
    },
    "confidence": <0.0-1.0>,
    "reasoning": "<summary of preference analysis>"
}

## Rules:
- Items eaten 3+ times in 7 days get HIGH fatigue score
- Rejected items get automatic 3-day cooldown
- Safe defaults must have >80% acceptance rate
- Never penalize items user explicitly marked as favorites
- Consider time-of-day preferences (breakfast vs dinner items)
"""

    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize PreferenceFatigueModeler."""
        super().__init__(
            agent_name="PreferenceFatigueModeler",
            system_prompt=self.SYSTEM_PROMPT,
            domain="nutrition_preferences",
            confidence_threshold=confidence_threshold
        )
        
        # Default cooldown periods (days)
        self.cooldown_rules = {
            "rejected": 3,
            "high_repetition": 2,
            "disliked_category": 5
        }
        
        # Common food categories for pattern detection
        self.food_categories = {
            "dal": "lentils",
            "rajma": "lentils",
            "chana": "lentils",
            "rice": "grains",
            "roti": "grains",
            "paratha": "grains",
            "chicken": "non_veg",
            "egg": "non_veg",
            "fish": "non_veg",
            "paneer": "dairy",
            "curd": "dairy",
            "milk": "dairy",
            "salad": "vegetables",
            "sabzi": "vegetables"
        }

    def build_wellness_prompt(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build preference analysis prompt."""
        
        # Extract meal history
        meal_history = user_data.get('meal_history', [])
        recent_meals = meal_history[-21:]  # Last 3 weeks
        
        # Extract rejection history
        rejections = user_data.get('rejected_items', [])
        
        # Extract explicit preferences
        favorites = user_data.get('favorites', [])
        dislikes = user_data.get('dislikes', [])
        
        # Calculate frequency stats
        frequency = self._calculate_frequency(recent_meals)
        
        prompt = f"""
## User Preference Data

### Recent Meal History (Last 21 meals):
{json.dumps(recent_meals, indent=2)}

### Frequency Analysis (Last 7 days):
{json.dumps(frequency, indent=2)}

### Rejection History:
{json.dumps(rejections, indent=2)}

### Explicit Preferences:
- Favorites: {favorites}
- Dislikes: {dislikes}

### Current Constraints:
- Dietary Restrictions: {user_data.get('dietary_restrictions', [])}
- Meal Time: {constraints.get('meal_time', 'lunch')}
- Variety Preference: {user_data.get('variety_preference', 'moderate')}  # low, moderate, high

### Today's Date: {datetime.now().strftime('%Y-%m-%d')}

## Task
Analyze the user's food preferences and fatigue levels:
1. Identify items with high repetition fatigue
2. Compile cooldown list for today
3. Find safe defaults that can be suggested
4. Detect any preference trends
5. Calculate penalty adjustments for meal scoring

Respond with strict JSON format as specified in your system prompt.
"""
        return prompt

    def _calculate_frequency(self, meals: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate food item frequency from meal history."""
        frequency = defaultdict(int)
        
        # Filter to last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        
        for meal in meals:
            meal_date = meal.get('date', '')
            if meal_date:
                try:
                    if datetime.strptime(meal_date, '%Y-%m-%d') >= cutoff:
                        for item in meal.get('items', []):
                            frequency[item] += 1
                except ValueError:
                    pass
            else:
                # If no date, assume recent
                for item in meal.get('items', []):
                    frequency[item] += 1
        
        return dict(frequency)

    def calculate_fatigue_score(self, item: str, frequency: int, days: int = 7) -> float:
        """Calculate fatigue score for an item based on frequency."""
        if days == 0:
            return 0.0
        
        # Normalized frequency (times per day)
        normalized = frequency / days
        
        # Fatigue curve: exponential increase above 0.5 times/day
        if normalized <= 0.3:
            return 0.0
        elif normalized <= 0.5:
            return 0.3
        elif normalized <= 0.7:
            return 0.6
        else:
            return min(1.0, 0.6 + (normalized - 0.7) * 2)

    def get_cooldown_items(self, rejections: List[Dict[str, Any]], high_fatigue: List[str]) -> List[str]:
        """Get list of items that should be on cooldown today."""
        cooldown = set()
        today = datetime.now()
        
        # Add recently rejected items
        for rejection in rejections:
            rejection_date = rejection.get('date', '')
            if rejection_date:
                try:
                    reject_dt = datetime.strptime(rejection_date, '%Y-%m-%d')
                    cooldown_days = self.cooldown_rules["rejected"]
                    if (today - reject_dt).days < cooldown_days:
                        cooldown.add(rejection.get('item', ''))
                except ValueError:
                    pass
        
        # Add high fatigue items
        cooldown.update(high_fatigue)
        
        return list(cooldown)


def create_preference_fatigue_modeler(confidence_threshold: float = 0.7) -> PreferenceFatigueModeler:
    """Factory function to create PreferenceFatigueModeler instance."""
    return PreferenceFatigueModeler(confidence_threshold=confidence_threshold)
