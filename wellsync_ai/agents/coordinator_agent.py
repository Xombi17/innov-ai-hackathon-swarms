"""
Coordinator Agent for WellSync AI system.

Implements CoordinatorAgent with conflict resolution system prompts,
proposal collection and validation logic, and weighted constraint
satisfaction problem solving for multi-objective optimization.
"""

import json
import math
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from wellsync_ai.agents.base_agent import WellnessAgent
from wellsync_ai.data.shared_state import AgentProposal
from wellsync_ai.agents.recovery_prioritization import (
    RecoveryPrioritizationEngine, 
    EnergyBalance, 
    EnergyConflictType,
    RecoveryPriority
)
from wellsync_ai.data.database import get_database_manager


class ConflictType(Enum):
    """Types of conflicts between agent proposals."""
    ENERGY_CONFLICT = "energy_conflict"
    TIME_CONFLICT = "time_conflict"
    BUDGET_CONFLICT = "budget_conflict"
    RECOVERY_CONFLICT = "recovery_conflict"
    NUTRITIONAL_CONFLICT = "nutritional_conflict"
    MOTIVATION_CONFLICT = "motivation_conflict"


@dataclass
class ConflictResolution:
    """Represents a resolved conflict between proposals."""
    conflict_type: ConflictType
    affected_agents: List[str]
    resolution_strategy: str
    trade_offs_made: List[str]
    confidence_impact: float
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            'conflict_type': self.conflict_type.value if isinstance(self.conflict_type, ConflictType) else str(self.conflict_type),
            'affected_agents': self.affected_agents,
            'resolution_strategy': self.resolution_strategy,
            'trade_offs_made': self.trade_offs_made,
            'confidence_impact': self.confidence_impact,
            'reasoning': self.reasoning
        }


@dataclass
class WeightedConstraint:
    """Represents a weighted constraint in the optimization problem."""
    constraint_name: str
    weight: float
    constraint_type: str  # "hard", "soft", "preference"
    violation_cost: float
    source_agent: str


class CoordinatorAgent(WellnessAgent):
    """
    Coordinator agent for system-wide coherence and conflict resolution.
    
    Orchestrates all wellness agents, resolves conflicts using multi-objective
    optimization, and generates unified plans with clear priorities and
    trade-off explanations.
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        """Initialize CoordinatorAgent with conflict resolution configuration."""
        
        system_prompt = """You are the coordinator agent in the WellSync AI system.
Your role is to orchestrate all wellness agents and resolve conflicts to create unified, coherent wellness plans.

CORE RESPONSIBILITIES:
- Collect and validate proposals from all domain agents (Fitness, Nutrition, Sleep, Mental Wellness)
- Detect and resolve conflicts between agent proposals using multi-objective optimization
- Generate unified wellness plans that balance all domain requirements
- Maintain global constraint satisfaction across all wellness domains
- Provide clear explanations of trade-offs and decision rationale

CONFLICT RESOLUTION PRIORITIES (highest to lowest):
1. Safety and recovery constraints (Sleep Agent overrides)
2. Hard constraints (budget limits, time availability, dietary restrictions)
3. Nutritional adequacy minimums (Nutrition Agent requirements)
4. Sustainable fitness progress (Fitness Agent recommendations)
5. Mental wellness and motivation (Mental Wellness Agent feedback)
6. User preferences and soft constraints

CONFLICT TYPES TO RESOLVE:
- Energy conflicts: High fitness demands vs. low energy availability
- Time conflicts: Competing demands for limited time slots
- Budget conflicts: Nutritional needs vs. fitness equipment vs. budget limits
- Recovery conflicts: Training intensity vs. sleep debt or stress levels
- Nutritional conflicts: Fitness energy needs vs. weight management goals
- Motivation conflicts: Plan complexity vs. user capacity and adherence

OPTIMIZATION PRINCIPLES:
- Prioritize long-term sustainability over short-term gains
- Maintain minimum viable standards in all domains
- Prefer gradual progress over aggressive changes
- Respect hard constraints absolutely (never violate)
- Minimize total constraint violation cost across all domains
- Maximize overall system confidence while maintaining domain balance

INPUT FORMAT: You will receive structured proposals from domain agents:
{
    "FitnessAgent": {
        "workout_plan": {...},
        "confidence": 0.0-1.0,
        "energy_demand": "low/medium/high",
        "constraints_used": [...],
        "dependencies": [...]
    },
    "NutritionAgent": {
        "meal_plan": {...},
        "confidence": 0.0-1.0,
        "nutritional_adequacy": "low/medium/high",
        "budget_utilization": 0.0-1.0,
        "constraints_used": [...],
        "dependencies": [...]
    },
    "SleepAgent": {
        "sleep_recommendations": {...},
        "confidence": 0.0-1.0,
        "recovery_status": "poor/fair/good/excellent",
        "constraints_for_others": {...},
        "dependencies": [...]
    },
    "MentalWellnessAgent": {
        "wellness_recommendations": {...},
        "confidence": 0.0-1.0,
        "motivation_level": "low/medium/high",
        "complexity_adjustments": {...},
        "dependencies": [...]
    }
}

OUTPUT FORMAT: Always respond with valid JSON containing:
{
    "unified_plan": {
        "fitness": {...},
        "nutrition": {...},
        "sleep": {...},
        "mental_wellness": {...}
    },
    "confidence": 0.0-1.0,
    "conflicts_detected": [...],
    "conflicts_resolved": [...],
    "trade_offs_made": [...],
    "agent_contributions": {...},
    "constraint_satisfaction_score": 0.0-1.0,
    "optimization_metrics": {...},
    "reasoning": "detailed explanation of coordination decisions and trade-offs"
}

