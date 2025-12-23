"""
Fitness Agent for WellSync AI system.

Implements FitnessAgent with workout planning system prompts,
training load calculation, overtraining detection logic, and
constraint handling for time and equipment limitations.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from wellsync_ai.agents.base_agent import WellnessAgent
from wellsync_ai.data.database import get_database_manager


class FitnessAgent(WellnessAgent):
    """
    Fitness expert agent for sustainable workout planning.
    
    Specializes in creating workout plans that prevent overtraining,
    handle time and equipment constraints, and coordinate energy
    demands with other wellness domains.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize FitnessAgent with domain-specific configuration."""
        
        system_prompt = """You are a fitness expert agent in the WellSync AI system. 
Your role is to create sustainable workout plans that prevent overtraining and respect real-world constraints.

CORE RESPONSIBILITIES:
- Design progressive workout plans that build fitness sustainably
- Detect overtraining risk and recommend deload periods when appropriate
- Respect time availability, equipment limitations, and recovery constraints
- Coordinate energy demands with nutrition and sleep agents
- Adapt plans dynamically based on user feedback and constraint changes

CONSTRAINTS YOU MUST RESPECT:
- Time availability from user schedule (never exceed available time)
- Equipment limitations (only use available equipment)
- Recovery signals from Sleep Agent (reduce intensity when sleep debt detected)
- Energy demands coordination with Nutrition Agent
- Previous workout performance and recovery indicators

OVERTRAINING DETECTION RULES:
- If training load increases >20% week-over-week, recommend deload
- If user reports fatigue scores >7/10 for 3+ consecutive days, reduce intensity
- If heart rate variability drops >15% from baseline, prioritize recovery
- If sleep quality is poor (<6 hours or frequent wake-ups), limit high-intensity work

WORKOUT ADAPTATION PRINCIPLES:
- Progressive overload: increase volume or intensity by 5-10% weekly when appropriate
- Deload weeks: reduce volume by 40-50% every 4-6 weeks or when overtraining detected
- Time constraints: prioritize compound movements and circuit training for efficiency
- Equipment constraints: provide bodyweight alternatives and substitutions

OUTPUT FORMAT: Always respond with valid JSON containing:
{
    "workout_plan": {
        "weekly_schedule": [...],
        "exercises": [...],
        "progression_plan": "...",
        "adaptations_made": [...]
    },
    "confidence": 0.0-1.0,
    "energy_demand": "low/medium/high",
    "training_load_score": 0-100,
    "overtraining_risk": "low/medium/high",
    "constraints_used": [...],
    "dependencies": [...],
    "reasoning": "detailed explanation of workout design decisions"
}

