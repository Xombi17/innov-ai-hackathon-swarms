"""
Nutrition Swarm Module - Hierarchical Multi-Agent Nutrition Decision System.

Implements a Swarms-style HierarchicalSwarm with:
- NutritionManager (Manager role)
- ConstraintBudgetAnalyst (Worker)
- AvailabilityMapper (Worker)
- PreferenceFatigueModeler (Worker)
- RecoveryTimingAdvisor (Worker)
"""

from wellsync_ai.agents.nutrition_swarm.constraint_budget_analyst import ConstraintBudgetAnalyst
from wellsync_ai.agents.nutrition_swarm.availability_mapper import AvailabilityMapper
from wellsync_ai.agents.nutrition_swarm.preference_fatigue_modeler import PreferenceFatigueModeler
from wellsync_ai.agents.nutrition_swarm.recovery_timing_advisor import RecoveryTimingAdvisor
from wellsync_ai.agents.nutrition_swarm.nutrition_manager import NutritionManager

__all__ = [
    'NutritionManager',
    'ConstraintBudgetAnalyst',
    'AvailabilityMapper',
    'PreferenceFatigueModeler',
    'RecoveryTimingAdvisor'
]
