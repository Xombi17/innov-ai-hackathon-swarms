"""
Recovery & Timing Advisor Worker Agent.

Uses workload and sleep signals to recommend meal timing
and digestion load considerations. Stays in wellness scope.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from wellsync_ai.agents.base_agent import WellnessAgent


class RecoveryTimingAdvisor(WellnessAgent):
    """
    Recovery and meal timing advisor worker agent.
    
    Provides recommendations on:
    - Optimal meal timing based on activity schedule
    - Digestion load management
    - Pre/post workout nutrition timing
    - Sleep-aware dinner timing
    """
    
    SYSTEM_PROMPT = """You are a Recovery & Timing Advisor for a nutrition planning system.

Your role is to recommend optimal meal timing and digestion considerations
based on the user's activity, sleep, and recovery signals.

## Your Responsibilities:
1. Recommend optimal meal times based on activity schedule
2. Advise on digestion load (heavy vs light meals)
3. Provide pre/post workout nutrition timing
4. Consider sleep quality for evening meal recommendations
5. Stay within WELLNESS scope - NO medical advice

## Output Format (STRICT JSON):
{
    "timing_recommendations": {
        "next_meal": {
            "recommended_time": "<HH:MM>",
            "meal_type": "breakfast|lunch|dinner|snack",
            "flexibility_window": "<e.g., ±30 minutes>",
            "reasoning": "<why this time>"
        },
        "meal_schedule": [
            {
                "meal": "<meal type>",
                "time": "<HH:MM>",
                "priority": "high|medium|low"
            }
        ]
    },
    "digestion_guidance": {
        "recommended_load": "light|moderate|heavy",
        "reasoning": "<based on activity/recovery>",
        "foods_to_prioritize": ["<easy digest foods>"],
        "foods_to_avoid_now": ["<heavy/slow digest foods>"]
    },
    "workout_nutrition": {
        "pre_workout": {
            "timing_before_minutes": <number>,
            "recommended_foods": ["<foods>"],
            "avoid": ["<foods>"]
        },
        "post_workout": {
            "timing_after_minutes": <number>,
            "recommended_foods": ["<foods>"],
            "protein_priority": true|false
        }
    },
    "sleep_considerations": {
        "last_meal_before_sleep": "<HH:MM>",
        "dinner_recommendation": "light|moderate",
        "avoid_before_bed": ["<foods/drinks>"]
    },
    "recovery_signals": {
        "energy_level": "low|moderate|high",
        "recovery_status": "recovering|recovered|fatigued",
        "hydration_reminder": true|false
    },
    "confidence": <0.0-1.0>,
    "reasoning": "<summary of timing analysis>"
}