CRITICAL: Never recommend exercises that require unavailable equipment. Always provide alternatives."""

        super().__init__(
            agent_name="FitnessAgent",
            system_prompt=system_prompt,
            domain="fitness",
            confidence_threshold=confidence_threshold
        )
        
        # Fitness-specific attributes
        self.training_load_history = []
        self.overtraining_indicators = {}
        self.equipment_database = self._initialize_equipment_database()
        self.exercise_database = self._initialize_exercise_database()
        
        # Training load calculation parameters
        self.load_decay_factor = 0.85  # Exponential decay for training load
        self.overtraining_threshold = 80  # Training load threshold for overtraining risk
        self.deload_threshold = 0.20  # 20% increase triggers deload consideration
    
    def build_wellness_prompt(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build fitness-specific wellness prompt."""
        
        # Extract relevant data
        fitness_history = user_data.get('fitness_history', {})
        current_fitness_level = user_data.get('fitness_level', 'beginner')
        goals = user_data.get('goals', {}).get('fitness', {})
        time_constraints = constraints.get('time_available', {})
        equipment_available = constraints.get('equipment', [])
        
        # Get recovery constraints from shared state
        recovery_constraints = {}
        if shared_state:
            sleep_data = shared_state.get('recent_data', {}).get('sleep', {})
            recovery_constraints = shared_state.get('agent_proposals', {}).get('SleepAgent', {}).get('constraints_for_others', {})
        
        # Calculate current training load
        current_training_load = self._calculate_training_load(fitness_history)
        overtraining_risk = self._assess_overtraining_risk(user_data, current_training_load)
        
        # Build comprehensive prompt
        prompt = f"""
WORKOUT PLANNING REQUEST

USER PROFILE:
- Current fitness level: {current_fitness_level}
- Fitness goals: {json.dumps(goals, indent=2)}
- Recent workout history: {json.dumps(fitness_history, indent=2)}

CONSTRAINTS TO RESPECT:
- Time available: {json.dumps(time_constraints, indent=2)}
- Equipment available: {equipment_available}
- Recovery constraints: {json.dumps(recovery_constraints, indent=2)}

CURRENT TRAINING METRICS:
- Training load score: {current_training_load}
- Overtraining risk: {overtraining_risk}
- Training load history: {self.training_load_history[-7:] if self.training_load_history else []}

RECOVERY SIGNALS:
{self._format_recovery_signals(user_data, shared_state)}

TASK: Design a sustainable workout plan that:
1. Respects all time and equipment constraints
2. Progresses toward fitness goals appropriately
3. Prevents overtraining based on current metrics
4. Coordinates energy demands with other wellness domains
5. Provides equipment alternatives when needed

Consider the user's training history, current recovery status, and constraint limitations.
Explain your reasoning for intensity choices, exercise selection, and progression strategy.
"""
        
        return prompt
    
    def _calculate_training_load(self, fitness_history: Dict[str, Any]) -> float:
        """
        Calculate current training load using exponentially weighted moving average.
        
        Args:
            fitness_history: Recent workout data
            
        Returns:
            Training load score (0-100)
        """
        recent_workouts = fitness_history.get('recent_workouts', [])
        if not recent_workouts:
            return 0.0
        
        # Calculate load for each workout
        workout_loads = []
        for workout in recent_workouts[-14:]:  # Last 2 weeks
            duration = workout.get('duration_minutes', 0)
            intensity = self._map_intensity_to_score(workout.get('intensity', 'low'))
            volume = workout.get('exercises_count', 0)
            
            # Training load = duration * intensity * volume factor
            load = (duration / 60) * intensity * (1 + volume * 0.1)
            workout_loads.append(load)
        
        # Apply exponential decay (recent workouts weighted more heavily)
        weighted_load = 0.0
        total_weight = 0.0
        
        for i, load in enumerate(reversed(workout_loads)):
            weight = self.load_decay_factor ** i
            weighted_load += load * weight
            total_weight += weight
        
        if total_weight > 0:
            normalized_load = (weighted_load / total_weight) * 10  # Scale to 0-100
            return min(normalized_load, 100.0)
        
        return 0.0
    
    def _map_intensity_to_score(self, intensity: str) -> float:
        """Map intensity string to numerical score."""
        intensity_map = {
            'low': 3.0,
            'light': 4.0,
            'moderate': 6.0,
            'vigorous': 8.0,
            'high': 9.0,
            'maximum': 10.0
        }
        return intensity_map.get(intensity.lower(), 5.0)
    
    def _assess_overtraining_risk(self, user_data: Dict[str, Any], training_load: float) -> str:
        """
        Assess overtraining risk based on multiple indicators.
        
        Args:
            user_data: User profile and recent data
            training_load: Current training load score
            
        Returns:
            Risk level: "low", "medium", or "high"
        """
        risk_factors = []
        
        # Training load risk
        if training_load > self.overtraining_threshold:
            risk_factors.append("high_training_load")
        
        # Check for rapid load increases
        if len(self.training_load_history) >= 2:
            recent_increase = (training_load - self.training_load_history[-1]) / self.training_load_history[-1]
            if recent_increase > self.deload_threshold:
                risk_factors.append("rapid_load_increase")
        
        # Subjective wellness indicators
        wellness_scores = user_data.get('wellness_scores', {})
        fatigue_score = wellness_scores.get('fatigue', 0)
        if fatigue_score > 7:
            risk_factors.append("high_fatigue")
        
        # Sleep quality indicators
        sleep_data = user_data.get('recent_data', {}).get('sleep', {})
        avg_sleep_hours = sleep_data.get('average_hours', 8)
        sleep_quality = sleep_data.get('quality_score', 8)
        
        if avg_sleep_hours < 6 or sleep_quality < 5:
            risk_factors.append("poor_sleep")
        
        # Heart rate variability (if available)
        hrv_data = user_data.get('hrv_data', {})
        if hrv_data:
            hrv_trend = hrv_data.get('trend', 'stable')
            if hrv_trend == 'declining':
                risk_factors.append("declining_hrv")
        
        # Determine overall risk
        if len(risk_factors) >= 3:
            return "high"
        elif len(risk_factors) >= 1:
            return "medium"
        else:
            return "low"
    
    def _format_recovery_signals(self, user_data: Dict[str, Any], shared_state: Optional[Dict[str, Any]]) -> str:
        """Format recovery signals for prompt context."""
        
        signals = []
        
        # Sleep signals
        sleep_data = user_data.get('recent_data', {}).get('sleep', {})
        if sleep_data:
            avg_hours = sleep_data.get('average_hours', 0)
            quality = sleep_data.get('quality_score', 0)
            signals.append(f"Sleep: {avg_hours}h average, quality {quality}/10")
        
        # Subjective wellness
        wellness = user_data.get('wellness_scores', {})
        if wellness:
            fatigue = wellness.get('fatigue', 0)
            motivation = wellness.get('motivation', 0)
            signals.append(f"Subjective: fatigue {fatigue}/10, motivation {motivation}/10")
        
        # Recovery constraints from other agents
        if shared_state:
            sleep_constraints = shared_state.get('agent_proposals', {}).get('SleepAgent', {})
            if sleep_constraints:
                recovery_status = sleep_constraints.get('recovery_status', 'unknown')
                signals.append(f"Sleep Agent status: {recovery_status}")
        
        return "\n".join(signals) if signals else "No recovery signals available"
    
    def _initialize_equipment_database(self) -> Dict[str, List[str]]:
        """Initialize equipment database with exercise categories."""
        return {
            'bodyweight': ['push_ups', 'pull_ups', 'squats', 'lunges', 'planks', 'burpees'],
            'dumbbells': ['dumbbell_press', 'dumbbell_rows', 'dumbbell_squats', 'dumbbell_curls'],
            'barbell': ['deadlifts', 'squats', 'bench_press', 'rows', 'overhead_press'],
            'resistance_bands': ['band_pulls', 'band_squats', 'band_presses', 'band_rows'],
            'kettlebells': ['kettlebell_swings', 'goblet_squats', 'turkish_getups'],
            'cardio_machine': ['treadmill', 'elliptical', 'stationary_bike', 'rowing_machine'],
            'gym_access': ['cable_machine', 'lat_pulldown', 'leg_press', 'smith_machine']
        }
    
    def _initialize_exercise_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize exercise database with alternatives and progressions."""
        return {
            'push_ups': {
                'muscle_groups': ['chest', 'triceps', 'shoulders'],
                'equipment': 'bodyweight',
                'alternatives': ['incline_push_ups', 'knee_push_ups', 'wall_push_ups'],
                'progressions': ['diamond_push_ups', 'one_arm_push_ups', 'archer_push_ups']
            },
            'squats': {
                'muscle_groups': ['quadriceps', 'glutes', 'hamstrings'],
                'equipment': 'bodyweight',
                'alternatives': ['chair_squats', 'wall_sits', 'lunges'],
                'progressions': ['jump_squats', 'pistol_squats', 'bulgarian_split_squats']
            },
            'deadlifts': {
                'muscle_groups': ['hamstrings', 'glutes', 'back'],
                'equipment': 'barbell',
                'alternatives': ['romanian_deadlifts', 'single_leg_deadlifts', 'good_mornings'],
                'progressions': ['sumo_deadlifts', 'deficit_deadlifts', 'trap_bar_deadlifts']
            }
            # Additional exercises would be added here
        }
    
    def process_workout_feedback(self, feedback: Dict[str, Any]) -> None:
        """
        Process user feedback on workout performance.
        
        Args:
            feedback: User feedback on completed workout
        """
        # Update training load history
        workout_load = self._calculate_workout_load(feedback)
        self.training_load_history.append(workout_load)
        
        # Keep only recent history (last 30 workouts)
        if len(self.training_load_history) > 30:
            self.training_load_history = self.training_load_history[-30:]
        
        # Update overtraining indicators
        self._update_overtraining_indicators(feedback)
        
        # Store feedback in memory
        self.memory.store_episodic_memory(
            self.session_id or "feedback_session",
            {
                'feedback_type': 'workout_performance',
                'feedback_data': feedback,
                'training_load': workout_load,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def _calculate_workout_load(self, feedback: Dict[str, Any]) -> float:
        """Calculate training load for a specific workout."""
        duration = feedback.get('duration_minutes', 0)
        perceived_exertion = feedback.get('perceived_exertion', 5)  # 1-10 scale
        completion_rate = feedback.get('completion_rate', 1.0)  # 0-1 scale
        
        # Load = duration * intensity * completion
        load = (duration / 60) * perceived_exertion * completion_rate
        return load
    
    def _update_overtraining_indicators(self, feedback: Dict[str, Any]) -> None:
        """Update overtraining indicators based on feedback."""
        
        # Track fatigue trends
        fatigue_score = feedback.get('fatigue_level', 5)
        if 'fatigue_history' not in self.overtraining_indicators:
            self.overtraining_indicators['fatigue_history'] = []
        
        self.overtraining_indicators['fatigue_history'].append({
            'score': fatigue_score,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.overtraining_indicators['fatigue_history']) > 14:
            self.overtraining_indicators['fatigue_history'] = \
                self.overtraining_indicators['fatigue_history'][-14:]
        
        # Track performance trends
        performance_rating = feedback.get('performance_rating', 5)  # 1-10 scale
        if 'performance_history' not in self.overtraining_indicators:
            self.overtraining_indicators['performance_history'] = []
        
        self.overtraining_indicators['performance_history'].append({
            'rating': performance_rating,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.overtraining_indicators['performance_history']) > 14:
            self.overtraining_indicators['performance_history'] = \
                self.overtraining_indicators['performance_history'][-14:]
    
    def get_training_recommendations(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get training recommendations based on current status.
        
        Args:
            user_data: Current user data and constraints
            
        Returns:
            Training recommendations dictionary
        """
        current_load = self._calculate_training_load(user_data.get('fitness_history', {}))
        overtraining_risk = self._assess_overtraining_risk(user_data, current_load)
        
        recommendations = {
            'current_training_load': current_load,
            'overtraining_risk': overtraining_risk,
            'recommendations': []
        }
        
        # Generate specific recommendations
        if overtraining_risk == "high":
            recommendations['recommendations'].extend([
                "Implement immediate deload week (reduce volume by 50%)",
                "Focus on mobility and light recovery activities",
                "Prioritize sleep and stress management",
                "Consider taking 2-3 complete rest days"
            ])
        elif overtraining_risk == "medium":
            recommendations['recommendations'].extend([
                "Reduce training intensity by 20-30% this week",
                "Add extra rest day between intense sessions",
                "Monitor fatigue levels closely",
                "Ensure adequate sleep (7-9 hours nightly)"
            ])
        else:
            recommendations['recommendations'].extend([
                "Continue current training progression",
                "Consider slight volume increase (5-10%) if feeling strong",
                "Maintain consistent sleep and recovery practices"
            ])
        
        # Equipment-specific recommendations
        available_equipment = user_data.get('constraints', {}).get('equipment', [])
        if not available_equipment or available_equipment == ['bodyweight']:
            recommendations['recommendations'].append(
                "Focus on bodyweight progressions and high-intensity intervals"
            )
        
        return recommendations
    
    def validate_workout_plan(self, workout_plan: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate workout plan against constraints.
        
        Args:
            workout_plan: Generated workout plan
            constraints: User constraints
            
        Returns:
            Validation results with any necessary corrections
        """
        validation_results = {
            'valid': True,
            'violations': [],
            'corrections': []
        }
        
        # Check time constraints
        time_available = constraints.get('time_available', {})
        for session in workout_plan.get('weekly_schedule', []):
            session_duration = session.get('duration_minutes', 0)
            max_duration = time_available.get('max_session_minutes', 120)
            
            if session_duration > max_duration:
                validation_results['valid'] = False
                validation_results['violations'].append(
                    f"Session duration {session_duration}min exceeds limit {max_duration}min"
                )
                validation_results['corrections'].append(
                    f"Reduce session to {max_duration}min by removing accessory exercises"
                )
        
        # Check equipment constraints
        available_equipment = constraints.get('equipment', [])
        required_equipment = workout_plan.get('equipment_needed', [])
        
        for equipment in required_equipment:
            if equipment not in available_equipment and equipment != 'bodyweight':
                validation_results['valid'] = False
                validation_results['violations'].append(
                    f"Required equipment '{equipment}' not available"
                )
                validation_results['corrections'].append(
                    f"Replace {equipment} exercises with bodyweight alternatives"
                )
        
        return validation_results


def create_fitness_agent(confidence_threshold: float = 0.7) -> FitnessAgent:
    """
    Factory function to create a FitnessAgent instance.
    
    Args:
        confidence_threshold: Minimum confidence for proposals
        
    Returns:
        Configured FitnessAgent instance
    """
    return FitnessAgent(confidence_threshold=confidence_threshold)