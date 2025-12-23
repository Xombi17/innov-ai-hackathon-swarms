"""
Recovery Prioritization Logic for WellSync AI system.

Implements energy conflict detection and resolution algorithms,
recovery and sustainability prioritization rules, and trade-off
explanation generation for user transparency.
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from wellsync_ai.data.database import get_database_manager


class EnergyConflictType(Enum):
    """Types of energy conflicts in the system."""
    HIGH_DEMAND_LOW_RECOVERY = "high_demand_low_recovery"
    INSUFFICIENT_NUTRITION = "insufficient_nutrition"
    SLEEP_DEBT_ACCUMULATION = "sleep_debt_accumulation"
    OVERTRAINING_RISK = "overtraining_risk"
    STRESS_OVERLOAD = "stress_overload"
    MULTIPLE_STRESSORS = "multiple_stressors"


@dataclass
class EnergyBalance:
    """Represents the current energy balance state."""
    energy_demand: float  # 0-100 scale
    energy_availability: float  # 0-100 scale
    recovery_capacity: float  # 0-100 scale
    stress_load: float  # 0-100 scale
    sustainability_score: float  # 0-100 scale
    balance_status: str  # "deficit", "balanced", "surplus"


@dataclass
class RecoveryPriority:
    """Represents a recovery prioritization decision."""
    priority_level: str  # "critical", "high", "medium", "low"
    affected_domains: List[str]
    interventions: List[str]
    trade_offs: List[str]
    timeline: str  # "immediate", "short_term", "medium_term"
    confidence: float


class RecoveryPrioritizationEngine:
    """
    Engine for detecting energy conflicts and prioritizing recovery.
    
    Implements algorithms for energy balance assessment, conflict detection,
    and recovery prioritization with sustainability focus.
    """
    
    def __init__(self):
        """Initialize recovery prioritization engine."""
        
        # Energy balance thresholds
        self.energy_deficit_threshold = 20  # Below this = energy deficit
        self.recovery_critical_threshold = 30  # Below this = critical recovery need
        self.overtraining_threshold = 80  # Above this = overtraining risk
        self.stress_overload_threshold = 75  # Above this = stress overload
        
        # Recovery prioritization weights
        self.recovery_weights = {
            'sleep_quality': 0.35,
            'training_load': 0.25,
            'stress_level': 0.20,
            'nutrition_adequacy': 0.15,
            'motivation_level': 0.05
        }
        
        # Sustainability factors
        self.sustainability_multipliers = {
            'aggressive': 0.7,  # Aggressive plans are less sustainable
            'moderate': 1.0,    # Moderate plans are baseline
            'conservative': 1.3  # Conservative plans are more sustainable
        }
        
        self.db_manager = get_database_manager()
    
    def assess_energy_balance(
        self,
        agent_proposals: Dict[str, Dict[str, Any]],
        user_data: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> EnergyBalance:
        """
        Assess current energy balance across all wellness domains.
        
        Args:
            agent_proposals: Proposals from all agents
            user_data: Current user data and metrics
            shared_state: Shared state information
            
        Returns:
            EnergyBalance assessment
        """
        
        # Calculate energy demand from fitness agent
        energy_demand = self._calculate_energy_demand(agent_proposals.get('FitnessAgent', {}))
        
        # Calculate energy availability from nutrition and sleep
        energy_availability = self._calculate_energy_availability(
            agent_proposals.get('NutritionAgent', {}),
            agent_proposals.get('SleepAgent', {}),
            user_data
        )
        
        # Calculate recovery capacity
        recovery_capacity = self._calculate_recovery_capacity(
            agent_proposals.get('SleepAgent', {}),
            user_data
        )
        
        # Calculate stress load
        stress_load = self._calculate_stress_load(
            agent_proposals.get('MentalWellnessAgent', {}),
            user_data
        )
        
        # Calculate sustainability score
        sustainability_score = self._calculate_sustainability_score(
            energy_demand, energy_availability, recovery_capacity, stress_load
        )
        
        # Determine balance status
        balance_status = self._determine_balance_status(
            energy_demand, energy_availability, recovery_capacity
        )
        
        return EnergyBalance(
            energy_demand=energy_demand,
            energy_availability=energy_availability,
            recovery_capacity=recovery_capacity,
            stress_load=stress_load,
            sustainability_score=sustainability_score,
            balance_status=balance_status
        )
    
    def detect_energy_conflicts(
        self,
        energy_balance: EnergyBalance,
        agent_proposals: Dict[str, Dict[str, Any]],
        user_data: Dict[str, Any]
    ) -> List[EnergyConflictType]:
        """
        Detect energy conflicts based on energy balance assessment.
        
        Args:
            energy_balance: Current energy balance state
            agent_proposals: Agent proposals
            user_data: User data and metrics
            
        Returns:
            List of detected energy conflicts
        """
        
        conflicts = []
        
        # High demand with low recovery
        if (energy_balance.energy_demand > 70 and 
            energy_balance.recovery_capacity < self.recovery_critical_threshold):
            conflicts.append(EnergyConflictType.HIGH_DEMAND_LOW_RECOVERY)
        
        # Insufficient nutrition for demands
        nutrition_adequacy = self._get_nutrition_adequacy(agent_proposals.get('NutritionAgent', {}))
        if energy_balance.energy_demand > 60 and nutrition_adequacy < 50:
            conflicts.append(EnergyConflictType.INSUFFICIENT_NUTRITION)
        
        # Sleep debt accumulation
        sleep_debt = self._calculate_sleep_debt(user_data)
        if sleep_debt > 2.0:  # More than 2 hours sleep debt
            conflicts.append(EnergyConflictType.SLEEP_DEBT_ACCUMULATION)
        
        # Overtraining risk
        training_load = self._get_training_load(agent_proposals.get('FitnessAgent', {}))
        if training_load > self.overtraining_threshold:
            conflicts.append(EnergyConflictType.OVERTRAINING_RISK)
        
        # Stress overload
        if energy_balance.stress_load > self.stress_overload_threshold:
            conflicts.append(EnergyConflictType.STRESS_OVERLOAD)
        
        # Multiple stressors
        if len(conflicts) >= 2:
            conflicts.append(EnergyConflictType.MULTIPLE_STRESSORS)
        
        return conflicts
    
    def prioritize_recovery(
        self,
        energy_conflicts: List[EnergyConflictType],
        energy_balance: EnergyBalance,
        agent_proposals: Dict[str, Dict[str, Any]],
        user_data: Dict[str, Any]
    ) -> RecoveryPriority:
        """
        Determine recovery prioritization based on conflicts and energy balance.
        
        Args:
            energy_conflicts: Detected energy conflicts
            energy_balance: Current energy balance
            agent_proposals: Agent proposals
            user_data: User data
            
        Returns:
            Recovery prioritization decision
        """
        
        # Determine priority level based on conflicts and balance
        priority_level = self._determine_priority_level(energy_conflicts, energy_balance)
        
        # Identify affected domains
        affected_domains = self._identify_affected_domains(energy_conflicts, agent_proposals)
        
        # Generate interventions
        interventions = self._generate_recovery_interventions(
            energy_conflicts, energy_balance, agent_proposals
        )
        
        # Identify trade-offs
        trade_offs = self._identify_recovery_trade_offs(
            energy_conflicts, interventions, agent_proposals
        )
        
        # Determine timeline
        timeline = self._determine_recovery_timeline(priority_level, energy_conflicts)
        
        # Calculate confidence
        confidence = self._calculate_recovery_confidence(
            energy_balance, len(energy_conflicts), interventions
        )
        
        return RecoveryPriority(
            priority_level=priority_level,
            affected_domains=affected_domains,
            interventions=interventions,
            trade_offs=trade_offs,
            timeline=timeline,
            confidence=confidence
        )
    
    def generate_trade_off_explanations(
        self,
        recovery_priority: RecoveryPriority,
        energy_balance: EnergyBalance,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate detailed explanations of recovery trade-offs for user transparency.
        
        Args:
            recovery_priority: Recovery prioritization decision
            energy_balance: Current energy balance
            agent_proposals: Agent proposals
            
        Returns:
            Detailed trade-off explanations
        """
        
        explanations = {
            'recovery_rationale': self._explain_recovery_rationale(recovery_priority, energy_balance),
            'domain_impacts': self._explain_domain_impacts(recovery_priority, agent_proposals),
            'trade_off_details': self._explain_trade_off_details(recovery_priority),
            'sustainability_benefits': self._explain_sustainability_benefits(recovery_priority),
            'timeline_explanation': self._explain_timeline_rationale(recovery_priority),
            'confidence_factors': self._explain_confidence_factors(recovery_priority, energy_balance)
        }
        
        return explanations
    
    def _calculate_energy_demand(self, fitness_proposal: Dict[str, Any]) -> float:
        """Calculate energy demand from fitness proposal."""
        
        energy_demand_map = {
            'low': 30,
            'medium': 60,
            'high': 90
        }
        
        energy_demand_str = fitness_proposal.get('energy_demand', 'medium')
        base_demand = energy_demand_map.get(energy_demand_str, 60)
        
        # Adjust based on training load if available
        training_load = fitness_proposal.get('training_load_score', 50)
        adjustment = (training_load - 50) * 0.4  # Scale adjustment
        
        return max(0, min(100, base_demand + adjustment))
    
    def _calculate_energy_availability(
        self,
        nutrition_proposal: Dict[str, Any],
        sleep_proposal: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> float:
        """Calculate energy availability from nutrition and sleep."""
        
        # Nutrition contribution (60% of availability)
        nutrition_adequacy_map = {
            'low': 20,
            'medium': 60,
            'high': 90
        }
        
        nutrition_adequacy = nutrition_proposal.get('nutritional_adequacy', 'medium')
        nutrition_score = nutrition_adequacy_map.get(nutrition_adequacy, 60)
        
        # Sleep contribution (40% of availability)
        recovery_status_map = {
            'poor': 20,
            'fair': 50,
            'good': 80,
            'excellent': 95
        }
        
        recovery_status = sleep_proposal.get('recovery_status', 'fair')
        sleep_score = recovery_status_map.get(recovery_status, 50)
        
        # Weighted combination
        availability = (nutrition_score * 0.6) + (sleep_score * 0.4)
        
        return max(0, min(100, availability))
    
    def _calculate_recovery_capacity(
        self,
        sleep_proposal: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> float:
        """Calculate recovery capacity based on sleep and stress indicators."""
        
        # Base recovery from sleep status
        recovery_status_map = {
            'poor': 25,
            'fair': 50,
            'good': 75,
            'excellent': 95
        }
        
        recovery_status = sleep_proposal.get('recovery_status', 'fair')
        base_recovery = recovery_status_map.get(recovery_status, 50)
        
        # Adjust for sleep debt
        sleep_debt = self._calculate_sleep_debt(user_data)
        sleep_debt_penalty = min(30, sleep_debt * 10)  # 10 points per hour of debt, max 30
        
        # Adjust for stress indicators
        stress_indicators = user_data.get('stress_indicators', {})
        stress_penalty = self._calculate_stress_penalty(stress_indicators)
        
        recovery_capacity = base_recovery - sleep_debt_penalty - stress_penalty
        
        return max(0, min(100, recovery_capacity))
    
    def _calculate_stress_load(
        self,
        mental_wellness_proposal: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> float:
        """Calculate current stress load."""
        
        # Base stress from motivation level (inverse relationship)
        motivation_level_map = {
            'low': 70,    # Low motivation = high stress
            'medium': 40,
            'high': 20    # High motivation = low stress
        }
        
        motivation_level = mental_wellness_proposal.get('motivation_level', 'medium')
        base_stress = motivation_level_map.get(motivation_level, 40)
        
        # Add stress from external factors
        stress_indicators = user_data.get('stress_indicators', {})
        external_stress = self._calculate_external_stress(stress_indicators)
        
        total_stress = base_stress + external_stress
        
        return max(0, min(100, total_stress))
    
    def _calculate_sustainability_score(
        self,
        energy_demand: float,
        energy_availability: float,
        recovery_capacity: float,
        stress_load: float
    ) -> float:
        """Calculate sustainability score for current plan."""
        
        # Energy balance factor
        energy_balance = energy_availability - energy_demand
        balance_factor = max(0, min(100, 50 + energy_balance))
        
        # Recovery adequacy factor
        recovery_factor = recovery_capacity
        
        # Stress management factor
        stress_factor = 100 - stress_load
        
        # Weighted combination
        sustainability = (
            balance_factor * 0.4 +
            recovery_factor * 0.35 +
            stress_factor * 0.25
        )
        
        return max(0, min(100, sustainability))
    
    def _determine_balance_status(
        self,
        energy_demand: float,
        energy_availability: float,
        recovery_capacity: float
    ) -> str:
        """Determine energy balance status."""
        
        balance = energy_availability - energy_demand
        
        if balance < -20 or recovery_capacity < self.recovery_critical_threshold:
            return "deficit"
        elif balance > 20 and recovery_capacity > 70:
            return "surplus"
        else:
            return "balanced"
    
    def _get_nutrition_adequacy(self, nutrition_proposal: Dict[str, Any]) -> float:
        """Get nutrition adequacy score."""
        adequacy_map = {
            'low': 30,
            'medium': 65,
            'high': 90
        }
        
        adequacy = nutrition_proposal.get('nutritional_adequacy', 'medium')
        return adequacy_map.get(adequacy, 65)
    
    def _calculate_sleep_debt(self, user_data: Dict[str, Any]) -> float:
        """Calculate accumulated sleep debt in hours."""
        
        sleep_data = user_data.get('recent_data', {}).get('sleep', {})
        
        # Get recent sleep hours (last 7 days)
        recent_sleep = sleep_data.get('daily_hours', [])
        if not recent_sleep:
            return 0.0
        
        # Calculate debt based on 8-hour target
        target_hours = 8.0
        total_debt = 0.0
        
        for daily_hours in recent_sleep[-7:]:  # Last 7 days
            if daily_hours < target_hours:
                total_debt += (target_hours - daily_hours)
        
        return total_debt
    
    def _get_training_load(self, fitness_proposal: Dict[str, Any]) -> float:
        """Get training load score."""
        return fitness_proposal.get('training_load_score', 50)
    
    def _calculate_stress_penalty(self, stress_indicators: Dict[str, Any]) -> float:
        """Calculate stress penalty for recovery capacity."""
        
        penalty = 0.0
        
        # Work stress
        work_stress = stress_indicators.get('work_stress_level', 0)  # 0-10 scale
        penalty += work_stress * 2  # Up to 20 points
        
        # Life stress
        life_stress = stress_indicators.get('life_stress_level', 0)  # 0-10 scale
        penalty += life_stress * 1.5  # Up to 15 points
        
        # Health concerns
        health_concerns = stress_indicators.get('health_concerns', False)
        if health_concerns:
            penalty += 10
        
        return min(penalty, 40)  # Cap at 40 points
    
    def _calculate_external_stress(self, stress_indicators: Dict[str, Any]) -> float:
        """Calculate external stress contribution."""
        
        stress = 0.0
        
        # Work-related stress
        work_stress = stress_indicators.get('work_stress_level', 0)  # 0-10 scale
        stress += work_stress * 3  # Up to 30 points
        
        # Relationship stress
        relationship_stress = stress_indicators.get('relationship_stress', 0)  # 0-10 scale
        stress += relationship_stress * 2  # Up to 20 points
        
        # Financial stress
        financial_stress = stress_indicators.get('financial_stress', 0)  # 0-10 scale
        stress += financial_stress * 2.5  # Up to 25 points
        
        return min(stress, 60)  # Cap at 60 points
    
    def _determine_priority_level(
        self,
        energy_conflicts: List[EnergyConflictType],
        energy_balance: EnergyBalance
    ) -> str:
        """Determine recovery priority level."""
        
        # Critical priority conditions
        if (EnergyConflictType.MULTIPLE_STRESSORS in energy_conflicts or
            energy_balance.recovery_capacity < 25 or
            energy_balance.sustainability_score < 30):
            return "critical"
        
        # High priority conditions
        if (len(energy_conflicts) >= 2 or
            EnergyConflictType.HIGH_DEMAND_LOW_RECOVERY in energy_conflicts or
            EnergyConflictType.OVERTRAINING_RISK in energy_conflicts or
            energy_balance.balance_status == "deficit"):
            return "high"
        
        # Medium priority conditions
        if (len(energy_conflicts) == 1 or
            energy_balance.recovery_capacity < 50 or
            energy_balance.sustainability_score < 60):
            return "medium"
        
        # Low priority (maintenance)
        return "low"
    
    def _identify_affected_domains(
        self,
        energy_conflicts: List[EnergyConflictType],
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Identify wellness domains affected by recovery prioritization."""
        
        affected = set()
        
        # Always affected by recovery prioritization
        affected.add("sleep")
        
        # Fitness affected by most conflicts
        fitness_affecting_conflicts = [
            EnergyConflictType.HIGH_DEMAND_LOW_RECOVERY,
            EnergyConflictType.OVERTRAINING_RISK,
            EnergyConflictType.MULTIPLE_STRESSORS
        ]
        
        if any(conflict in energy_conflicts for conflict in fitness_affecting_conflicts):
            affected.add("fitness")
        
        # Nutrition affected by energy availability issues
        nutrition_affecting_conflicts = [
            EnergyConflictType.INSUFFICIENT_NUTRITION,
            EnergyConflictType.HIGH_DEMAND_LOW_RECOVERY
        ]
        
        if any(conflict in energy_conflicts for conflict in nutrition_affecting_conflicts):
            affected.add("nutrition")
        
        # Mental wellness affected by stress-related conflicts
        stress_affecting_conflicts = [
            EnergyConflictType.STRESS_OVERLOAD,
            EnergyConflictType.MULTIPLE_STRESSORS
        ]
        
        if any(conflict in energy_conflicts for conflict in stress_affecting_conflicts):
            affected.add("mental_wellness")
        
        return list(affected)
    
    def _generate_recovery_interventions(
        self,
        energy_conflicts: List[EnergyConflictType],
        energy_balance: EnergyBalance,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate specific recovery interventions."""
        
        interventions = []
        
        # Sleep-focused interventions
        if (EnergyConflictType.SLEEP_DEBT_ACCUMULATION in energy_conflicts or
            energy_balance.recovery_capacity < 40):
            interventions.extend([
                "Prioritize sleep duration (aim for 8+ hours nightly)",
                "Implement consistent sleep schedule",
                "Optimize sleep environment for quality"
            ])
        
        # Training load interventions
        if (EnergyConflictType.HIGH_DEMAND_LOW_RECOVERY in energy_conflicts or
            EnergyConflictType.OVERTRAINING_RISK in energy_conflicts):
            interventions.extend([
                "Reduce training intensity by 20-30%",
                "Add extra rest day between intense sessions",
                "Focus on active recovery activities"
            ])
        
        # Nutrition interventions
        if EnergyConflictType.INSUFFICIENT_NUTRITION in energy_conflicts:
            interventions.extend([
                "Increase caloric intake to match energy demands",
                "Optimize pre/post workout nutrition timing",
                "Ensure adequate protein for recovery"
            ])
        
        # Stress management interventions
        if (EnergyConflictType.STRESS_OVERLOAD in energy_conflicts or
            energy_balance.stress_load > 70):
            interventions.extend([
                "Implement stress reduction techniques",
                "Simplify wellness plan complexity",
                "Consider meditation or relaxation practices"
            ])
        
        # Multiple stressor interventions
        if EnergyConflictType.MULTIPLE_STRESSORS in energy_conflicts:
            interventions.extend([
                "Implement comprehensive recovery protocol",
                "Temporarily reduce all wellness demands",
                "Focus on basic health maintenance only"
            ])
        
        return interventions
    
    def _identify_recovery_trade_offs(
        self,
        energy_conflicts: List[EnergyConflictType],
        interventions: List[str],
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Identify trade-offs made for recovery prioritization."""
        
        trade_offs = []
        
        # Fitness trade-offs
        fitness_proposal = agent_proposals.get('FitnessAgent', {})
        if fitness_proposal.get('energy_demand') == 'high':
            trade_offs.append("Reduced fitness intensity for recovery prioritization")
            trade_offs.append("Delayed fitness progression to ensure sustainability")
        
        # Nutrition trade-offs
        nutrition_proposal = agent_proposals.get('NutritionAgent', {})
        if nutrition_proposal.get('budget_utilization', 0) > 0.8:
            trade_offs.append("May require increased food budget for adequate nutrition")
        
        # Time trade-offs
        if "sleep duration" in str(interventions).lower():
            trade_offs.append("Increased sleep time may reduce available time for other activities")
        
        # Complexity trade-offs
        if "simplify" in str(interventions).lower():
            trade_offs.append("Simplified plans may progress more slowly toward goals")
        
        # Goal timeline trade-offs
        if len(energy_conflicts) >= 2:
            trade_offs.append("Extended timeline for achieving wellness goals")
            trade_offs.append("Focus on sustainability over aggressive optimization")
        
        return trade_offs
    
    def _determine_recovery_timeline(
        self,
        priority_level: str,
        energy_conflicts: List[EnergyConflictType]
    ) -> str:
        """Determine timeline for recovery interventions."""
        
        if priority_level == "critical":
            return "immediate"
        elif priority_level == "high":
            return "short_term"  # 1-2 weeks
        elif priority_level == "medium":
            return "medium_term"  # 2-4 weeks
        else:
            return "ongoing"  # Maintenance
    
    def _calculate_recovery_confidence(
        self,
        energy_balance: EnergyBalance,
        conflict_count: int,
        interventions: List[str]
    ) -> float:
        """Calculate confidence in recovery prioritization decision."""
        
        base_confidence = 0.8
        
        # Reduce confidence for multiple conflicts
        conflict_penalty = min(0.3, conflict_count * 0.1)
        
        # Reduce confidence for severe energy imbalance
        if energy_balance.balance_status == "deficit":
            balance_penalty = 0.1
        else:
            balance_penalty = 0.0
        
        # Increase confidence for comprehensive interventions
        intervention_bonus = min(0.2, len(interventions) * 0.02)
        
        confidence = base_confidence - conflict_penalty - balance_penalty + intervention_bonus
        
        return max(0.3, min(1.0, confidence))
    
    def _explain_recovery_rationale(
        self,
        recovery_priority: RecoveryPriority,
        energy_balance: EnergyBalance
    ) -> str:
        """Explain the rationale for recovery prioritization."""
        
        rationale_parts = []
        
        # Priority level explanation
        if recovery_priority.priority_level == "critical":
            rationale_parts.append("Critical recovery prioritization due to severe energy imbalance")
        elif recovery_priority.priority_level == "high":
            rationale_parts.append("High recovery priority to prevent overtraining and maintain sustainability")
        else:
            rationale_parts.append("Moderate recovery focus to optimize long-term wellness outcomes")
        
        # Energy balance explanation
        if energy_balance.balance_status == "deficit":
            rationale_parts.append(f"Current energy deficit (demand: {energy_balance.energy_demand:.0f}, availability: {energy_balance.energy_availability:.0f})")
        
        # Recovery capacity explanation
        if energy_balance.recovery_capacity < 50:
            rationale_parts.append(f"Limited recovery capacity ({energy_balance.recovery_capacity:.0f}/100) requires intervention")
        
        # Sustainability explanation
        if energy_balance.sustainability_score < 60:
            rationale_parts.append(f"Low sustainability score ({energy_balance.sustainability_score:.0f}/100) indicates unsustainable current trajectory")
        
        return ". ".join(rationale_parts) + "."
    
    def _explain_domain_impacts(
        self,
        recovery_priority: RecoveryPriority,
        agent_proposals: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Explain how recovery prioritization impacts each domain."""
        
        impacts = {}
        
        for domain in recovery_priority.affected_domains:
            if domain == "fitness":
                impacts["fitness"] = "Training intensity reduced to allow for adequate recovery and prevent overtraining"
            elif domain == "nutrition":
                impacts["nutrition"] = "Nutrition plan optimized to support recovery and energy availability"
            elif domain == "sleep":
                impacts["sleep"] = "Sleep prioritized as the foundation for all other wellness activities"
            elif domain == "mental_wellness":
                impacts["mental_wellness"] = "Plan complexity reduced to match current motivation and stress capacity"
        
        return impacts
    
    def _explain_trade_off_details(self, recovery_priority: RecoveryPriority) -> List[Dict[str, str]]:
        """Provide detailed explanations of each trade-off."""
        
        trade_off_details = []
        
        for trade_off in recovery_priority.trade_offs:
            if "fitness intensity" in trade_off.lower():
                trade_off_details.append({
                    "trade_off": trade_off,
                    "rationale": "Reduced intensity prevents overtraining and allows for better adaptation",
                    "benefit": "Improved long-term progress and reduced injury risk"
                })
            elif "food budget" in trade_off.lower():
                trade_off_details.append({
                    "trade_off": trade_off,
                    "rationale": "Adequate nutrition is essential for recovery and energy availability",
                    "benefit": "Better energy levels and training adaptation"
                })
            elif "sleep time" in trade_off.lower():
                trade_off_details.append({
                    "trade_off": trade_off,
                    "rationale": "Sleep is the most important recovery intervention",
                    "benefit": "Improved recovery, energy, and overall wellness outcomes"
                })
            else:
                trade_off_details.append({
                    "trade_off": trade_off,
                    "rationale": "Supports overall recovery and sustainability",
                    "benefit": "Better long-term wellness outcomes"
                })
        
        return trade_off_details
    
    def _explain_sustainability_benefits(self, recovery_priority: RecoveryPriority) -> List[str]:
        """Explain sustainability benefits of recovery prioritization."""
        
        benefits = [
            "Prevents burnout and overtraining syndrome",
            "Maintains consistent progress over time",
            "Reduces risk of injury and setbacks",
            "Improves adherence to wellness plans",
            "Supports long-term habit formation"
        ]
        
        # Add priority-specific benefits
        if recovery_priority.priority_level in ["critical", "high"]:
            benefits.extend([
                "Prevents need for extended recovery periods",
                "Maintains motivation and engagement"
            ])
        
        return benefits
    
    def _explain_timeline_rationale(self, recovery_priority: RecoveryPriority) -> str:
        """Explain the rationale for the recovery timeline."""
        
        timeline_explanations = {
            "immediate": "Immediate intervention required to prevent further deterioration",
            "short_term": "Short-term focus needed to restore energy balance within 1-2 weeks",
            "medium_term": "Medium-term approach allows gradual improvement over 2-4 weeks",
            "ongoing": "Ongoing maintenance approach for sustained wellness"
        }
        
        return timeline_explanations.get(recovery_priority.timeline, "Timeline based on current recovery needs")
    
    def _explain_confidence_factors(
        self,
        recovery_priority: RecoveryPriority,
        energy_balance: EnergyBalance
    ) -> Dict[str, str]:
        """Explain factors affecting confidence in recovery prioritization."""
        
        factors = {}
        
        # Confidence level explanation
        if recovery_priority.confidence > 0.8:
            factors["confidence_level"] = "High confidence based on clear indicators and established interventions"
        elif recovery_priority.confidence > 0.6:
            factors["confidence_level"] = "Moderate confidence with some uncertainty in outcomes"
        else:
            factors["confidence_level"] = "Lower confidence due to complex interactions and multiple variables"
        
        # Data quality factors
        factors["data_quality"] = "Based on current energy balance assessment and agent proposals"
        
        # Intervention effectiveness
        factors["intervention_track_record"] = "Interventions based on established recovery science principles"
        
        return factors


def create_recovery_prioritization_engine() -> RecoveryPrioritizationEngine:
    """
    Factory function to create a RecoveryPrioritizationEngine instance.
    
    Returns:
        Configured RecoveryPrioritizationEngine instance
    """
    return RecoveryPrioritizationEngine()