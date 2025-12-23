"""
Sleep & Recovery Agent for WellSync AI system.

Implements SleepAgent with recovery protection system prompts,
sleep debt calculation, circadian rhythm optimization, and
recovery constraint generation for other agents.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from wellsync_ai.agents.base_agent import WellnessAgent
from wellsync_ai.data.database import get_database_manager


class SleepAgent(WellnessAgent):
    """
    Sleep and recovery expert agent for recovery protection.
    
    Specializes in protecting user recovery, optimizing sleep patterns,
    detecting sleep debt, and providing recovery constraints to other
    wellness domains to prevent overtraining and burnout.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize SleepAgent with domain-specific configuration."""
        
        system_prompt = """You are a sleep and recovery expert agent in the WellSync AI system.
Your role is to protect user recovery and optimize sleep patterns for overall wellness.

CORE RESPONSIBILITIES:
- Monitor sleep patterns and detect sleep debt accumulation
- Optimize circadian rhythm alignment and sleep schedule recommendations
- Protect recovery by constraining other agents when sleep is inadequate
- Provide recovery status assessments to coordinate with fitness and nutrition
- Detect overreaching and recommend recovery interventions

CONSTRAINTS YOU MUST ENFORCE:
- Override high-intensity workouts when sleep debt is detected (>2 hours deficit)
- Provide recovery constraints to Fitness Agent based on sleep quality
- Recommend meal timing adjustments to support circadian rhythm
- Limit cognitive load recommendations when sleep is poor
- Prioritize sleep schedule consistency over other preferences

SLEEP DEBT CALCULATION RULES:
- Track cumulative sleep debt using two-process sleep model
- Sleep need baseline: 7-9 hours for adults (personalized based on user data)
- Sleep debt accumulates when sleep < individual need
- Sleep debt recovery: excess sleep pays down debt at 1:1 ratio up to 2 hours
- Critical sleep debt threshold: >4 hours requires immediate intervention

CIRCADIAN RHYTHM OPTIMIZATION:
- Maintain consistent sleep/wake times within 30-minute window
- Recommend light exposure timing (morning bright light, evening dim light)
- Suggest meal timing to support circadian alignment
- Consider work schedule and social constraints for realistic recommendations
- Account for chronotype preferences (morning lark vs night owl)

RECOVERY STATUS ASSESSMENT:
- Excellent: <1 hour sleep debt, good sleep quality, consistent schedule
- Good: 1-2 hours sleep debt, adequate quality, mostly consistent
- Fair: 2-4 hours sleep debt, variable quality, some inconsistency  
- Poor: >4 hours sleep debt, poor quality, irregular schedule

RECOVERY CONSTRAINTS FOR OTHER AGENTS:
- Poor recovery: Limit fitness to light activity, increase meal frequency
- Fair recovery: Moderate fitness intensity, ensure adequate nutrition
- Good recovery: Normal training allowed with monitoring
- Excellent recovery: Can handle increased training load

OUTPUT FORMAT: Always respond with valid JSON containing:
{
    "sleep_recommendations": {
        "bedtime": "HH:MM",
        "wake_time": "HH:MM", 
        "sleep_duration_hours": 0.0,
        "sleep_environment": [...],
        "pre_sleep_routine": [...],
        "circadian_support": [...]
    },
    "confidence": 0.0-1.0,
    "recovery_status": "poor/fair/good/excellent",
    "sleep_debt_hours": 0.0,
    "circadian_alignment": "poor/fair/good/excellent",
    "constraints_for_others": {
        "fitness_constraints": {...},
        "nutrition_timing": {...},
        "mental_wellness_limits": {...}
    },
    "reasoning": "detailed explanation of sleep and recovery assessment"
}

