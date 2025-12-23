"""
Mental Wellness Agent for WellSync AI system.

Implements MentalWellnessAgent with motivation management prompts,
adherence pattern monitoring, cognitive load assessment, and
plan complexity adjustment recommendations.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from wellsync_ai.agents.base_agent import WellnessAgent
from wellsync_ai.data.database import get_database_manager


class MentalWellnessAgent(WellnessAgent):
    """
    Mental wellness expert agent for motivation maintenance and cognitive load management.
    
    Specializes in monitoring adherence patterns, assessing motivation levels,
    detecting decision fatigue, and adjusting plan complexity during high-stress
    periods to maintain long-term engagement and sustainable wellness habits.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize MentalWellnessAgent with domain-specific configuration."""
        
        system_prompt = """You are a mental wellness expert agent in the WellSync AI system.
Your role is to maintain user motivation and manage cognitive load for sustainable wellness habits.

CORE RESPONSIBILITIES:
- Monitor adherence patterns to assess motivation and engagement levels
- Detect decision fatigue and recommendation overload in wellness plans
- Suggest plan simplification during high-stress periods
- Provide engagement feedback and motivation strategies to other agents
- Adjust cognitive load based on user's mental capacity and stress levels

MOTIVATION ASSESSMENT PRINCIPLES:
- Track adherence patterns across all wellness domains (fitness, nutrition, sleep)
- Identify motivation trends: increasing, stable, declining, or fluctuating
- Detect preference fatigue when users show declining engagement with repeated recommendations
- Monitor completion rates and quality of engagement with wellness activities
- Assess intrinsic vs extrinsic motivation factors

COGNITIVE LOAD MANAGEMENT:
- Evaluate plan complexity across all wellness domains
- Detect decision fatigue from too many simultaneous changes
- Recommend habit stacking vs. isolated habit formation
- Adjust recommendation frequency based on user's cognitive capacity
- Simplify plans during high-stress periods or life transitions

STRESS AND LIFE CONTEXT ASSESSMENT:
- Monitor stress indicators from user data and other agent feedback
- Detect life transitions, work pressure, or personal challenges
- Adjust wellness expectations during high-stress periods
- Recommend stress management techniques and coping strategies
- Prioritize mental health over performance goals when necessary

ADHERENCE PATTERN ANALYSIS:
- Track completion rates for different types of wellness activities
- Identify patterns: which activities are consistently followed vs. abandoned
- Detect seasonal, weekly, or daily patterns in motivation and adherence
- Analyze correlation between stress levels and wellness engagement
- Monitor recovery from motivation dips and engagement lapses

PLAN COMPLEXITY ADJUSTMENT RULES:
- High stress/low motivation: Reduce to 1-2 simple, familiar habits
- Moderate stress: Maintain current complexity, add stress management
- Low stress/high motivation: Can handle increased complexity and new challenges
- Decision fatigue detected: Simplify choices, use habit stacking
- Preference fatigue: Introduce variety and new approaches

OUTPUT FORMAT: Always respond with valid JSON containing:
{
    "wellness_recommendations": {
        "motivation_strategies": [...],
        "stress_management": [...],
        "habit_adjustments": [...],
        "engagement_techniques": [...]
    },
    "confidence": 0.0-1.0,
    "motivation_level": "low/medium/high",
    "stress_level": "low/medium/high",
    "cognitive_load_assessment": "low/medium/high/overload",
    "adherence_trend": "improving/stable/declining/fluctuating",
    "complexity_adjustments": {
        "fitness_simplification": {...},
        "nutrition_simplification": {...},
        "sleep_simplification": {...},
        "overall_plan_changes": [...]
    },
    "reasoning": "detailed explanation of mental wellness assessment and recommendations"
}