## Guardrails - STRICTLY FOLLOW:
- NO medical advice or disease-related recommendations
- NO eating disorder content or extreme restriction suggestions
- NO shame language about eating habits
- If user asks about medical conditions, respond: "Please consult a healthcare professional"
- Keep targets FLEXIBLE and adequacy-focused, not obsessive precision
- Focus on WELLNESS and PERFORMANCE, not weight or appearance
"""

    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize RecoveryTimingAdvisor."""
        super().__init__(
            agent_name="RecoveryTimingAdvisor",
            system_prompt=self.SYSTEM_PROMPT,
            domain="nutrition_timing",
            confidence_threshold=confidence_threshold
        )
        
        # Digestion time estimates (hours)
        self.digestion_times = {
            "light": {"fruits": 0.5, "salad": 1, "soup": 1, "juice": 0.5},
            "moderate": {"rice": 2, "bread": 2, "pasta": 2.5, "eggs": 2},
            "heavy": {"red_meat": 4, "fried_foods": 4, "rich_desserts": 3, "fatty_foods": 4}
        }
        
        # Pre-workout food timing (minutes before)
        self.pre_workout_timing = {
            "light_snack": 30,
            "small_meal": 60,
            "full_meal": 120
        }
        
        # Post-workout protein window (minutes after)
        self.post_workout_window = 45

    def build_wellness_prompt(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build timing advice prompt."""
        
        # Extract activity schedule
        activity_schedule = user_data.get('activity_schedule', {})
        workout_time = activity_schedule.get('workout_time', None)
        workout_duration = activity_schedule.get('workout_duration_minutes', 60)
        workout_intensity = activity_schedule.get('workout_intensity', 'moderate')
        
        # Extract sleep data
        sleep_data = user_data.get('sleep_data', {})
        bedtime = sleep_data.get('usual_bedtime', '23:00')
        wake_time = sleep_data.get('usual_wake_time', '07:00')
        last_night_quality = sleep_data.get('last_night_quality', 'good')
        hours_slept = sleep_data.get('hours_slept', 7)
        
        # Current state
        current_time = datetime.now().strftime('%H:%M')
        current_energy = user_data.get('current_energy_level', 'moderate')
        
        # Recovery info from fitness agent
        recovery_status = shared_state.get('recovery_status', 'normal') if shared_state else 'normal'
        
        prompt = f"""
## Current State
- Current Time: {current_time}
- Current Energy Level: {current_energy}
- Recovery Status: {recovery_status}

## Activity Schedule
- Workout Time: {workout_time if workout_time else 'Not scheduled today'}
- Workout Duration: {workout_duration} minutes
- Workout Intensity: {workout_intensity}
- Other Activities: {activity_schedule.get('other_activities', 'None specified')}

## Sleep Information
- Usual Bedtime: {bedtime}
- Usual Wake Time: {wake_time}
- Last Night Quality: {last_night_quality}
- Hours Slept: {hours_slept}

## Meals Already Eaten Today:
{json.dumps(shared_state.get('meals_today', []) if shared_state else [], indent=2)}

## User Preferences
- Prefers Eating: {user_data.get('eating_speed', 'moderate')}
- Digestion Sensitivity: {user_data.get('digestion_sensitivity', 'normal')}

## Task
Based on the user's activity, sleep, and current state:
1. Recommend optimal timing for the next meal
2. Suggest appropriate meal load (light/moderate/heavy)
3. If workout is scheduled, provide pre/post workout nutrition timing
4. Consider sleep timing for dinner recommendations
5. Flag any hydration or recovery priorities

REMEMBER: Stay within wellness scope. No medical advice.

Respond with strict JSON format as specified in your system prompt.
"""
        return prompt

    def get_optimal_meal_time(
        self,
        current_time: datetime,
        workout_time: Optional[datetime],
        bedtime: datetime
    ) -> Dict[str, Any]:
        """Calculate optimal meal times based on schedule."""
        
        recommendations = []
        
        # Check if workout affects timing
        if workout_time:
            pre_workout = workout_time - timedelta(hours=2)
            post_workout = workout_time + timedelta(hours=1)
            
            recommendations.append({
                "meal": "pre_workout_snack",
                "time": pre_workout.strftime('%H:%M'),
                "priority": "high"
            })
            recommendations.append({
                "meal": "post_workout",
                "time": post_workout.strftime('%H:%M'),
                "priority": "high"
            })
        
        # Dinner timing (3 hours before bed)
        dinner_time = bedtime - timedelta(hours=3)
        recommendations.append({
            "meal": "dinner",
            "time": dinner_time.strftime('%H:%M'),
            "priority": "medium"
        })
        
        return recommendations

    def assess_digestion_load(
        self,
        time_until_next_activity: int,  # minutes
        current_energy: str,
        is_evening: bool
    ) -> str:
        """Recommend digestion load based on schedule and state."""
        
        # If activity coming soon, keep it light
        if time_until_next_activity < 90:
            return "light"
        
        # If low energy and no immediate activity, moderate is fine
        if current_energy == "low" and time_until_next_activity > 120:
            return "moderate"
        
        # Evening meals should generally be lighter
        if is_evening:
            return "moderate"
        
        return "moderate"


def create_recovery_timing_advisor(confidence_threshold: float = 0.7) -> RecoveryTimingAdvisor:
    """Factory function to create RecoveryTimingAdvisor instance."""
    return RecoveryTimingAdvisor(confidence_threshold=confidence_threshold)