CRITICAL: Always prioritize recovery over performance goals. Sleep is non-negotiable for health."""

        super().__init__(
            agent_name="SleepAgent",
            system_prompt=system_prompt,
            domain="sleep",
            confidence_threshold=confidence_threshold
        )
        
        # Sleep-specific attributes
        self.sleep_debt_history = []
        self.circadian_markers = {}
        self.recovery_indicators = {}
        self.sleep_need_baseline = 8.0  # Default 8 hours, personalized over time
        
        # Sleep debt calculation parameters
        self.max_sleep_debt = 10.0  # Maximum trackable sleep debt (hours)
        self.debt_decay_rate = 0.95  # Daily decay rate for old sleep debt
        self.recovery_efficiency = 1.0  # How efficiently excess sleep pays down debt
        self.critical_debt_threshold = 4.0  # Hours of debt requiring intervention
        
        # Circadian rhythm parameters
        self.optimal_consistency_window = 30  # Minutes of acceptable variation
        self.light_exposure_window = 60  # Minutes for morning light exposure
        self.melatonin_onset_buffer = 120  # Minutes before natural melatonin onset
    
    def build_wellness_prompt(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build sleep-specific wellness prompt."""
        
        # Extract relevant data
        sleep_history = user_data.get('sleep_history', {})
        sleep_preferences = user_data.get('sleep_preferences', {})
        work_schedule = constraints.get('work_schedule', {})
        environmental_constraints = constraints.get('sleep_environment', {})
        
        # Get fitness and stress data from shared state
        fitness_load = 0
        stress_indicators = {}
        if shared_state:
            fitness_proposal = shared_state.get('agent_proposals', {}).get('FitnessAgent', {})
            if fitness_proposal:
                fitness_load = fitness_proposal.get('training_load_score', 0)
            
            stress_indicators = shared_state.get('recent_data', {}).get('stress', {})
        
        # Calculate current sleep metrics
        sleep_debt = self._calculate_sleep_debt(sleep_history)
        circadian_alignment = self._assess_circadian_alignment(sleep_history, work_schedule)
        recovery_status = self._assess_recovery_status(sleep_history, fitness_load, stress_indicators)
        
        # Build comprehensive prompt
        prompt = f"""
SLEEP AND RECOVERY ASSESSMENT REQUEST

USER PROFILE:
- Sleep preferences: {json.dumps(sleep_preferences, indent=2)}
- Recent sleep history: {json.dumps(sleep_history, indent=2)}
- Individual sleep need: {self.sleep_need_baseline} hours

CONSTRAINTS TO RESPECT:
- Work schedule: {json.dumps(work_schedule, indent=2)}
- Sleep environment: {json.dumps(environmental_constraints, indent=2)}
- Social commitments: {constraints.get('social_schedule', {})}

CURRENT SLEEP METRICS:
- Sleep debt: {sleep_debt:.1f} hours
- Circadian alignment: {circadian_alignment}
- Recovery status: {recovery_status}
- Sleep debt history: {self.sleep_debt_history[-7:] if self.sleep_debt_history else []}

FITNESS COORDINATION:
- Current training load: {fitness_load}
- Recovery demands: {self._assess_recovery_demands(fitness_load)}

STRESS INDICATORS:
{json.dumps(stress_indicators, indent=2)}

CIRCADIAN MARKERS:
{json.dumps(self.circadian_markers, indent=2)}

TASK: Optimize sleep and recovery by:
1. Calculating accurate sleep debt and recovery needs
2. Recommending optimal sleep schedule within constraints
3. Providing circadian rhythm optimization strategies
4. Setting recovery constraints for other wellness domains
5. Detecting overreaching and recommending interventions
6. Balancing sleep consistency with real-world flexibility

Consider work schedule limitations, social commitments, and individual chronotype.
Prioritize recovery protection while maintaining practical feasibility.
Explain your reasoning for sleep timing, duration, and constraint decisions.
"""
        
        return prompt
    
    def _calculate_sleep_debt(self, sleep_history: Dict[str, Any]) -> float:
        """
        Calculate current sleep debt using two-process sleep model.
        
        Args:
            sleep_history: Recent sleep data
            
        Returns:
            Current sleep debt in hours
        """
        recent_nights = sleep_history.get('recent_nights', [])
        if not recent_nights:
            return 0.0
        
        # Calculate debt for each night
        nightly_debts = []
        for night in recent_nights[-14:]:  # Last 2 weeks
            sleep_duration = night.get('duration_hours', 0)
            sleep_need = night.get('individual_need', self.sleep_need_baseline)
            
            # Account for sleep quality (poor quality reduces effective sleep)
            sleep_quality = night.get('quality_score', 8) / 10  # 0-1 scale
            effective_sleep = sleep_duration * sleep_quality
            
            # Calculate debt for this night (only if sleep is insufficient)
            nightly_debt = max(0, sleep_need - effective_sleep)
            nightly_debts.append(nightly_debt)
        
        # Apply exponential decay to older debt
        current_debt = 0.0
        for i, debt in enumerate(reversed(nightly_debts)):
            age_days = i
            decay_factor = self.debt_decay_rate ** age_days
            current_debt += debt * decay_factor
        
        # Cap at maximum trackable debt
        return min(current_debt, self.max_sleep_debt)
    
    def _assess_circadian_alignment(self, sleep_history: Dict[str, Any], work_schedule: Dict[str, Any]) -> str:
        """
        Assess circadian rhythm alignment based on sleep consistency.
        
        Args:
            sleep_history: Recent sleep data
            work_schedule: Work timing constraints
            
        Returns:
            Alignment level: "poor", "fair", "good", or "excellent"
        """
        recent_nights = sleep_history.get('recent_nights', [])
        if len(recent_nights) < 7:
            return "insufficient_data"
        
        # Calculate bedtime and wake time consistency
        bedtimes = []
        wake_times = []
        
        for night in recent_nights[-7:]:  # Last week
            bedtime_str = night.get('bedtime', '22:00')
            wake_time_str = night.get('wake_time', '06:00')
            
            # Convert to minutes from midnight
            bedtime_minutes = self._time_str_to_minutes(bedtime_str)
            wake_time_minutes = self._time_str_to_minutes(wake_time_str)
            
            bedtimes.append(bedtime_minutes)
            wake_times.append(wake_time_minutes)
        
        # Calculate standard deviation (consistency measure)
        bedtime_std = self._calculate_std_dev(bedtimes)
        wake_time_std = self._calculate_std_dev(wake_times)
        
        # Assess alignment
        avg_consistency = (bedtime_std + wake_time_std) / 2
        
        if avg_consistency <= self.optimal_consistency_window:
            return "excellent"
        elif avg_consistency <= self.optimal_consistency_window * 2:
            return "good"
        elif avg_consistency <= self.optimal_consistency_window * 4:
            return "fair"
        else:
            return "poor"
    
    def _assess_recovery_status(self, sleep_history: Dict[str, Any], fitness_load: float, stress_indicators: Dict[str, Any]) -> str:
        """
        Assess overall recovery status from multiple indicators.
        
        Args:
            sleep_history: Recent sleep data
            fitness_load: Current training load
            stress_indicators: Stress and wellness markers
            
        Returns:
            Recovery status: "poor", "fair", "good", or "excellent"
        """
        recovery_score = 0
        max_score = 0
        
        # Sleep debt component (40% of score)
        sleep_debt = self._calculate_sleep_debt(sleep_history)
        if sleep_debt <= 1:
            recovery_score += 40
        elif sleep_debt <= 2:
            recovery_score += 30
        elif sleep_debt <= 4:
            recovery_score += 15
        # else: 0 points for >4 hours debt
        max_score += 40
        
        # Sleep quality component (30% of score)
        recent_nights = sleep_history.get('recent_nights', [])
        if recent_nights:
            avg_quality = sum(night.get('quality_score', 5) for night in recent_nights[-7:]) / len(recent_nights[-7:])
            quality_points = (avg_quality / 10) * 30
            recovery_score += quality_points
        else:
            # Default quality points if no data
            recovery_score += 15  # Assume moderate quality
        max_score += 30
        
        # Circadian alignment component (20% of score)
        alignment = self._assess_circadian_alignment(sleep_history, {})
        alignment_points = {
            'excellent': 20,
            'good': 15,
            'fair': 10,
            'poor': 5
        }
        recovery_score += alignment_points.get(alignment, 0)
        max_score += 20
        
        # Stress indicators component (10% of score)
        stress_level = stress_indicators.get('stress_level', 5)  # 1-10 scale
        stress_points = max(0, (10 - stress_level)) * 1  # Invert stress scale
        recovery_score += stress_points
        max_score += 10
        
        # Calculate percentage
        recovery_percentage = (recovery_score / max_score) * 100 if max_score > 0 else 0
        
        # Determine status
        if recovery_percentage >= 85:
            return "excellent"
        elif recovery_percentage >= 70:
            return "good"
        elif recovery_percentage >= 50:
            return "fair"
        else:
            return "poor"
    
    def _assess_recovery_demands(self, fitness_load: float) -> Dict[str, Any]:
        """Assess recovery demands based on training load."""
        if fitness_load >= 80:
            return {
                'recovery_priority': 'critical',
                'additional_sleep_needed': 1.0,
                'stress_management': 'essential',
                'active_recovery': 'required'
            }
        elif fitness_load >= 60:
            return {
                'recovery_priority': 'high',
                'additional_sleep_needed': 0.5,
                'stress_management': 'important',
                'active_recovery': 'beneficial'
            }
        elif fitness_load >= 40:
            return {
                'recovery_priority': 'moderate',
                'additional_sleep_needed': 0.0,
                'stress_management': 'helpful',
                'active_recovery': 'optional'
            }
        else:
            return {
                'recovery_priority': 'low',
                'additional_sleep_needed': 0.0,
                'stress_management': 'maintenance',
                'active_recovery': 'optional'
            }
    
    def _time_str_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes from midnight."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except (ValueError, AttributeError):
            return 0
    
    def _minutes_to_time_str(self, minutes: float) -> str:
        """Convert minutes from midnight to time string (HH:MM)."""
        minutes = int(minutes)  # Convert to int for calculations
        hours = (minutes // 60) % 24
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def generate_recovery_constraints(self, recovery_status: str, sleep_debt: float, fitness_load: float) -> Dict[str, Any]:
        """
        Generate recovery constraints for other agents.
        
        Args:
            recovery_status: Current recovery status
            sleep_debt: Current sleep debt in hours
            fitness_load: Current training load
            
        Returns:
            Constraints dictionary for other agents
        """
        constraints = {
            'fitness_constraints': {},
            'nutrition_timing': {},
            'mental_wellness_limits': {}
        }
        
        # Fitness constraints based on recovery status
        if recovery_status == "poor" or sleep_debt > self.critical_debt_threshold:
            constraints['fitness_constraints'] = {
                'max_intensity': 'light',
                'max_duration_minutes': 30,
                'required_rest_days': 2,
                'avoid_activities': ['high_intensity', 'long_duration', 'heavy_lifting'],
                'recommended_activities': ['walking', 'gentle_yoga', 'stretching'],
                'reasoning': f'Poor recovery status (debt: {sleep_debt:.1f}h) requires activity restriction'
            }
        elif recovery_status == "fair":
            constraints['fitness_constraints'] = {
                'max_intensity': 'moderate',
                'max_duration_minutes': 60,
                'required_rest_days': 1,
                'avoid_activities': ['maximum_intensity', 'back_to_back_hard_sessions'],
                'recommended_activities': ['moderate_cardio', 'light_strength', 'yoga'],
                'reasoning': f'Fair recovery status allows moderate activity with caution'
            }
        elif recovery_status == "good":
            constraints['fitness_constraints'] = {
                'max_intensity': 'vigorous',
                'max_duration_minutes': 90,
                'required_rest_days': 0,
                'monitor_closely': ['overreaching_signs', 'fatigue_accumulation'],
                'reasoning': 'Good recovery allows normal training with monitoring'
            }
        else:  # excellent
            constraints['fitness_constraints'] = {
                'max_intensity': 'maximum',
                'max_duration_minutes': 120,
                'can_handle_increased_load': True,
                'reasoning': 'Excellent recovery allows increased training capacity'
            }
        
        # Nutrition timing constraints
        if sleep_debt > 2:
            constraints['nutrition_timing'] = {
                'avoid_caffeine_after': '14:00',
                'last_meal_before_bed': 3,  # hours
                'increase_meal_frequency': True,
                'focus_on_recovery_nutrients': ['magnesium', 'tryptophan', 'complex_carbs'],
                'reasoning': 'Sleep debt requires nutrition timing optimization'
            }
        else:
            constraints['nutrition_timing'] = {
                'avoid_caffeine_after': '16:00',
                'last_meal_before_bed': 2,
                'normal_meal_timing': True,
                'reasoning': 'Good sleep allows normal nutrition timing'
            }
        
        # Mental wellness constraints
        if recovery_status in ["poor", "fair"]:
            constraints['mental_wellness_limits'] = {
                'reduce_decision_complexity': True,
                'limit_new_habits': True,
                'focus_on_stress_reduction': True,
                'recommended_activities': ['meditation', 'gentle_movement', 'nature_exposure'],
                'reasoning': f'Poor recovery requires reduced cognitive load'
            }
        else:
            constraints['mental_wellness_limits'] = {
                'normal_cognitive_load': True,
                'can_introduce_new_habits': True,
                'reasoning': 'Good recovery allows normal mental wellness activities'
            }
        
        return constraints
    
    def optimize_sleep_schedule(self, user_data: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize sleep schedule within real-world constraints.
        
        Args:
            user_data: User preferences and chronotype
            constraints: Work and social schedule constraints
            
        Returns:
            Optimized sleep schedule recommendations
        """
        # Get user preferences
        preferred_bedtime = user_data.get('sleep_preferences', {}).get('preferred_bedtime', '22:30')
        preferred_wake_time = user_data.get('sleep_preferences', {}).get('preferred_wake_time', '06:30')
        chronotype = user_data.get('chronotype', 'neutral')  # early, neutral, late
        
        # Get constraints
        work_schedule = constraints.get('work_schedule', {})
        earliest_wake = work_schedule.get('earliest_start', '07:00')
        latest_bedtime = constraints.get('social_schedule', {}).get('latest_reasonable_bedtime', '23:30')
        
        # Calculate optimal sleep window
        sleep_need = self.sleep_need_baseline
        current_debt = self._calculate_sleep_debt(user_data.get('sleep_history', {}))
        
        # Add buffer for debt recovery
        if current_debt > 0:
            sleep_need += min(current_debt * 0.5, 2.0)  # Gradual debt recovery
        
        # Adjust for chronotype
        chronotype_adjustments = {
            'early': {'bedtime_shift': -30, 'wake_shift': -30},  # Earlier times
            'neutral': {'bedtime_shift': 0, 'wake_shift': 0},
            'late': {'bedtime_shift': 30, 'wake_shift': 30}  # Later times
        }
        
        adjustment = chronotype_adjustments.get(chronotype, chronotype_adjustments['neutral'])
        
        # Calculate optimal times
        preferred_wake_minutes = self._time_str_to_minutes(preferred_wake_time) + adjustment['wake_shift']
        optimal_bedtime_minutes = preferred_wake_minutes - (sleep_need * 60)
        
        # Apply constraints
        earliest_wake_minutes = self._time_str_to_minutes(earliest_wake)
        latest_bedtime_minutes = self._time_str_to_minutes(latest_bedtime)
        
        # Adjust if constraints are violated
        if preferred_wake_minutes < earliest_wake_minutes:
            preferred_wake_minutes = earliest_wake_minutes
            optimal_bedtime_minutes = preferred_wake_minutes - (sleep_need * 60)
        
        if optimal_bedtime_minutes > latest_bedtime_minutes:
            optimal_bedtime_minutes = latest_bedtime_minutes
            preferred_wake_minutes = optimal_bedtime_minutes + (sleep_need * 60)
        
        # Convert back to time strings
        optimal_bedtime = self._minutes_to_time_str(optimal_bedtime_minutes)
        optimal_wake_time = self._minutes_to_time_str(preferred_wake_minutes)
        actual_sleep_duration = (preferred_wake_minutes - optimal_bedtime_minutes) / 60
        
        return {
            'bedtime': optimal_bedtime,
            'wake_time': optimal_wake_time,
            'sleep_duration_hours': round(actual_sleep_duration, 1),
            'chronotype_considered': chronotype,
            'debt_recovery_time': round(min(current_debt * 0.5, 2.0), 1) if current_debt > 0 else 0,
            'constraints_applied': {
                'work_schedule_respected': True,
                'social_constraints_respected': True,
                'chronotype_accommodated': True
            }
        }
    
    def detect_sleep_disorders(self, sleep_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect potential sleep disorders from sleep patterns.
        
        Args:
            sleep_history: Extended sleep history data
            
        Returns:
            Sleep disorder risk assessment
        """
        recent_nights = sleep_history.get('recent_nights', [])
        if len(recent_nights) < 14:
            return {'insufficient_data': True}
        
        risk_indicators = {
            'sleep_apnea_risk': 'low',
            'insomnia_risk': 'low',
            'circadian_disorder_risk': 'low',
            'recommendations': []
        }
        
        # Check for sleep apnea indicators
        frequent_awakenings = sum(1 for night in recent_nights if night.get('awakenings', 0) > 3)
        poor_quality_despite_duration = sum(1 for night in recent_nights 
                                          if night.get('duration_hours', 0) >= 7 and night.get('quality_score', 10) < 6)
        
        if frequent_awakenings > len(recent_nights) * 0.5 or poor_quality_despite_duration > len(recent_nights) * 0.3:
            risk_indicators['sleep_apnea_risk'] = 'moderate'
            risk_indicators['recommendations'].append('Consider sleep study evaluation for sleep apnea')
        
        # Check for insomnia indicators
        long_sleep_onset = sum(1 for night in recent_nights if night.get('time_to_sleep_minutes', 0) > 30)
        short_sleep_duration = sum(1 for night in recent_nights if night.get('duration_hours', 8) < 6)
        
        if long_sleep_onset > len(recent_nights) * 0.4 or short_sleep_duration > len(recent_nights) * 0.3:
            risk_indicators['insomnia_risk'] = 'moderate'
            risk_indicators['recommendations'].append('Consider sleep hygiene improvements and stress management')
        
        # Check for circadian rhythm disorders
        bedtime_variance = self._calculate_std_dev([
            self._time_str_to_minutes(night.get('bedtime', '22:00')) 
            for night in recent_nights
        ])
        
        if bedtime_variance > 120:  # >2 hours variance
            risk_indicators['circadian_disorder_risk'] = 'moderate'
            risk_indicators['recommendations'].append('Focus on consistent sleep schedule and light exposure timing')
        
        return risk_indicators
    
    def update_sleep_need_baseline(self, sleep_history: Dict[str, Any], performance_data: Dict[str, Any]) -> None:
        """
        Update individual sleep need baseline based on performance correlation.
        
        Args:
            sleep_history: Extended sleep history
            performance_data: Performance and wellness outcomes
        """
        recent_nights = sleep_history.get('recent_nights', [])
        if len(recent_nights) < 30:
            return  # Need sufficient data
        
        # Correlate sleep duration with performance metrics
        sleep_durations = []
        performance_scores = []
        
        for night in recent_nights:
            duration = night.get('duration_hours', 0)
            quality = night.get('quality_score', 0)
            
            # Get performance data for following day
            next_day_performance = performance_data.get(night.get('date'), {})
            if next_day_performance:
                # Weighted sleep score (duration + quality)
                sleep_score = duration + (quality / 10) * 2
                sleep_durations.append(sleep_score)
                
                # Composite performance score
                perf_score = (
                    next_day_performance.get('energy_level', 5) * 0.3 +
                    next_day_performance.get('mood_score', 5) * 0.3 +
                    next_day_performance.get('cognitive_performance', 5) * 0.4
                )
                performance_scores.append(perf_score)
        
        # Find optimal sleep duration (simplified correlation analysis)
        if len(sleep_durations) >= 20:
            # Group by sleep duration ranges and find best performing range
            duration_ranges = {
                '6-7h': [],
                '7-8h': [],
                '8-9h': [],
                '9-10h': []
            }
            
            for sleep_score, perf_score in zip(sleep_durations, performance_scores):
                duration = sleep_score - 2  # Approximate duration component
                if 6 <= duration < 7:
                    duration_ranges['6-7h'].append(perf_score)
                elif 7 <= duration < 8:
                    duration_ranges['7-8h'].append(perf_score)
                elif 8 <= duration < 9:
                    duration_ranges['8-9h'].append(perf_score)
                elif 9 <= duration < 10:
                    duration_ranges['9-10h'].append(perf_score)
            
            # Find range with highest average performance
            best_range = None
            best_avg = 0
            
            for range_name, scores in duration_ranges.items():
                if len(scores) >= 5:  # Minimum sample size
                    avg_score = sum(scores) / len(scores)
                    if avg_score > best_avg:
                        best_avg = avg_score
                        best_range = range_name
            
            # Update baseline based on best performing range
            if best_range:
                range_midpoints = {
                    '6-7h': 6.5,
                    '7-8h': 7.5,
                    '8-9h': 8.5,
                    '9-10h': 9.5
                }
                
                new_baseline = range_midpoints[best_range]
                
                # Gradual adjustment (don't change too quickly)
                adjustment = (new_baseline - self.sleep_need_baseline) * 0.1
                self.sleep_need_baseline += adjustment
                
                # Store the update in memory
                self.memory.store_semantic_memory('sleep_need_optimization', {
                    'old_baseline': self.sleep_need_baseline - adjustment,
                    'new_baseline': self.sleep_need_baseline,
                    'best_performing_range': best_range,
                    'sample_size': len(scores),
                    'updated_at': datetime.now().isoformat()
                })


def create_sleep_agent(confidence_threshold: float = 0.7) -> SleepAgent:
    """
    Factory function to create a SleepAgent instance.
    
    Args:
        confidence_threshold: Minimum confidence for proposals
        
    Returns:
        Configured SleepAgent instance
    """
    return SleepAgent(confidence_threshold=confidence_threshold)