CRITICAL: Always prioritize mental health and sustainable motivation over short-term performance goals."""

        super().__init__(
            agent_name="MentalWellnessAgent",
            system_prompt=system_prompt,
            domain="mental_wellness",
            confidence_threshold=confidence_threshold
        )
        
        # Mental wellness specific attributes
        self.adherence_history = []
        self.motivation_indicators = {}
        self.stress_patterns = {}
        self.cognitive_load_metrics = {}
        
        # Motivation assessment parameters
        self.adherence_window_days = 14  # Days to analyze for adherence patterns
        self.motivation_decline_threshold = 0.7  # Below this ratio indicates declining motivation
        self.stress_threshold_high = 7  # Stress level (1-10) considered high
        self.decision_fatigue_threshold = 5  # Number of simultaneous changes that may cause fatigue
        
        # Cognitive load assessment parameters
        self.complexity_weights = {
            'new_habits': 3,  # New habits require more cognitive resources
            'existing_habits': 1,  # Existing habits require less
            'decisions_per_day': 2,  # Each decision point adds load
            'tracking_requirements': 1.5  # Tracking adds moderate load
        }
        
        # Preference fatigue detection
        self.preference_fatigue_window = 21  # Days to check for repeated patterns
        self.variety_threshold = 0.3  # Minimum variety ratio to avoid fatigue
    
    def build_wellness_prompt(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build mental wellness specific prompt."""
        
        # Extract relevant data
        wellness_history = user_data.get('wellness_history', {})
        stress_indicators = user_data.get('stress_indicators', {})
        life_context = user_data.get('life_context', {})
        mental_health_data = user_data.get('mental_health', {})
        
        # Get proposals from other agents to assess complexity
        agent_proposals = {}
        current_plan_complexity = {}
        if shared_state:
            agent_proposals = shared_state.get('agent_proposals', {})
            current_plan_complexity = self._assess_current_plan_complexity(agent_proposals)
        
        # Calculate motivation and adherence metrics
        adherence_analysis = self._analyze_adherence_patterns(wellness_history)
        motivation_assessment = self._assess_motivation_level(wellness_history, stress_indicators)
        cognitive_load = self._calculate_cognitive_load(agent_proposals, user_data)
        stress_analysis = self._analyze_stress_patterns(stress_indicators, life_context)
        
        # Build comprehensive prompt
        prompt = f"""
MENTAL WELLNESS AND MOTIVATION ASSESSMENT REQUEST

USER PROFILE:
- Current life context: {json.dumps(life_context, indent=2)}
- Mental health baseline: {json.dumps(mental_health_data, indent=2)}
- Stress indicators: {json.dumps(stress_indicators, indent=2)}

ADHERENCE ANALYSIS:
{json.dumps(adherence_analysis, indent=2)}

MOTIVATION ASSESSMENT:
{json.dumps(motivation_assessment, indent=2)}

COGNITIVE LOAD ANALYSIS:
{json.dumps(cognitive_load, indent=2)}

STRESS PATTERN ANALYSIS:
{json.dumps(stress_analysis, indent=2)}

CURRENT PLAN COMPLEXITY:
{json.dumps(current_plan_complexity, indent=2)}

OTHER AGENT PROPOSALS:
- Fitness Agent: {json.dumps(agent_proposals.get('FitnessAgent', {}), indent=2)}
- Nutrition Agent: {json.dumps(agent_proposals.get('NutritionAgent', {}), indent=2)}
- Sleep Agent: {json.dumps(agent_proposals.get('SleepAgent', {}), indent=2)}

CONSTRAINTS TO CONSIDER:
- Time availability: {constraints.get('time_available', {})}
- Life stressors: {constraints.get('current_stressors', [])}
- Support systems: {constraints.get('support_systems', {})}

TASK: Optimize mental wellness and motivation by:
1. Assessing current motivation level and adherence trends
2. Evaluating cognitive load from all wellness recommendations
3. Detecting decision fatigue, preference fatigue, or stress overload
4. Recommending plan complexity adjustments for sustainable engagement
5. Providing motivation strategies and stress management techniques
6. Suggesting engagement improvements for other wellness domains

Consider the user's current stress level, life context, and cognitive capacity.
Balance wellness goals with mental health and sustainable motivation.
Explain your reasoning for complexity adjustments and motivation strategies.
"""
        
        return prompt
    
    def _analyze_adherence_patterns(self, wellness_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze adherence patterns across wellness domains.
        
        Args:
            wellness_history: Historical wellness activity data
            
        Returns:
            Adherence analysis with trends and patterns
        """
        recent_activities = wellness_history.get('recent_activities', [])
        if not recent_activities:
            return {'insufficient_data': True}
        
        # Analyze adherence by domain
        domain_adherence = {
            'fitness': [],
            'nutrition': [],
            'sleep': [],
            'overall': []
        }
        
        # Calculate adherence rates for recent period
        for activity in recent_activities[-self.adherence_window_days:]:
            domain = activity.get('domain', 'unknown')
            completed = activity.get('completed', False)
            completion_quality = activity.get('completion_quality', 0.5)  # 0-1 scale
            
            # Weight completion by quality
            adherence_score = 1.0 if completed else 0.0
            if completed:
                adherence_score *= completion_quality
            
            if domain in domain_adherence:
                domain_adherence[domain].append(adherence_score)
            domain_adherence['overall'].append(adherence_score)
        
        # Calculate adherence rates and trends
        adherence_analysis = {}
        for domain, scores in domain_adherence.items():
            if scores:
                current_rate = sum(scores) / len(scores)
                
                # Calculate trend (recent vs. earlier)
                if len(scores) >= 7:
                    recent_rate = sum(scores[-7:]) / len(scores[-7:])
                    earlier_rate = sum(scores[:-7]) / len(scores[:-7]) if len(scores) > 7 else current_rate
                    trend = 'improving' if recent_rate > earlier_rate * 1.1 else \
                           'declining' if recent_rate < earlier_rate * 0.9 else 'stable'
                else:
                    trend = 'insufficient_data'
                
                adherence_analysis[domain] = {
                    'adherence_rate': round(current_rate, 2),
                    'trend': trend,
                    'sample_size': len(scores),
                    'consistency': self._calculate_consistency(scores)
                }
        
        # Identify patterns
        patterns = self._identify_adherence_patterns(recent_activities)
        
        return {
            'domain_adherence': adherence_analysis,
            'patterns': patterns,
            'overall_trend': adherence_analysis.get('overall', {}).get('trend', 'unknown'),
            'analysis_period_days': min(len(recent_activities), self.adherence_window_days)
        }
    
    def _assess_motivation_level(self, wellness_history: Dict[str, Any], stress_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess current motivation level from multiple indicators.
        
        Args:
            wellness_history: Historical wellness data
            stress_indicators: Current stress and mood data
            
        Returns:
            Motivation assessment with level and contributing factors
        """
        motivation_score = 0
        max_score = 0
        factors = {}
        
        # Adherence trend factor (30% of score)
        recent_activities = wellness_history.get('recent_activities', [])
        if recent_activities:
            recent_completion_rate = sum(1 for activity in recent_activities[-7:] 
                                       if activity.get('completed', False)) / len(recent_activities[-7:])
            adherence_points = recent_completion_rate * 30
            motivation_score += adherence_points
            factors['adherence_contribution'] = adherence_points
        max_score += 30
        
        # Engagement quality factor (25% of score)
        engagement_scores = [activity.get('engagement_score', 5) for activity in recent_activities[-7:]]
        if engagement_scores:
            avg_engagement = sum(engagement_scores) / len(engagement_scores)
            engagement_points = (avg_engagement / 10) * 25  # Normalize to 0-25
            motivation_score += engagement_points
            factors['engagement_contribution'] = engagement_points
        max_score += 25
        
        # Mood and energy factor (25% of score)
        mood_score = stress_indicators.get('mood_score', 5)  # 1-10 scale
        energy_level = stress_indicators.get('energy_level', 5)  # 1-10 scale
        mood_energy_avg = (mood_score + energy_level) / 2
        mood_points = (mood_energy_avg / 10) * 25
        motivation_score += mood_points
        factors['mood_energy_contribution'] = mood_points
        max_score += 25
        
        # Stress level factor (20% of score, inverted)
        stress_level = stress_indicators.get('stress_level', 5)  # 1-10 scale
        stress_points = ((10 - stress_level) / 10) * 20  # Invert stress scale
        motivation_score += stress_points
        factors['stress_contribution'] = stress_points
        max_score += 20
        
        # Calculate overall motivation level
        motivation_percentage = (motivation_score / max_score) * 100 if max_score > 0 else 50
        
        # Determine motivation level
        if motivation_percentage >= 75:
            level = 'high'
        elif motivation_percentage >= 50:
            level = 'medium'
        else:
            level = 'low'
        
        # Detect specific motivation issues
        issues = []
        if recent_completion_rate < 0.5:
            issues.append('low_adherence')
        if avg_engagement < 6:
            issues.append('low_engagement')
        if stress_level > self.stress_threshold_high:
            issues.append('high_stress')
        if mood_score < 4:
            issues.append('low_mood')
        
        return {
            'motivation_level': level,
            'motivation_score': round(motivation_percentage, 1),
            'contributing_factors': factors,
            'motivation_issues': issues,
            'trend_indicators': self._assess_motivation_trend(wellness_history)
        }
    
    def _calculate_cognitive_load(self, agent_proposals: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cognitive load from current wellness recommendations.
        
        Args:
            agent_proposals: Proposals from other agents
            user_data: User profile and preferences
            
        Returns:
            Cognitive load assessment
        """
        total_load = 0
        load_breakdown = {}
        
        # Analyze each agent's proposal complexity
        for agent_name, proposal in agent_proposals.items():
            agent_load = 0
            
            if agent_name == 'FitnessAgent':
                workout_plan = proposal.get('workout_plan', {})
                exercises_count = len(workout_plan.get('exercises', []))
                new_exercises = len([ex for ex in workout_plan.get('exercises', []) 
                                   if ex.get('is_new', False)])
                
                agent_load += exercises_count * self.complexity_weights['existing_habits']
                agent_load += new_exercises * self.complexity_weights['new_habits']
                
                if workout_plan.get('requires_tracking', False):
                    agent_load += self.complexity_weights['tracking_requirements']
            
            elif agent_name == 'NutritionAgent':
                meal_plan = proposal.get('meal_plan', {})
                daily_meals = meal_plan.get('daily_meals', [])
                new_recipes = len([meal for meal in daily_meals 
                                 if meal.get('is_new_recipe', False)])
                
                agent_load += len(daily_meals) * self.complexity_weights['existing_habits']
                agent_load += new_recipes * self.complexity_weights['new_habits']
                
                if meal_plan.get('requires_meal_prep', False):
                    agent_load += self.complexity_weights['tracking_requirements']
            
            elif agent_name == 'SleepAgent':
                sleep_recs = proposal.get('sleep_recommendations', {})
                schedule_changes = len([change for change in sleep_recs.get('schedule_changes', [])
                                      if change.get('is_new', False)])
                
                agent_load += schedule_changes * self.complexity_weights['new_habits']
                
                if sleep_recs.get('requires_tracking', False):
                    agent_load += self.complexity_weights['tracking_requirements']
            
            load_breakdown[agent_name] = agent_load
            total_load += agent_load
        
        # Assess user's cognitive capacity
        stress_level = user_data.get('stress_indicators', {}).get('stress_level', 5)
        life_changes = len(user_data.get('life_context', {}).get('recent_changes', []))
        
        # Adjust load based on user capacity
        capacity_multiplier = 1.0
        if stress_level > 7:
            capacity_multiplier = 0.5  # High stress reduces capacity
        elif stress_level > 5:
            capacity_multiplier = 0.75  # Moderate stress reduces capacity
        
        if life_changes > 2:
            capacity_multiplier *= 0.8  # Life changes reduce capacity
        
        effective_load = total_load / capacity_multiplier
        
        # Determine load level
        if effective_load > 15:
            load_level = 'overload'
        elif effective_load > 10:
            load_level = 'high'
        elif effective_load > 5:
            load_level = 'medium'
        else:
            load_level = 'low'
        
        return {
            'total_cognitive_load': round(total_load, 1),
            'effective_load': round(effective_load, 1),
            'load_level': load_level,
            'load_breakdown': load_breakdown,
            'capacity_factors': {
                'stress_level': stress_level,
                'life_changes': life_changes,
                'capacity_multiplier': capacity_multiplier
            },
            'overload_risk': effective_load > 12
        }
    
    def _analyze_stress_patterns(self, stress_indicators: Dict[str, Any], life_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze stress patterns and their impact on wellness engagement.
        
        Args:
            stress_indicators: Current stress measurements
            life_context: Life situation and changes
            
        Returns:
            Stress pattern analysis
        """
        current_stress = stress_indicators.get('stress_level', 5)
        stress_sources = stress_indicators.get('stress_sources', [])
        coping_resources = life_context.get('coping_resources', [])
        
        # Assess stress impact on wellness
        stress_impact = {
            'wellness_capacity_reduction': 0,
            'priority_adjustments_needed': [],
            'stress_management_urgency': 'low'
        }
        
        if current_stress >= 8:
            stress_impact.update({
                'wellness_capacity_reduction': 0.6,
                'priority_adjustments_needed': ['reduce_complexity', 'focus_on_basics', 'add_stress_management'],
                'stress_management_urgency': 'high'
            })
        elif current_stress >= 6:
            stress_impact.update({
                'wellness_capacity_reduction': 0.3,
                'priority_adjustments_needed': ['moderate_complexity', 'maintain_routines'],
                'stress_management_urgency': 'medium'
            })
        
        # Identify stress management needs
        stress_management_needs = []
        if 'work' in stress_sources:
            stress_management_needs.extend(['time_management', 'boundary_setting'])
        if 'relationships' in stress_sources:
            stress_management_needs.extend(['communication_skills', 'social_support'])
        if 'health' in stress_sources:
            stress_management_needs.extend(['medical_support', 'self_care_prioritization'])
        if 'finances' in stress_sources:
            stress_management_needs.extend(['budget_planning', 'resource_optimization'])
        
        return {
            'current_stress_level': current_stress,
            'stress_sources': stress_sources,
            'available_coping_resources': coping_resources,
            'stress_impact': stress_impact,
            'stress_management_needs': stress_management_needs,
            'resilience_factors': self._assess_resilience_factors(life_context, coping_resources)
        }
    
    def _assess_current_plan_complexity(self, agent_proposals: Dict[str, Any]) -> Dict[str, Any]:
        """Assess complexity of current wellness plan from all agents."""
        complexity_metrics = {
            'total_new_habits': 0,
            'total_decisions_per_day': 0,
            'total_tracking_requirements': 0,
            'simultaneous_changes': 0
        }
        
        for agent_name, proposal in agent_proposals.items():
            if agent_name == 'FitnessAgent':
                workout_plan = proposal.get('workout_plan', {})
                new_exercises = len([ex for ex in workout_plan.get('exercises', []) 
                                   if ex.get('is_new', False)])
                complexity_metrics['total_new_habits'] += new_exercises
                
                if workout_plan.get('requires_daily_decisions', False):
                    complexity_metrics['total_decisions_per_day'] += 1
                
                if new_exercises > 0:
                    complexity_metrics['simultaneous_changes'] += 1
            
            elif agent_name == 'NutritionAgent':
                meal_plan = proposal.get('meal_plan', {})
                new_recipes = len([meal for meal in meal_plan.get('daily_meals', []) 
                                 if meal.get('is_new_recipe', False)])
                complexity_metrics['total_new_habits'] += new_recipes
                
                if meal_plan.get('requires_daily_planning', False):
                    complexity_metrics['total_decisions_per_day'] += 1
                
                if new_recipes > 0:
                    complexity_metrics['simultaneous_changes'] += 1
            
            elif agent_name == 'SleepAgent':
                sleep_recs = proposal.get('sleep_recommendations', {})
                schedule_changes = len(sleep_recs.get('schedule_changes', []))
                complexity_metrics['total_new_habits'] += schedule_changes
                
                if schedule_changes > 0:
                    complexity_metrics['simultaneous_changes'] += 1
        
        return complexity_metrics
    
    def _calculate_consistency(self, scores: List[float]) -> float:
        """Calculate consistency score from adherence scores."""
        if len(scores) < 2:
            return 1.0
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_score = sum(scores) / len(scores)
        if mean_score == 0:
            return 0.0
        
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_score
        
        # Convert to consistency score (0-1, higher = more consistent)
        consistency = max(0, 1 - cv)
        return round(consistency, 2)
    
    def _identify_adherence_patterns(self, recent_activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify patterns in adherence behavior."""
        patterns = {
            'weekly_patterns': {},
            'time_of_day_patterns': {},
            'activity_type_patterns': {},
            'streak_analysis': {}
        }
        
        # Weekly patterns
        day_adherence = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
        
        for activity in recent_activities:
            day_of_week = activity.get('day_of_week')
            completed = activity.get('completed', False)
            
            if day_of_week in day_adherence:
                day_adherence[day_of_week].append(1 if completed else 0)
        
        for day, completions in day_adherence.items():
            if completions:
                patterns['weekly_patterns'][day] = sum(completions) / len(completions)
        
        # Activity type patterns
        activity_types = {}
        for activity in recent_activities:
            activity_type = activity.get('type', 'unknown')
            completed = activity.get('completed', False)
            
            if activity_type not in activity_types:
                activity_types[activity_type] = []
            activity_types[activity_type].append(1 if completed else 0)
        
        for activity_type, completions in activity_types.items():
            if completions:
                patterns['activity_type_patterns'][activity_type] = sum(completions) / len(completions)
        
        return patterns
    
    def _assess_motivation_trend(self, wellness_history: Dict[str, Any]) -> Dict[str, Any]:
        """Assess motivation trend over time."""
        recent_activities = wellness_history.get('recent_activities', [])
        
        if len(recent_activities) < 14:
            return {'insufficient_data': True}
        
        # Split into two periods for comparison
        mid_point = len(recent_activities) // 2
        earlier_period = recent_activities[:mid_point]
        recent_period = recent_activities[mid_point:]
        
        # Calculate engagement scores for each period
        earlier_engagement = sum(activity.get('engagement_score', 5) for activity in earlier_period) / len(earlier_period)
        recent_engagement = sum(activity.get('engagement_score', 5) for activity in recent_period) / len(recent_period)
        
        # Calculate completion rates
        earlier_completion = sum(1 for activity in earlier_period if activity.get('completed', False)) / len(earlier_period)
        recent_completion = sum(1 for activity in recent_period if activity.get('completed', False)) / len(recent_period)
        
        # Determine trend
        engagement_change = recent_engagement - earlier_engagement
        completion_change = recent_completion - earlier_completion
        
        if engagement_change > 0.5 and completion_change > 0.1:
            trend = 'improving'
        elif engagement_change < -0.5 or completion_change < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'engagement_change': round(engagement_change, 2),
            'completion_change': round(completion_change, 2),
            'earlier_period_engagement': round(earlier_engagement, 2),
            'recent_period_engagement': round(recent_engagement, 2)
        }
    
    def _assess_resilience_factors(self, life_context: Dict[str, Any], coping_resources: List[str]) -> Dict[str, Any]:
        """Assess factors that contribute to resilience and stress management."""
        resilience_score = 0
        max_score = 0
        
        # Social support (25% of resilience)
        social_support = life_context.get('social_support_level', 5)  # 1-10 scale
        resilience_score += (social_support / 10) * 25
        max_score += 25
        
        # Coping resources (35% of resilience)
        effective_coping_resources = ['exercise', 'meditation', 'social_connection', 'hobbies', 'professional_help']
        available_effective_resources = len([resource for resource in coping_resources 
                                           if resource in effective_coping_resources])
        coping_points = min(available_effective_resources / len(effective_coping_resources), 1.0) * 35
        resilience_score += coping_points
        max_score += 35
        
        # Life stability (25% of resilience)
        recent_changes = len(life_context.get('recent_changes', []))
        stability_score = max(0, 1 - (recent_changes / 5))  # Normalize to 0-1
        resilience_score += stability_score * 25
        max_score += 25
        
        # Self-efficacy (15% of resilience)
        self_efficacy = life_context.get('self_efficacy_score', 7)  # 1-10 scale
        resilience_score += (self_efficacy / 10) * 15
        max_score += 15
        
        resilience_percentage = (resilience_score / max_score) * 100 if max_score > 0 else 50
        
        return {
            'resilience_score': round(resilience_percentage, 1),
            'resilience_level': 'high' if resilience_percentage >= 75 else 
                              'medium' if resilience_percentage >= 50 else 'low',
            'contributing_factors': {
                'social_support': social_support,
                'coping_resources_count': available_effective_resources,
                'life_stability': round(stability_score, 2),
                'self_efficacy': self_efficacy
            }
        }
    
    def generate_complexity_adjustments(self, cognitive_load: Dict[str, Any], motivation_level: str, stress_level: str) -> Dict[str, Any]:
        """
        Generate complexity adjustments for other agents based on mental wellness assessment.
        
        Args:
            cognitive_load: Current cognitive load assessment
            motivation_level: Current motivation level
            stress_level: Current stress level
            
        Returns:
            Complexity adjustment recommendations for other agents
        """
        adjustments = {
            'fitness_simplification': {},
            'nutrition_simplification': {},
            'sleep_simplification': {},
            'overall_plan_changes': []
        }
        
        # Determine adjustment level based on multiple factors
        if (cognitive_load.get('load_level') == 'overload' or 
            motivation_level == 'low' or 
            stress_level == 'high'):
            
            # High simplification needed
            adjustments['fitness_simplification'] = {
                'reduce_exercise_variety': True,
                'focus_on_familiar_activities': True,
                'limit_new_exercises': 1,
                'reduce_tracking_requirements': True,
                'simplify_progression': True
            }
            
            adjustments['nutrition_simplification'] = {
                'reduce_meal_variety': True,
                'focus_on_simple_meals': True,
                'limit_new_recipes': 1,
                'reduce_meal_prep_complexity': True,
                'use_familiar_foods': True
            }
            
            adjustments['sleep_simplification'] = {
                'focus_on_consistent_bedtime': True,
                'limit_sleep_environment_changes': True,
                'simplify_pre_sleep_routine': True
            }
            
            adjustments['overall_plan_changes'] = [
                'Reduce simultaneous changes to maximum 2',
                'Focus on maintaining existing habits rather than building new ones',
                'Increase support and check-in frequency',
                'Add stress management as priority'
            ]
            
        elif (cognitive_load.get('load_level') == 'high' or 
              motivation_level == 'medium' or 
              stress_level == 'medium'):
            
            # Moderate simplification needed
            adjustments['fitness_simplification'] = {
                'limit_new_exercises': 2,
                'maintain_current_complexity': True,
                'add_flexibility_options': True
            }
            
            adjustments['nutrition_simplification'] = {
                'limit_new_recipes': 2,
                'provide_simple_alternatives': True,
                'maintain_current_meal_structure': True
            }
            
            adjustments['sleep_simplification'] = {
                'maintain_current_routine': True,
                'add_stress_management_techniques': True
            }
            
            adjustments['overall_plan_changes'] = [
                'Limit simultaneous changes to maximum 3',
                'Provide more flexibility in implementation',
                'Add motivation support strategies'
            ]
            
        else:
            # Low/no simplification needed - can handle complexity
            adjustments['overall_plan_changes'] = [
                'Current complexity level is appropriate',
                'Can consider gradual complexity increases',
                'Monitor for signs of overload'
            ]
        
        return adjustments
    
    def detect_preference_fatigue(self, wellness_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect preference fatigue from repeated similar recommendations.
        
        Args:
            wellness_history: Historical wellness activity data
            
        Returns:
            Preference fatigue assessment and variety recommendations
        """
        recent_activities = wellness_history.get('recent_activities', [])
        
        if len(recent_activities) < self.preference_fatigue_window:
            return {'insufficient_data': True}
        
        # Analyze variety in different domains
        domain_variety = {}
        
        for domain in ['fitness', 'nutrition', 'sleep']:
            domain_activities = [activity for activity in recent_activities 
                               if activity.get('domain') == domain]
            
            if domain_activities:
                activity_types = [activity.get('type') for activity in domain_activities]
                unique_types = len(set(activity_types))
                total_activities = len(activity_types)
                
                variety_ratio = unique_types / total_activities if total_activities > 0 else 0
                
                domain_variety[domain] = {
                    'variety_ratio': variety_ratio,
                    'fatigue_risk': 'high' if variety_ratio < self.variety_threshold else 'low',
                    'unique_activities': unique_types,
                    'total_activities': total_activities
                }
        
        # Overall preference fatigue assessment
        avg_variety = sum(domain['variety_ratio'] for domain in domain_variety.values()) / len(domain_variety)
        
        fatigue_level = 'high' if avg_variety < self.variety_threshold else \
                       'medium' if avg_variety < self.variety_threshold * 1.5 else 'low'
        
        # Generate variety recommendations
        variety_recommendations = []
        for domain, metrics in domain_variety.items():
            if metrics['fatigue_risk'] == 'high':
                if domain == 'fitness':
                    variety_recommendations.append('Introduce new exercise types or workout formats')
                elif domain == 'nutrition':
                    variety_recommendations.append('Add new cuisines or cooking methods')
                elif domain == 'sleep':
                    variety_recommendations.append('Vary relaxation techniques or sleep environment')
        
        return {
            'overall_fatigue_level': fatigue_level,
            'average_variety_ratio': round(avg_variety, 2),
            'domain_variety': domain_variety,
            'variety_recommendations': variety_recommendations,
            'analysis_period_days': self.preference_fatigue_window
        }
    
    def generate_motivation_strategies(self, motivation_assessment: Dict[str, Any], adherence_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate personalized motivation strategies based on assessment.
        
        Args:
            motivation_assessment: Current motivation level and factors
            adherence_analysis: Adherence patterns and trends
            
        Returns:
            List of personalized motivation strategies
        """
        strategies = []
        
        motivation_level = motivation_assessment.get('motivation_level', 'medium')
        motivation_issues = motivation_assessment.get('motivation_issues', [])
        adherence_trend = adherence_analysis.get('overall_trend', 'stable')
        
        # Base strategies for motivation level
        if motivation_level == 'low':
            strategies.extend([
                'Focus on very small, achievable daily wins',
                'Reduce goals to absolute minimum viable habits',
                'Celebrate any progress, no matter how small',
                'Consider external accountability partner or system'
            ])
        elif motivation_level == 'medium':
            strategies.extend([
                'Set weekly mini-challenges to maintain engagement',
                'Track progress visually with charts or apps',
                'Reward yourself for consistency milestones'
            ])
        else:  # high motivation
            strategies.extend([
                'Channel high motivation into building sustainable systems',
                'Set stretch goals while maintaining realistic expectations',
                'Consider helping others to maintain engagement'
            ])
        
        # Address specific motivation issues
        if 'low_adherence' in motivation_issues:
            strategies.extend([
                'Identify and remove barriers to completion',
                'Use implementation intentions (if-then planning)',
                'Start with habit stacking on existing routines'
            ])
        
        if 'low_engagement' in motivation_issues:
            strategies.extend([
                'Find ways to make activities more enjoyable',
                'Connect activities to personal values and identity',
                'Introduce variety and novelty regularly'
            ])
        
        if 'high_stress' in motivation_issues:
            strategies.extend([
                'Prioritize stress management over performance goals',
                'Use wellness activities as stress relief, not additional pressure',
                'Practice self-compassion and flexible expectations'
            ])
        
        # Address adherence trends
        if adherence_trend == 'declining':
            strategies.extend([
                'Investigate what changed to cause the decline',
                'Temporarily reduce expectations to rebuild confidence',
                'Focus on maintaining existing habits before adding new ones'
            ])
        elif adherence_trend == 'improving':
            strategies.extend([
                'Acknowledge and celebrate the positive trend',
                'Identify what\'s working well and do more of it',
                'Consider gradual expansion of successful strategies'
            ])
        
        return strategies
    
    def assess_decision_fatigue(self, agent_proposals: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess decision fatigue from wellness recommendations.
        
        Args:
            agent_proposals: Current proposals from other agents
            user_data: User profile and current state
            
        Returns:
            Decision fatigue assessment and recommendations
        """
        # Count decision points across all proposals
        daily_decisions = 0
        decision_complexity = 0
        
        for agent_name, proposal in agent_proposals.items():
            if agent_name == 'FitnessAgent':
                workout_plan = proposal.get('workout_plan', {})
                # Count exercise selection decisions
                if workout_plan.get('requires_exercise_selection', False):
                    daily_decisions += 1
                    decision_complexity += 2
                
                # Count intensity/duration decisions
                if workout_plan.get('requires_intensity_decisions', False):
                    daily_decisions += 1
                    decision_complexity += 1
            
            elif agent_name == 'NutritionAgent':
                meal_plan = proposal.get('meal_plan', {})
                # Count meal planning decisions
                daily_meals = len(meal_plan.get('daily_meals', []))
                if meal_plan.get('requires_daily_planning', False):
                    daily_decisions += daily_meals
                    decision_complexity += daily_meals * 2
                
                # Count substitution decisions
                if meal_plan.get('allows_substitutions', False):
                    daily_decisions += 1
                    decision_complexity += 1
            
            elif agent_name == 'SleepAgent':
                sleep_recs = proposal.get('sleep_recommendations', {})
                # Count sleep timing decisions
                if sleep_recs.get('flexible_timing', False):
                    daily_decisions += 1
                    decision_complexity += 1
        
        # Assess user's decision-making capacity
        stress_level = user_data.get('stress_indicators', {}).get('stress_level', 5)
        mental_energy = user_data.get('mental_health', {}).get('mental_energy', 7)
        
        # Calculate decision fatigue risk
        capacity_reduction = 1.0
        if stress_level > 7:
            capacity_reduction = 0.5
        elif stress_level > 5:
            capacity_reduction = 0.75
        
        if mental_energy < 5:
            capacity_reduction *= 0.8
        
        effective_decision_capacity = 10 * capacity_reduction  # Base capacity of 10 decisions
        
        fatigue_risk = 'low'
        if daily_decisions > effective_decision_capacity:
            fatigue_risk = 'high'
        elif daily_decisions > effective_decision_capacity * 0.8:
            fatigue_risk = 'medium'
        
        # Generate recommendations to reduce decision fatigue
        recommendations = []
        if fatigue_risk in ['medium', 'high']:
            recommendations.extend([
                'Pre-plan decisions during high-energy times',
                'Use default options to reduce daily choices',
                'Batch similar decisions together',
                'Automate routine decisions where possible'
            ])
        
        if fatigue_risk == 'high':
            recommendations.extend([
                'Significantly reduce the number of daily wellness decisions',
                'Focus on one domain at a time to minimize cognitive load',
                'Use simple yes/no decisions instead of complex choices'
            ])
        
        return {
            'daily_decisions_count': daily_decisions,
            'decision_complexity_score': decision_complexity,
            'effective_capacity': round(effective_decision_capacity, 1),
            'fatigue_risk': fatigue_risk,
            'capacity_factors': {
                'stress_level': stress_level,
                'mental_energy': mental_energy,
                'capacity_reduction': capacity_reduction
            },
            'recommendations': recommendations
        }


def create_mental_wellness_agent(confidence_threshold: float = 0.7) -> MentalWellnessAgent:
    """
    Factory function to create a MentalWellnessAgent instance.
    
    Args:
        confidence_threshold: Minimum confidence for proposals
        
    Returns:
        Configured MentalWellnessAgent instance
    """
    return MentalWellnessAgent(confidence_threshold=confidence_threshold)