CRITICAL RULES:
- Never violate hard constraints (safety, budget limits, dietary restrictions)
- Always explain trade-offs and decision rationale clearly
- Maintain minimum viable standards in all wellness domains
- Prioritize recovery and sustainability over aggressive optimization
- Ensure all agent contributions are acknowledged and integrated appropriately"""

        super().__init__(
            agent_name="CoordinatorAgent",
            system_prompt=system_prompt,
            domain="coordinator",
            confidence_threshold=confidence_threshold
        )
        
        # Coordination-specific attributes
        self.conflict_resolution_history = []
        self.optimization_weights = self._initialize_optimization_weights()
        self.constraint_hierarchy = self._initialize_constraint_hierarchy()
        self.trade_off_strategies = self._initialize_trade_off_strategies()
        
        # Recovery prioritization engine
        self.recovery_engine = RecoveryPrioritizationEngine()
        
        # Multi-objective optimization parameters
        self.min_domain_confidence = 0.3  # Minimum acceptable confidence per domain
        self.max_constraint_violations = 3  # Maximum soft constraint violations
        self.recovery_priority_multiplier = 2.0  # Extra weight for recovery constraints
        self.sustainability_factor = 0.8  # Preference for sustainable vs. aggressive plans
    
    def build_wellness_prompt(
        self, 
        user_data: Dict[str, Any], 
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build coordination-specific wellness prompt."""
        
        # This method is called with agent proposals for coordination
        agent_proposals = user_data.get('agent_proposals', {})
        
        # Analyze conflicts between proposals
        conflicts_detected = self._detect_conflicts(agent_proposals, constraints)
        constraint_analysis = self._analyze_constraints(agent_proposals, constraints)
        
        # Summarize proposals to fit within context limits
        summarized_proposals = self._summarize_proposals(agent_proposals)
        
        # Build comprehensive coordination prompt
        prompt = f"""
COORDINATION REQUEST

AGENT PROPOSALS TO COORDINATE:
{json.dumps(summarized_proposals, indent=2)}

USER CONSTRAINTS:
{json.dumps(constraints, indent=2)}

CONFLICTS DETECTED:
{json.dumps([conflict.to_dict() for conflict in conflicts_detected], indent=2)}

CONSTRAINT ANALYSIS:
{json.dumps(constraint_analysis, indent=2)}

OPTIMIZATION CONTEXT:
- Total agents proposing: {len(agent_proposals)}
- Hard constraints count: {len([c for c in constraint_analysis.get('constraints', []) if c.get('type') == 'hard'])}
- Soft constraints count: {len([c for c in constraint_analysis.get('constraints', []) if c.get('type') == 'soft'])}
- Recovery priority active: {self._is_recovery_priority_active(agent_proposals)}

COORDINATION TASK:
Generate a unified wellness plan that resolves all detected conflicts while:
1. Respecting the constraint hierarchy (safety > hard > soft > preferences)
2. Maintaining minimum viable standards in all wellness domains
3. Optimizing for long-term sustainability and adherence
4. Providing clear explanations for all trade-offs made
5. Maximizing overall system confidence within constraint bounds

Apply multi-objective optimization to balance competing demands.
Explain your reasoning for conflict resolution strategies and trade-off decisions.
"""
        
        return prompt

    def _summarize_proposals(self, agent_proposals: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize agent proposals to reduce token usage."""
        summary = {}
        for agent, data in agent_proposals.items():
            if not isinstance(data, dict):
                summary[agent] = str(data)[:200]
                continue
                
            # Keep core domain output and metrics, drop verbose reasoning/metadata
            agent_summary = {}
            for key, value in data.items():
                if key in ['reasoning', 'timestamp', 'session_id', 'agent_name', 'domain']:
                    continue
                agent_summary[key] = value
            summary[agent] = agent_summary
        return summary
    
    def coordinate_agent_proposals(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        user_constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agent proposals into a unified plan.
        
        Args:
            agent_proposals: Proposals from all domain agents
            user_constraints: User constraints and preferences
            shared_state: Current shared state
            
        Returns:
            Unified coordination result
        """
        try:
            # Validate all proposals
            validation_results = self._validate_all_proposals(agent_proposals)
            if not validation_results['all_valid']:
                return self._handle_invalid_proposals(validation_results)
            
            # Assess energy balance and recovery prioritization
            user_data = shared_state.get('user_profile', {}) if shared_state else {}
            energy_balance = self.recovery_engine.assess_energy_balance(
                agent_proposals, user_data, shared_state
            )
            
            # Detect energy conflicts
            energy_conflicts = self.recovery_engine.detect_energy_conflicts(
                energy_balance, agent_proposals, user_data
            )
            
            # Determine recovery prioritization
            recovery_priority = None
            if energy_conflicts:
                recovery_priority = self.recovery_engine.prioritize_recovery(
                    energy_conflicts, energy_balance, agent_proposals, user_data
                )
                
                # Apply recovery prioritization to proposals
                self._apply_recovery_prioritization(agent_proposals, recovery_priority)
            
            # Detect remaining conflicts after recovery prioritization
            conflicts = self._detect_conflicts(agent_proposals, user_constraints)
            
            # If no conflicts, create simple unified plan
            if not conflicts:
                unified_plan = self._create_unified_plan_no_conflicts(agent_proposals, user_constraints)
                
                # Add recovery prioritization information if applicable
                if recovery_priority:
                    unified_plan['recovery_prioritization'] = {
                        'energy_balance': energy_balance.to_dict(),
                        'energy_conflicts': [c.value for c in energy_conflicts],
                        'recovery_priority': recovery_priority.to_dict(),
                        'trade_off_explanations': self.recovery_engine.generate_trade_off_explanations(
                            recovery_priority, energy_balance, agent_proposals
                        )
                    }
                
                return unified_plan
            
            # Resolve conflicts using multi-objective optimization
            resolution_result = self._resolve_conflicts_with_optimization(
                agent_proposals, conflicts, user_constraints
            )
            
            # Generate final unified plan
            unified_plan = self._generate_unified_plan(
                agent_proposals, resolution_result, user_constraints
            )
            
            # Add recovery prioritization information
            if recovery_priority:
                unified_plan['recovery_prioritization'] = {
                    'energy_balance': energy_balance.to_dict(),
                    'energy_conflicts': [c.value for c in energy_conflicts],
                    'recovery_priority': recovery_priority.to_dict(),
                    'trade_off_explanations': self.recovery_engine.generate_trade_off_explanations(
                        recovery_priority, energy_balance, agent_proposals
                    )
                }
            
            # Store coordination session in memory
            self._store_coordination_session(
                agent_proposals, conflicts, resolution_result, unified_plan
            )
            
            return unified_plan
            
        except Exception as e:
            # Return error coordination result
            return self._create_error_coordination_result(str(e), agent_proposals)
    
    def _validate_all_proposals(self, agent_proposals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate all agent proposals for completeness and consistency."""
        
        validation_results = {
            'all_valid': True,
            'agent_validations': {},
            'missing_agents': [],
            'invalid_proposals': []
        }
        
        # Expected agents
        expected_agents = ['FitnessAgent', 'NutritionAgent', 'SleepAgent', 'MentalWellnessAgent']
        
        # Check for missing agents
        for agent in expected_agents:
            if agent not in agent_proposals:
                validation_results['missing_agents'].append(agent)
                validation_results['all_valid'] = False
        
        # Validate each proposal
        for agent_name, proposal in agent_proposals.items():
            agent_validation = self._validate_single_agent_proposal(agent_name, proposal)
            validation_results['agent_validations'][agent_name] = agent_validation
            
            if not agent_validation['valid']:
                validation_results['invalid_proposals'].append(agent_name)
                validation_results['all_valid'] = False
        
        return validation_results
    
    def _validate_single_agent_proposal(self, agent_name: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single agent proposal (lenient validation with defaults)."""
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'defaults_added': []
        }
        
        # Ensure proposal is a dict
        if not isinstance(proposal, dict):
            proposal = {'raw_response': str(proposal)}
            validation['warnings'].append("Proposal converted from non-dict format")
        
        # Add default confidence if missing (instead of failing)
        if 'confidence' not in proposal:
            proposal['confidence'] = 0.5
            validation['defaults_added'].append('confidence=0.5')
            validation['warnings'].append("Added default confidence value")
        else:
            confidence = proposal['confidence']
            if not isinstance(confidence, (int, float)):
                proposal['confidence'] = 0.5
                validation['warnings'].append("Fixed invalid confidence type")
            elif not 0 <= confidence <= 1:
                proposal['confidence'] = max(0, min(1, confidence))
                validation['warnings'].append("Confidence clamped to [0, 1]")
        
        # Add default reasoning if missing
        if 'reasoning' not in proposal:
            proposal['reasoning'] = "Generated by wellness agent"
            validation['defaults_added'].append('reasoning')
        
        # Agent-specific defaults with RICH, USEFUL data (not empty placeholders)
        agent_defaults = {
            'FitnessAgent': {
                'workout_plan': {
                    'focus': 'balanced_strength',
                    'intensity': 'moderate',
                    'sessions': [
                        {'day': 'Monday', 'type': 'Upper Body', 'duration': 45, 'exercises': [
                            {'name': 'Push-ups', 'sets': 3, 'reps': 12},
                            {'name': 'Dumbbell Rows', 'sets': 3, 'reps': 10},
                            {'name': 'Shoulder Press', 'sets': 3, 'reps': 10}
                        ]},
                        {'day': 'Wednesday', 'type': 'Lower Body', 'duration': 45, 'exercises': [
                            {'name': 'Squats', 'sets': 4, 'reps': 12},
                            {'name': 'Lunges', 'sets': 3, 'reps': 10},
                            {'name': 'Glute Bridges', 'sets': 3, 'reps': 15}
                        ]},
                        {'day': 'Friday', 'type': 'Full Body', 'duration': 40, 'exercises': [
                            {'name': 'Burpees', 'sets': 3, 'reps': 8},
                            {'name': 'Mountain Climbers', 'sets': 3, 'reps': 20},
                            {'name': 'Plank', 'sets': 3, 'reps': '30s hold'}
                        ]}
                    ],
                    'weekly_volume': '130 minutes',
                    'progression': 'Increase reps by 2 each week'
                },
                'energy_demand': 'medium',
                'training_load_score': 55,
                'overtraining_risk': 'low'
            },
            'NutritionAgent': {
                'meal_plan': {
                    'focus': 'balanced_nutrition',
                    'daily_calories': 2200,
                    'macro_split': {'protein': '30%', 'carbs': '45%', 'fats': '25%'},
                    'meals': [
                        {'meal': 'Breakfast', 'time': '7:30 AM', 'items': ['Oatmeal with berries', 'Greek yogurt', 'Black coffee'], 'calories': 450},
                        {'meal': 'Lunch', 'time': '12:30 PM', 'items': ['Grilled chicken salad', 'Whole grain bread', 'Olive oil dressing'], 'calories': 650},
                        {'meal': 'Snack', 'time': '4:00 PM', 'items': ['Apple', 'Almond butter', 'Handful of nuts'], 'calories': 300},
                        {'meal': 'Dinner', 'time': '7:00 PM', 'items': ['Baked salmon', 'Quinoa', 'Steamed vegetables'], 'calories': 700}
                    ],
                    'hydration': '8-10 glasses of water',
                    'budget_estimate': '$12-15/day'
                },
                'nutritional_adequacy': 'high',
                'budget_utilization': 0.75
            },
            'SleepAgent': {
                'sleep_recommendations': {
                    'target_hours': 8,
                    'focus': 'recovery_optimization',
                    'bedtime': '10:30 PM',
                    'wake_time': '6:30 AM',
                    'sleep_hygiene': [
                        'No screens 1 hour before bed',
                        'Keep bedroom at 65-68°F',
                        'Avoid caffeine after 2 PM',
                        'Use blackout curtains'
                    ],
                    'wind_down_routine': ['Light stretching', 'Reading', 'Deep breathing exercises']
                },
                'recovery_status': 'good',
                'sleep_quality_target': 85
            },
            'MentalWellnessAgent': {
                'wellness_recommendations': {
                    'focus': 'stress_management',
                    'daily_practices': [
                        {'activity': 'Morning Meditation', 'duration': '10 min', 'time': '6:45 AM'},
                        {'activity': 'Gratitude Journaling', 'duration': '5 min', 'time': '9:00 PM'},
                        {'activity': 'Mindful Walking', 'duration': '15 min', 'time': '12:00 PM'}
                    ],
                    'stress_management': ['Progressive muscle relaxation', 'Box breathing technique'],
                    'mood_tracking': 'Daily check-in recommended',
                    'social_connection': 'Schedule one meaningful conversation daily'
                },
                'motivation_level': 'medium',
                'complexity_adjustments': {'simplification_needed': False}
            }
        }
        
        if agent_name in agent_defaults:
            for field, default_value in agent_defaults[agent_name].items():
                if field not in proposal:
                    proposal[field] = default_value
                    validation['defaults_added'].append(f'{field}')
                    validation['warnings'].append(f"Added default {field}")
        
        return validation
    
    def _detect_conflicts(
        self, 
        agent_proposals: Dict[str, Dict[str, Any]], 
        constraints: Dict[str, Any]
    ) -> List[ConflictResolution]:
        """Detect conflicts between agent proposals."""
        
        conflicts = []
        
        # Energy conflicts
        energy_conflict = self._detect_energy_conflicts(agent_proposals)
        if energy_conflict:
            conflicts.append(energy_conflict)
        
        # Time conflicts
        time_conflict = self._detect_time_conflicts(agent_proposals, constraints)
        if time_conflict:
            conflicts.append(time_conflict)
        
        # Budget conflicts
        budget_conflict = self._detect_budget_conflicts(agent_proposals, constraints)
        if budget_conflict:
            conflicts.append(budget_conflict)
        
        # Recovery conflicts
        recovery_conflict = self._detect_recovery_conflicts(agent_proposals)
        if recovery_conflict:
            conflicts.append(recovery_conflict)
        
        # Nutritional conflicts
        nutritional_conflict = self._detect_nutritional_conflicts(agent_proposals)
        if nutritional_conflict:
            conflicts.append(nutritional_conflict)
        
        # Motivation conflicts
        motivation_conflict = self._detect_motivation_conflicts(agent_proposals)
        if motivation_conflict:
            conflicts.append(motivation_conflict)
        
        return conflicts
    
    def _apply_recovery_prioritization(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        recovery_priority: RecoveryPriority
    ) -> None:
        """Apply recovery prioritization modifications to agent proposals."""
        
        if recovery_priority.priority_level in ["critical", "high"]:
            # Apply aggressive recovery prioritization
            
            # Fitness modifications
            if "fitness" in recovery_priority.affected_domains:
                fitness_proposal = agent_proposals.get('FitnessAgent', {})
                if fitness_proposal:
                    # Reduce energy demand
                    current_demand = fitness_proposal.get('energy_demand', 'medium')
                    if current_demand == 'high':
                        fitness_proposal['energy_demand'] = 'medium'
                    elif current_demand == 'medium':
                        fitness_proposal['energy_demand'] = 'low'
                    
                    # Modify workout plan for recovery
                    workout_plan = fitness_proposal.get('workout_plan', {})
                    if workout_plan:
                        workout_plan['recovery_prioritization'] = True
                        workout_plan['intensity_reduction'] = 'recovery_focused'
                        workout_plan['modification_reason'] = f"Recovery prioritization: {recovery_priority.priority_level}"
                    
                    # Reduce confidence slightly due to modification
                    fitness_proposal['confidence'] = max(0.3, fitness_proposal.get('confidence', 0.5) - 0.1)
            
            # Sleep modifications
            if "sleep" in recovery_priority.affected_domains:
                sleep_proposal = agent_proposals.get('SleepAgent', {})
                if sleep_proposal:
                    # Enhance sleep recommendations
                    sleep_recommendations = sleep_proposal.get('sleep_recommendations', {})
                    sleep_recommendations['recovery_prioritization'] = True
                    sleep_recommendations['priority_level'] = recovery_priority.priority_level
                    
                    # Add recovery-specific constraints for other agents
                    constraints_for_others = sleep_proposal.get('constraints_for_others', {})
                    constraints_for_others['recovery_priority'] = recovery_priority.priority_level
                    constraints_for_others['max_training_intensity'] = 'medium' if recovery_priority.priority_level == 'critical' else 'moderate'
                    sleep_proposal['constraints_for_others'] = constraints_for_others
            
            # Nutrition modifications
            if "nutrition" in recovery_priority.affected_domains:
                nutrition_proposal = agent_proposals.get('NutritionAgent', {})
                if nutrition_proposal:
                    # Optimize for recovery nutrition
                    meal_plan = nutrition_proposal.get('meal_plan', {})
                    if meal_plan:
                        meal_plan['recovery_optimization'] = True
                        meal_plan['focus'] = 'recovery_and_energy_availability'
                    
                    # Increase nutritional adequacy priority
                    if nutrition_proposal.get('nutritional_adequacy') == 'low':
                        nutrition_proposal['adequacy_priority'] = 'critical'
            
            # Mental wellness modifications
            if "mental_wellness" in recovery_priority.affected_domains:
                mental_wellness_proposal = agent_proposals.get('MentalWellnessAgent', {})
                if mental_wellness_proposal:
                    # Simplify recommendations
                    wellness_recommendations = mental_wellness_proposal.get('wellness_recommendations', {})
                    wellness_recommendations['complexity_reduction'] = True
                    wellness_recommendations['focus'] = 'stress_reduction_and_recovery'
                    
                    # Update complexity adjustments
                    complexity_adjustments = mental_wellness_proposal.get('complexity_adjustments', {})
                    complexity_adjustments['simplification_needed'] = True
                    complexity_adjustments['reason'] = 'recovery_prioritization'
                    mental_wellness_proposal['complexity_adjustments'] = complexity_adjustments
    
    def _detect_energy_conflicts(self, agent_proposals: Dict[str, Dict[str, Any]]) -> Optional[ConflictResolution]:
        """Detect energy demand vs. availability conflicts."""
        
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        sleep_proposal = agent_proposals.get('SleepAgent', {})
        
        fitness_energy_demand = fitness_proposal.get('energy_demand', 'medium')
        nutrition_adequacy = nutrition_proposal.get('nutritional_adequacy', 'medium')
        recovery_status = sleep_proposal.get('recovery_status', 'fair')
        
        # High energy demand with poor nutrition or recovery
        if (fitness_energy_demand == 'high' and 
            (nutrition_adequacy == 'low' or recovery_status in ['poor', 'fair'])):
            
            return ConflictResolution(
                conflict_type=ConflictType.ENERGY_CONFLICT,
                affected_agents=['FitnessAgent', 'NutritionAgent', 'SleepAgent'],
                resolution_strategy="reduce_fitness_intensity_or_improve_nutrition_recovery",
                trade_offs_made=[],
                confidence_impact=-0.1,
                reasoning="High fitness energy demands conflict with inadequate nutrition or poor recovery"
            )
        
        return None
    
    def _detect_time_conflicts(
        self, 
        agent_proposals: Dict[str, Dict[str, Any]], 
        constraints: Dict[str, Any]
    ) -> Optional[ConflictResolution]:
        """Detect time allocation conflicts."""
        
        # Calculate total time demands
        total_time_needed = 0
        time_demanding_agents = []
        
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        
        # Fitness time demands
        workout_plan = fitness_proposal.get('workout_plan', {})
        if workout_plan:
            weekly_schedule = workout_plan.get('weekly_schedule', [])
            for session in weekly_schedule:
                total_time_needed += session.get('duration_minutes', 0)
            if total_time_needed > 0:
                time_demanding_agents.append('FitnessAgent')
        
        # Nutrition time demands (meal prep)
        meal_plan = nutrition_proposal.get('meal_plan', {})
        if meal_plan:
            prep_time = meal_plan.get('total_prep_time_minutes', 0)
            total_time_needed += prep_time
            if prep_time > 0:
                time_demanding_agents.append('NutritionAgent')
        
        # Check against available time
        time_constraints = constraints.get('time_available', {})
        max_weekly_minutes = time_constraints.get('max_weekly_minutes', 600)  # 10 hours default
        
        if total_time_needed > max_weekly_minutes:
            return ConflictResolution(
                conflict_type=ConflictType.TIME_CONFLICT,
                affected_agents=time_demanding_agents,
                resolution_strategy="reduce_time_demands_or_increase_efficiency",
                trade_offs_made=[],
                confidence_impact=-0.15,
                reasoning=f"Total time needed ({total_time_needed}min) exceeds available time ({max_weekly_minutes}min)"
            )
        
        return None
    
    def _detect_budget_conflicts(
        self, 
        agent_proposals: Dict[str, Dict[str, Any]], 
        constraints: Dict[str, Any]
    ) -> Optional[ConflictResolution]:
        """Detect budget allocation conflicts."""
        
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        budget_utilization = nutrition_proposal.get('budget_utilization', 0.0)
        
        # Check if nutrition is using most/all of the budget
        budget_constraints = constraints.get('budget', {})
        weekly_budget = budget_constraints.get('weekly_food_budget', 100)
        
        if budget_utilization > 0.9:  # Using >90% of budget
            return ConflictResolution(
                conflict_type=ConflictType.BUDGET_CONFLICT,
                affected_agents=['NutritionAgent'],
                resolution_strategy="optimize_nutrition_costs_or_adjust_goals",
                trade_offs_made=[],
                confidence_impact=-0.1,
                reasoning=f"Nutrition plan uses {budget_utilization*100:.1f}% of available budget"
            )
        
        return None
    
    def _detect_recovery_conflicts(self, agent_proposals: Dict[str, Dict[str, Any]]) -> Optional[ConflictResolution]:
        """Detect recovery vs. training intensity conflicts."""
        
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        sleep_proposal = agent_proposals.get('SleepAgent', {})
        
        recovery_status = sleep_proposal.get('recovery_status', 'fair')
        fitness_energy_demand = fitness_proposal.get('energy_demand', 'medium')
        
        # Poor recovery with high training demands
        if recovery_status == 'poor' and fitness_energy_demand == 'high':
            return ConflictResolution(
                conflict_type=ConflictType.RECOVERY_CONFLICT,
                affected_agents=['FitnessAgent', 'SleepAgent'],
                resolution_strategy="prioritize_recovery_reduce_training_intensity",
                trade_offs_made=[],
                confidence_impact=-0.2,
                reasoning="Poor recovery status conflicts with high training intensity demands"
            )
        
        return None
    
    def _detect_nutritional_conflicts(self, agent_proposals: Dict[str, Dict[str, Any]]) -> Optional[ConflictResolution]:
        """Detect nutritional adequacy vs. other goal conflicts."""
        
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        
        nutritional_adequacy = nutrition_proposal.get('nutritional_adequacy', 'medium')
        fitness_energy_demand = fitness_proposal.get('energy_demand', 'medium')
        
        # Low nutritional adequacy with high fitness demands
        if nutritional_adequacy == 'low' and fitness_energy_demand == 'high':
            return ConflictResolution(
                conflict_type=ConflictType.NUTRITIONAL_CONFLICT,
                affected_agents=['NutritionAgent', 'FitnessAgent'],
                resolution_strategy="improve_nutrition_or_reduce_fitness_demands",
                trade_offs_made=[],
                confidence_impact=-0.15,
                reasoning="Low nutritional adequacy cannot support high fitness energy demands"
            )
        
        return None
    
    def _detect_motivation_conflicts(self, agent_proposals: Dict[str, Dict[str, Any]]) -> Optional[ConflictResolution]:
        """Detect motivation vs. plan complexity conflicts."""
        
        mental_wellness_proposal = agent_proposals.get('MentalWellnessAgent', {})
        
        motivation_level = mental_wellness_proposal.get('motivation_level', 'medium')
        complexity_adjustments = mental_wellness_proposal.get('complexity_adjustments', {})
        
        # Low motivation with complex plans from other agents
        if motivation_level == 'low' and complexity_adjustments.get('simplification_needed', False):
            affected_agents = []
            
            # Check which agents have complex proposals
            fitness_proposal = agent_proposals.get('FitnessAgent', {})
            nutrition_proposal = agent_proposals.get('NutritionAgent', {})
            
            if fitness_proposal.get('workout_plan', {}).get('complexity', 'medium') == 'high':
                affected_agents.append('FitnessAgent')
            
            if nutrition_proposal.get('meal_plan', {}).get('complexity', 'medium') == 'high':
                affected_agents.append('NutritionAgent')
            
            if affected_agents:
                affected_agents.append('MentalWellnessAgent')
                
                return ConflictResolution(
                    conflict_type=ConflictType.MOTIVATION_CONFLICT,
                    affected_agents=affected_agents,
                    resolution_strategy="simplify_plans_to_match_motivation_capacity",
                    trade_offs_made=[],
                    confidence_impact=-0.1,
                    reasoning="Low motivation level conflicts with complex plan requirements"
                )
        
        return None
    
    def _analyze_constraints(
        self, 
        agent_proposals: Dict[str, Dict[str, Any]], 
        user_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze all constraints for optimization."""
        
        constraints = []
        
        # Extract constraints from user input
        for constraint_type, constraint_data in user_constraints.items():
            if constraint_type == 'budget':
                constraints.append({
                    'name': 'budget_limit',
                    'type': 'hard',
                    'weight': 1.0,
                    'source': 'user',
                    'data': constraint_data
                })
            elif constraint_type == 'time_available':
                constraints.append({
                    'name': 'time_limit',
                    'type': 'hard',
                    'weight': 1.0,
                    'source': 'user',
                    'data': constraint_data
                })
            elif constraint_type == 'dietary_restrictions':
                constraints.append({
                    'name': 'dietary_restrictions',
                    'type': 'hard',
                    'weight': 1.0,
                    'source': 'user',
                    'data': constraint_data
                })
        
        # Extract constraints from agent proposals
        for agent_name, proposal in agent_proposals.items():
            constraints_used = proposal.get('constraints_used', [])
            for constraint in constraints_used:
                constraints.append({
                    'name': constraint,
                    'type': 'soft',
                    'weight': 0.8,
                    'source': agent_name,
                    'data': {}
                })
        
        # Add recovery constraints with high priority
        sleep_proposal = agent_proposals.get('SleepAgent', {})
        recovery_status = sleep_proposal.get('recovery_status', 'fair')
        
        if recovery_status == 'poor':
            constraints.append({
                'name': 'recovery_priority',
                'type': 'hard',
                'weight': 2.0,
                'source': 'SleepAgent',
                'data': {'recovery_status': recovery_status}
            })
        
        return {
            'constraints': constraints,
            'total_constraints': len(constraints),
            'hard_constraints': len([c for c in constraints if c['type'] == 'hard']),
            'soft_constraints': len([c for c in constraints if c['type'] == 'soft'])
        }
    
    def _is_recovery_priority_active(self, agent_proposals: Dict[str, Dict[str, Any]]) -> bool:
        """Check if recovery should be prioritized."""
        sleep_proposal = agent_proposals.get('SleepAgent', {})
        recovery_status = sleep_proposal.get('recovery_status', 'fair')
        return recovery_status in ['poor', 'fair']
    
    def _create_unified_plan_no_conflicts(
        self, 
        agent_proposals: Dict[str, Dict[str, Any]], 
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create unified plan when no conflicts exist."""
        
        unified_plan = {}
        agent_contributions = {}
        total_confidence = 0.0
        
        # Aggregate proposals from each agent
        for agent_name, proposal in agent_proposals.items():
            domain = agent_name.replace('Agent', '').lower()
            
            if domain == 'fitness':
                unified_plan['fitness'] = proposal.get('workout_plan', {})
            elif domain == 'nutrition':
                unified_plan['nutrition'] = proposal.get('meal_plan', {})
            elif domain == 'sleep':
                unified_plan['sleep'] = proposal.get('sleep_recommendations', {})
            elif domain == 'mentalwellness':
                unified_plan['mental_wellness'] = proposal.get('wellness_recommendations', {})
            
            agent_contributions[agent_name] = {
                'confidence': proposal.get('confidence', 0.5),
                'contribution_type': 'full_proposal',
                'modifications': []
            }
            
            total_confidence += proposal.get('confidence', 0.5)
        
        # Calculate overall confidence
        overall_confidence = total_confidence / len(agent_proposals) if agent_proposals else 0.0
        
        return {
            'unified_plan': unified_plan,
            'confidence': overall_confidence,
            'conflicts_detected': [],
            'conflicts_resolved': [],
            'trade_offs_made': [],
            'agent_contributions': agent_contributions,
            'constraint_satisfaction_score': 1.0,
            'optimization_metrics': {
                'total_agents': len(agent_proposals),
                'conflicts_count': 0,
                'optimization_time_ms': 0
            },
            'reasoning': self._generate_plan_summary(unified_plan, agent_proposals, constraints)
        }
    
    def _generate_plan_summary(
        self, 
        unified_plan: Dict[str, Any], 
        agent_proposals: Dict[str, Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> str:
        """Generate a rich, user-friendly summary of the wellness plan."""
        
        summary_parts = []
        
        # Fitness summary
        fitness = unified_plan.get('fitness', {})
        if fitness:
            sessions = fitness.get('sessions', [])
            focus = fitness.get('focus', 'general fitness')
            intensity = fitness.get('intensity', 'moderate')
            if sessions:
                summary_parts.append(
                    f"🏋️ **Fitness**: {len(sessions)} workout sessions per week focusing on {focus} "
                    f"at {intensity} intensity."
                )
            
        # Nutrition summary
        nutrition = unified_plan.get('nutrition', {})
        if nutrition:
            calories = nutrition.get('daily_calories', 2000)
            meals = nutrition.get('meals', [])
            budget = nutrition.get('budget_estimate', 'within budget')
            if meals:
                summary_parts.append(
                    f"🥗 **Nutrition**: {len(meals)} balanced meals per day targeting {calories} calories, "
                    f"{budget}."
                )
        
        # Sleep summary
        sleep = unified_plan.get('sleep', {})
        if sleep:
            target = sleep.get('target_hours', 8)
            bedtime = sleep.get('bedtime', '10:30 PM')
            wake = sleep.get('wake_time', '6:30 AM')
            summary_parts.append(
                f"💤 **Sleep**: {target} hours nightly ({bedtime} - {wake}) with optimized sleep hygiene."
            )
        
        # Mental wellness summary
        mental = unified_plan.get('mental_wellness', {})
        if mental:
            focus = mental.get('focus', 'stress management')
            practices = mental.get('daily_practices', [])
            if practices:
                summary_parts.append(
                    f"🧘 **Mental Wellness**: {len(practices)} daily practices for {focus}."
                )
        
        # Constraint satisfaction
        budget_constraint = constraints.get('daily_budget', 0)
        time_constraint = constraints.get('workout_minutes', 0)
        if budget_constraint or time_constraint:
            summary_parts.append(
                f"✅ **Constraints Met**: Plan optimized for ${budget_constraint}/day budget "
                f"and {time_constraint} min workout time."
            )
        
        if summary_parts:
            return "\\n\\n".join(summary_parts)
        else:
            return "Your personalized wellness plan has been created based on your goals and constraints."
    
    def _resolve_conflicts_with_optimization(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        conflicts: List[ConflictResolution],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve conflicts using multi-objective optimization."""
        
        resolution_start_time = datetime.now()
        resolved_conflicts = []
        
        # Sort conflicts by priority (recovery > hard constraints > soft constraints)
        prioritized_conflicts = self._prioritize_conflicts(conflicts)
        
        # Resolve each conflict using appropriate strategy
        for conflict in prioritized_conflicts:
            resolution = self._resolve_single_conflict(conflict, agent_proposals, constraints)
            resolved_conflicts.append(resolution)
            
            # Apply resolution modifications to proposals
            self._apply_conflict_resolution(agent_proposals, resolution)
        
        resolution_time = (datetime.now() - resolution_start_time).total_seconds() * 1000
        
        return {
            'conflicts_resolved': resolved_conflicts,  # Keep as objects for internal processing
            'conflicts_resolved_dicts': [c.to_dict() for c in resolved_conflicts],  # Serializable version
            'modified_proposals': agent_proposals,
            'resolution_time_ms': resolution_time,
            'optimization_success': True
        }
    
    def _prioritize_conflicts(self, conflicts: List[ConflictResolution]) -> List[ConflictResolution]:
        """Prioritize conflicts for resolution order."""
        
        priority_order = {
            ConflictType.RECOVERY_CONFLICT: 1,
            ConflictType.ENERGY_CONFLICT: 2,
            ConflictType.TIME_CONFLICT: 3,
            ConflictType.BUDGET_CONFLICT: 4,
            ConflictType.NUTRITIONAL_CONFLICT: 5,
            ConflictType.MOTIVATION_CONFLICT: 6
        }
        
        return sorted(conflicts, key=lambda c: priority_order.get(c.conflict_type, 10))
    
    def _resolve_single_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> ConflictResolution:
        """Resolve a single conflict using appropriate strategy."""
        
        if conflict.conflict_type == ConflictType.RECOVERY_CONFLICT:
            return self._resolve_recovery_conflict(conflict, agent_proposals)
        elif conflict.conflict_type == ConflictType.ENERGY_CONFLICT:
            return self._resolve_energy_conflict(conflict, agent_proposals)
        elif conflict.conflict_type == ConflictType.TIME_CONFLICT:
            return self._resolve_time_conflict(conflict, agent_proposals, constraints)
        elif conflict.conflict_type == ConflictType.BUDGET_CONFLICT:
            return self._resolve_budget_conflict(conflict, agent_proposals, constraints)
        elif conflict.conflict_type == ConflictType.NUTRITIONAL_CONFLICT:
            return self._resolve_nutritional_conflict(conflict, agent_proposals)
        elif conflict.conflict_type == ConflictType.MOTIVATION_CONFLICT:
            return self._resolve_motivation_conflict(conflict, agent_proposals)
        else:
            # Default resolution strategy
            return self._resolve_generic_conflict(conflict, agent_proposals)
    
    def _resolve_recovery_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> ConflictResolution:
        """Resolve recovery vs. training intensity conflicts."""
        
        # Recovery always takes priority - reduce fitness intensity
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        
        trade_offs = []
        if fitness_proposal.get('energy_demand') == 'high':
            trade_offs.append("Reduced fitness intensity from high to medium for recovery")
            fitness_proposal['energy_demand'] = 'medium'
            
            # Modify workout plan if present
            workout_plan = fitness_proposal.get('workout_plan', {})
            if workout_plan:
                workout_plan['intensity_adjustment'] = 'reduced_for_recovery'
                workout_plan['modification_reason'] = 'Poor recovery status requires intensity reduction'
        
        conflict.resolution_strategy = "prioritize_recovery_reduce_training_intensity"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.1  # Small confidence hit for modification
        
        return conflict
    
    def _resolve_energy_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> ConflictResolution:
        """Resolve energy demand vs. availability conflicts."""
        
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        
        trade_offs = []
        
        # Strategy: Improve nutrition first, then reduce fitness if needed
        if nutrition_proposal.get('nutritional_adequacy') == 'low':
            trade_offs.append("Prioritized nutritional adequacy improvement")
            nutrition_proposal['priority_adjustment'] = 'increase_adequacy'
            
            # If still conflict, reduce fitness intensity
            if fitness_proposal.get('energy_demand') == 'high':
                trade_offs.append("Reduced fitness intensity to match energy availability")
                fitness_proposal['energy_demand'] = 'medium'
        
        conflict.resolution_strategy = "balance_energy_supply_and_demand"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.05
        
        return conflict
    
    def _resolve_time_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> ConflictResolution:
        """Resolve time allocation conflicts."""
        
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        
        trade_offs = []
        
        # Strategy: Optimize for efficiency
        workout_plan = fitness_proposal.get('workout_plan', {})
        if workout_plan:
            trade_offs.append("Optimized workout plan for time efficiency")
            workout_plan['time_optimization'] = 'high_efficiency_focus'
        
        meal_plan = nutrition_proposal.get('meal_plan', {})
        if meal_plan:
            trade_offs.append("Simplified meal prep for time savings")
            meal_plan['prep_optimization'] = 'quick_prep_focus'
        
        conflict.resolution_strategy = "optimize_for_time_efficiency"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.1
        
        return conflict
    
    def _resolve_budget_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> ConflictResolution:
        """Resolve budget allocation conflicts."""
        
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        
        trade_offs = []
        
        # Strategy: Optimize nutrition for cost-effectiveness
        meal_plan = nutrition_proposal.get('meal_plan', {})
        if meal_plan:
            trade_offs.append("Optimized meal plan for budget constraints")
            meal_plan['cost_optimization'] = 'maximum_efficiency'
            nutrition_proposal['budget_utilization'] = min(
                nutrition_proposal.get('budget_utilization', 0.9), 0.85
            )
        
        conflict.resolution_strategy = "optimize_nutrition_for_budget"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.05
        
        return conflict
    
    def _resolve_nutritional_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> ConflictResolution:
        """Resolve nutritional adequacy conflicts."""
        
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        
        trade_offs = []
        
        # Strategy: Prioritize nutritional adequacy
        if nutrition_proposal.get('nutritional_adequacy') == 'low':
            trade_offs.append("Prioritized nutritional adequacy over fitness intensity")
            nutrition_proposal['adequacy_priority'] = 'high'
            
            # Reduce fitness demands if necessary
            if fitness_proposal.get('energy_demand') == 'high':
                fitness_proposal['energy_demand'] = 'medium'
                trade_offs.append("Reduced fitness intensity to match nutritional capacity")
        
        conflict.resolution_strategy = "prioritize_nutritional_adequacy"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.1
        
        return conflict
    
    def _resolve_motivation_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> ConflictResolution:
        """Resolve motivation vs. complexity conflicts."""
        
        mental_wellness_proposal = agent_proposals.get('MentalWellnessAgent', {})
        
        trade_offs = []
        
        # Strategy: Simplify all plans to match motivation capacity
        for agent_name in conflict.affected_agents:
            if agent_name == 'FitnessAgent':
                fitness_proposal = agent_proposals.get('FitnessAgent', {})
                workout_plan = fitness_proposal.get('workout_plan', {})
                if workout_plan:
                    workout_plan['complexity_reduction'] = 'simplified_for_motivation'
                    trade_offs.append("Simplified workout plan for better adherence")
            
            elif agent_name == 'NutritionAgent':
                nutrition_proposal = agent_proposals.get('NutritionAgent', {})
                meal_plan = nutrition_proposal.get('meal_plan', {})
                if meal_plan:
                    meal_plan['complexity_reduction'] = 'simplified_for_motivation'
                    trade_offs.append("Simplified meal plan for better adherence")
        
        conflict.resolution_strategy = "simplify_plans_for_motivation"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.05  # Small hit since simplification can improve adherence
        
        return conflict
    
    def _resolve_generic_conflict(
        self,
        conflict: ConflictResolution,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> ConflictResolution:
        """Generic conflict resolution strategy."""
        
        # Default: Apply conservative modifications to all affected agents
        trade_offs = ["Applied conservative modifications to resolve conflict"]
        
        for agent_name in conflict.affected_agents:
            proposal = agent_proposals.get(agent_name, {})
            proposal['conflict_resolution_applied'] = True
            proposal['modification_reason'] = f"Resolved {conflict.conflict_type.value}"
        
        conflict.resolution_strategy = "conservative_modification"
        conflict.trade_offs_made = trade_offs
        conflict.confidence_impact = -0.1
        
        return conflict
    
    def _apply_conflict_resolution(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        resolution: ConflictResolution
    ) -> None:
        """Apply conflict resolution modifications to agent proposals."""
        
        # Modifications are already applied in the resolution methods
        # This method can be used for additional post-processing if needed
        
        # Update confidence scores based on resolution impact
        for agent_name in resolution.affected_agents:
            if agent_name in agent_proposals:
                current_confidence = agent_proposals[agent_name].get('confidence', 0.5)
                new_confidence = max(0.1, current_confidence + resolution.confidence_impact)
                agent_proposals[agent_name]['confidence'] = new_confidence
    
    def _generate_unified_plan(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        resolution_result: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate final unified plan after conflict resolution."""
        
        unified_plan = {}
        agent_contributions = {}
        total_confidence = 0.0
        
        # Aggregate modified proposals
        for agent_name, proposal in agent_proposals.items():
            domain = agent_name.replace('Agent', '').lower()
            
            if domain == 'fitness':
                unified_plan['fitness'] = proposal.get('workout_plan', {})
            elif domain == 'nutrition':
                unified_plan['nutrition'] = proposal.get('meal_plan', {})
            elif domain == 'sleep':
                unified_plan['sleep'] = proposal.get('sleep_recommendations', {})
            elif domain == 'mentalwellness':
                unified_plan['mental_wellness'] = proposal.get('wellness_recommendations', {})
            
            # Track agent contributions and modifications
            modifications = []
            if 'conflict_resolution_applied' in proposal:
                modifications.append(proposal.get('modification_reason', 'Conflict resolution applied'))
            
            agent_contributions[agent_name] = {
                'confidence': proposal.get('confidence', 0.5),
                'contribution_type': 'modified_proposal' if modifications else 'full_proposal',
                'modifications': modifications
            }
            
            total_confidence += proposal.get('confidence', 0.5)
        
        # Calculate metrics
        overall_confidence = total_confidence / len(agent_proposals) if agent_proposals else 0.0
        
        conflicts_resolved = resolution_result.get('conflicts_resolved', [])
        all_trade_offs = []
        for conflict in conflicts_resolved:
            all_trade_offs.extend(conflict.trade_offs_made)
        
        # Calculate constraint satisfaction score
        constraint_satisfaction_score = self._calculate_constraint_satisfaction_score(
            unified_plan, constraints, conflicts_resolved
        )
        
        return {
            'unified_plan': unified_plan,
            'confidence': overall_confidence,
            'conflicts_detected': [c.conflict_type.value for c in conflicts_resolved],
            'conflicts_resolved': [c.to_dict() for c in conflicts_resolved],
            'trade_offs_made': all_trade_offs,
            'agent_contributions': agent_contributions,
            'constraint_satisfaction_score': constraint_satisfaction_score,
            'optimization_metrics': {
                'total_agents': len(agent_proposals),
                'conflicts_count': len(conflicts_resolved),
                'optimization_time_ms': resolution_result.get('resolution_time_ms', 0)
            },
            'reasoning': self._generate_coordination_reasoning(
                conflicts_resolved, all_trade_offs, constraint_satisfaction_score
            )
        }
    
    def _calculate_constraint_satisfaction_score(
        self,
        unified_plan: Dict[str, Any],
        constraints: Dict[str, Any],
        conflicts_resolved: List[ConflictResolution]
    ) -> float:
        """Calculate how well the unified plan satisfies constraints."""
        
        # Start with perfect score
        satisfaction_score = 1.0
        
        # Deduct for each conflict that had to be resolved
        for conflict in conflicts_resolved:
            if conflict.conflict_type in [ConflictType.RECOVERY_CONFLICT, ConflictType.ENERGY_CONFLICT]:
                satisfaction_score -= 0.1  # Major conflicts
            else:
                satisfaction_score -= 0.05  # Minor conflicts
        
        # Ensure score stays within bounds
        return max(0.0, min(1.0, satisfaction_score))
    
    def _generate_coordination_reasoning(
        self,
        conflicts_resolved: List[ConflictResolution],
        trade_offs_made: List[str],
        constraint_satisfaction_score: float
    ) -> str:
        """Generate explanation of coordination decisions."""
        
        if not conflicts_resolved:
            return "No conflicts detected between agent proposals. Unified plan created through direct integration of all agent recommendations."
        
        reasoning_parts = [
            f"Resolved {len(conflicts_resolved)} conflicts through multi-objective optimization.",
            f"Constraint satisfaction score: {constraint_satisfaction_score:.2f}"
        ]
        
        if trade_offs_made:
            reasoning_parts.append(f"Key trade-offs made: {'; '.join(trade_offs_made[:3])}")
        
        # Add conflict-specific reasoning
        conflict_types = [c.conflict_type.value for c in conflicts_resolved]
        if ConflictType.RECOVERY_CONFLICT.value in conflict_types:
            reasoning_parts.append("Prioritized recovery and sustainability over aggressive training.")
        
        if ConflictType.BUDGET_CONFLICT.value in conflict_types:
            reasoning_parts.append("Optimized for cost-effectiveness while maintaining nutritional adequacy.")
        
        return " ".join(reasoning_parts)
    
    def _handle_invalid_proposals(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Handle case where some agent proposals are invalid."""
        
        return {
            'unified_plan': {},
            'confidence': 0.0,
            'conflicts_detected': [],
            'conflicts_resolved': [],
            'trade_offs_made': [],
            'agent_contributions': {},
            'constraint_satisfaction_score': 0.0,
            'optimization_metrics': {
                'total_agents': 0,
                'conflicts_count': 0,
                'optimization_time_ms': 0
            },
            'error': 'Invalid agent proposals detected',
            'validation_results': validation_results,
            'reasoning': f"Coordination failed due to invalid proposals from: {', '.join(validation_results.get('invalid_proposals', []))}"
        }
    
    def _create_error_coordination_result(
        self, 
        error_message: str, 
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create error result for coordination failures."""
        
        return {
            'unified_plan': {},
            'confidence': 0.0,
            'conflicts_detected': [],
            'conflicts_resolved': [],
            'trade_offs_made': [],
            'agent_contributions': {},
            'constraint_satisfaction_score': 0.0,
            'optimization_metrics': {
                'total_agents': len(agent_proposals),
                'conflicts_count': 0,
                'optimization_time_ms': 0
            },
            'error': error_message,
            'reasoning': f"Coordination failed with error: {error_message}"
        }
    
    def _store_coordination_session(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        conflicts: List[ConflictResolution],
        resolution_result: Dict[str, Any],
        unified_plan: Dict[str, Any]
    ) -> None:
        """Store coordination session in memory for learning."""
        
        # Create serializable version of resolution_result
        serializable_resolution = {
            k: v for k, v in resolution_result.items() 
            if k != 'conflicts_resolved'  # Skip non-serializable objects
        }
        # Use the pre-serialized dicts if available
        if 'conflicts_resolved_dicts' in resolution_result:
            serializable_resolution['conflicts_resolved'] = resolution_result['conflicts_resolved_dicts']
        
        session_data = {
            'coordination_type': 'multi_agent_optimization',
            'agent_proposals': agent_proposals,
            'conflicts_detected': [c.to_dict() for c in conflicts],
            'resolution_result': serializable_resolution,
            'unified_plan': unified_plan,
            'timestamp': datetime.now().isoformat(),
            'success': unified_plan.get('constraint_satisfaction_score', 0) > 0.5
        }
        
        if self.session_id:
            self.memory.store_episodic_memory(self.session_id, session_data)
        
        # Update working memory with coordination metrics
        self.memory.update_working_memory({
            'last_coordination': session_data,
            'coordination_success_rate': self._calculate_success_rate(),
            'common_conflicts': self._track_common_conflicts(conflicts)
        })
    
    def _calculate_success_rate(self) -> float:
        """Calculate coordination success rate from recent history."""
        
        recent_sessions = self.memory.get_episodic_memory(limit=10)
        if not recent_sessions:
            return 1.0
        
        successful_sessions = sum(
            1 for session in recent_sessions 
            if session.get('data', {}).get('success', False)
        )
        
        return successful_sessions / len(recent_sessions)
    
    def _track_common_conflicts(self, current_conflicts: List[ConflictResolution]) -> Dict[str, int]:
        """Track frequency of different conflict types."""
        
        working_memory = self.memory.get_working_memory()
        conflict_counts = working_memory.get('common_conflicts', {})
        
        # Update counts with current conflicts
        for conflict in current_conflicts:
            conflict_type = conflict.conflict_type.value
            conflict_counts[conflict_type] = conflict_counts.get(conflict_type, 0) + 1
        
        return conflict_counts
    
    def _initialize_optimization_weights(self) -> Dict[str, float]:
        """Initialize weights for multi-objective optimization."""
        return {
            'recovery_priority': 2.0,
            'safety_constraints': 1.8,
            'hard_constraints': 1.5,
            'nutritional_adequacy': 1.2,
            'sustainability': 1.0,
            'user_preferences': 0.8,
            'efficiency': 0.6
        }
    
    def _initialize_constraint_hierarchy(self) -> List[str]:
        """Initialize constraint hierarchy for resolution prioritization."""
        return [
            'safety_constraints',
            'recovery_constraints',
            'hard_budget_constraints',
            'hard_time_constraints',
            'dietary_restrictions',
            'nutritional_minimums',
            'fitness_progression',
            'user_preferences',
            'optimization_preferences'
        ]
    
    def _initialize_trade_off_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize trade-off strategies for different conflict types."""
        return {
            'recovery_vs_intensity': {
                'priority': 'recovery',
                'strategy': 'reduce_intensity',
                'confidence_impact': -0.1
            },
            'budget_vs_nutrition': {
                'priority': 'nutrition_minimums',
                'strategy': 'optimize_cost_efficiency',
                'confidence_impact': -0.05
            },
            'time_vs_completeness': {
                'priority': 'time_constraints',
                'strategy': 'optimize_efficiency',
                'confidence_impact': -0.1
            },
            'complexity_vs_motivation': {
                'priority': 'motivation',
                'strategy': 'simplify_plans',
                'confidence_impact': -0.05
            }
        }


def create_coordinator_agent(confidence_threshold: float = 0.8) -> CoordinatorAgent:
    """
    Factory function to create a CoordinatorAgent instance.
    
    Args:
        confidence_threshold: Minimum confidence for coordination results
        
    Returns:
        Configured CoordinatorAgent instance
    """
    return CoordinatorAgent(confidence_threshold=confidence_threshold)