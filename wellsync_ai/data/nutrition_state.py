"""
Nutrition State Management.

Explicit state tracking for the nutrition decision loop:
- Budget: spent, remaining, billing cycle
- Availability: today's menu, nearby options, cooking access
- History: last N meals, rejections, fatigue score
- Execution: skipped meals, late meals, substitutions
- Signals: fitness/recovery priorities
- Targets: loose macros/quality goals
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum

from wellsync_ai.data.database import get_database_manager
from wellsync_ai.data.redis_client import get_redis_manager


class BudgetCycleType(Enum):
    """Budget cycle types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class BudgetState:
    """Budget tracking state."""
    cycle_type: str = "daily"
    cycle_start_date: str = ""
    total_budget: float = 500.0
    spent: float = 0.0
    remaining: float = 500.0
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_expense(self, amount: float, description: str = "") -> None:
        """Record an expense."""
        self.spent += amount
        self.remaining = self.total_budget - self.spent
        self.transactions.append({
            "amount": amount,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
    
    def reset_cycle(self) -> None:
        """Reset for new budget cycle."""
        self.spent = 0.0
        self.remaining = self.total_budget
        self.transactions = []
        self.cycle_start_date = datetime.now().strftime('%Y-%m-%d')


@dataclass
class AvailabilityState:
    """Food availability state."""
    todays_menu: Dict[str, List[str]] = field(default_factory=dict)
    nearby_options: List[Dict[str, Any]] = field(default_factory=list)
    has_cooking_access: bool = False
    available_ingredients: List[str] = field(default_factory=list)
    last_updated: str = ""
    
    def update_menu(self, menu: Dict[str, List[str]]) -> None:
        """Update today's menu."""
        self.todays_menu = menu
        self.last_updated = datetime.now().isoformat()


@dataclass
class MealHistoryState:
    """Meal history and fatigue tracking."""
    recent_meals: List[Dict[str, Any]] = field(default_factory=list)
    rejections: List[Dict[str, Any]] = field(default_factory=list)
    item_frequency: Dict[str, int] = field(default_factory=dict)
    fatigue_scores: Dict[str, float] = field(default_factory=dict)
    cooldown_list: List[str] = field(default_factory=list)
    
    def add_meal(self, meal: Dict[str, Any]) -> None:
        """Record a consumed meal."""
        meal['timestamp'] = datetime.now().isoformat()
        self.recent_meals.append(meal)
        
        # Keep only last 30 meals
        if len(self.recent_meals) > 30:
            self.recent_meals = self.recent_meals[-30:]
        
        # Update frequency
        for item in meal.get('items', []):
            item_name = item.get('name', item) if isinstance(item, dict) else item
            self.item_frequency[item_name] = self.item_frequency.get(item_name, 0) + 1
    
    def add_rejection(self, item: str, reason: str = "") -> None:
        """Record a rejected item."""
        self.rejections.append({
            "item": item,
            "reason": reason,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "timestamp": datetime.now().isoformat()
        })
        
        # Add to cooldown
        if item not in self.cooldown_list:
            self.cooldown_list.append(item)
    
    def calculate_fatigue(self) -> None:
        """Recalculate fatigue scores based on frequency."""
        for item, freq in self.item_frequency.items():
            # Fatigue increases with frequency
            if freq <= 2:
                self.fatigue_scores[item] = 0.0
            elif freq <= 4:
                self.fatigue_scores[item] = 0.3
            elif freq <= 6:
                self.fatigue_scores[item] = 0.6
            else:
                self.fatigue_scores[item] = min(1.0, 0.6 + (freq - 6) * 0.1)


@dataclass
class ExecutionState:
    """Meal execution tracking."""
    skipped_meals: List[Dict[str, Any]] = field(default_factory=list)
    late_meals: List[Dict[str, Any]] = field(default_factory=list)
    substitutions_made: List[Dict[str, Any]] = field(default_factory=list)
    compliance_score: float = 1.0
    
    def record_skip(self, meal_type: str, reason: str = "") -> None:
        """Record a skipped meal."""
        self.skipped_meals.append({
            "meal_type": meal_type,
            "reason": reason,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "timestamp": datetime.now().isoformat()
        })
        self._update_compliance()
    
    def record_substitution(self, original: str, substitute: str, reason: str = "") -> None:
        """Record a substitution made."""
        self.substitutions_made.append({
            "original": original,
            "substitute": substitute,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
    
    def _update_compliance(self) -> None:
        """Update compliance score based on recent execution."""
        # Simple decay: each skip in last 7 days reduces score
        recent_skips = [s for s in self.skipped_meals 
                       if datetime.fromisoformat(s['timestamp']) > datetime.now() - timedelta(days=7)]
        self.compliance_score = max(0.0, 1.0 - (len(recent_skips) * 0.1))


@dataclass
class SignalsState:
    """External signals affecting nutrition."""
    fitness_priority: str = "normal"  # recovery, performance, normal
    workout_completed: bool = False
    workout_intensity: str = "moderate"
    sleep_quality: str = "good"
    energy_level: str = "moderate"
    stress_level: str = "normal"
    hydration_status: str = "adequate"
    
    def update_from_fitness(self, fitness_data: Dict[str, Any]) -> None:
        """Update signals from fitness agent data."""
        self.workout_completed = fitness_data.get('workout_completed', False)
        self.workout_intensity = fitness_data.get('intensity', 'moderate')
        self.fitness_priority = fitness_data.get('nutrition_priority', 'normal')


@dataclass
class NutritionalTargets:
    """Nutritional targets (flexible, range-based)."""
    calorie_min: int = 1800
    calorie_max: int = 2200
    protein_min: int = 80
    protein_max: int = 120
    carb_ratio: float = 0.45  # As fraction of calories
    fat_ratio: float = 0.30
    fiber_min: int = 25
    water_liters: float = 2.5
    
    def get_target_summary(self) -> Dict[str, Any]:
        """Get summary of targets."""
        return {
            "calories": f"{self.calorie_min}-{self.calorie_max} kcal",
            "protein": f"{self.protein_min}-{self.protein_max}g",
            "fiber": f">{self.fiber_min}g",
            "water": f"{self.water_liters}L"
        }


class NutritionState:
    """
    Complete nutrition state for decision loop.
    
    Implements the state structure:
    - Budget: spent, remaining, billing cycle
    - Availability: today's menu, nearby options, cooking access
    - History: last N meals, rejections, fatigue score
    - Execution: skipped meals, late meals, substitutions
    - Signals: fitness/recovery priorities
    - Targets: loose macros/quality goals
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state_id = f"nutrition_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # State components
        self.budget = BudgetState()
        self.availability = AvailabilityState()
        self.history = MealHistoryState()
        self.execution = ExecutionState()
        self.signals = SignalsState()
        self.targets = NutritionalTargets()
        
        # Metadata
        self.created_at = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()
        
        # Storage managers
        self.db_manager = get_database_manager()
        self.redis_manager = get_redis_manager()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "user_id": self.user_id,
            "state_id": self.state_id,
            "budget": asdict(self.budget),
            "availability": asdict(self.availability),
            "history": asdict(self.history),
            "execution": asdict(self.execution),
            "signals": asdict(self.signals),
            "targets": asdict(self.targets),
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    def get_decision_context(self) -> Dict[str, Any]:
        """Get context for nutrition decision making."""
        return {
            "budget_remaining": self.budget.remaining,
            "budget_status": "ok" if self.budget.remaining > 100 else "tight",
            "meals_today": len([m for m in self.history.recent_meals 
                               if m.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))]),
            "high_fatigue_items": [item for item, score in self.history.fatigue_scores.items() if score > 0.6],
            "cooldown_items": self.history.cooldown_list,
            "fitness_priority": self.signals.fitness_priority,
            "compliance_score": self.execution.compliance_score,
            "targets": self.targets.get_target_summary()
        }
    
    def save(self) -> bool:
        """Persist state to storage."""
        self.last_updated = datetime.now().isoformat()
        state_dict = self.to_dict()
        
        try:
            # Save to Redis for real-time access
            self.redis_manager.set_shared_state(
                self.state_id,
                state_dict,
                ttl=86400  # 24 hours
            )
            
            # Save to SQLite for persistence
            self.db_manager.store_shared_state(state_dict)
            
            return True
        except Exception as e:
            print(f"Failed to save nutrition state: {e}")
            return False
    
    @classmethod
    def load(cls, user_id: str) -> Optional['NutritionState']:
        """Load state from storage."""
        state_id = f"nutrition_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        redis_manager = get_redis_manager()
        
        state_data = redis_manager.get_shared_state(state_id)
        if state_data:
            instance = cls(user_id)
            instance._load_from_dict(state_data)
            return instance
        
        return None
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load state from dictionary."""
        if 'budget' in data:
            self.budget = BudgetState(**data['budget'])
        if 'availability' in data:
            self.availability = AvailabilityState(**data['availability'])
        if 'history' in data:
            self.history = MealHistoryState(**data['history'])
        if 'execution' in data:
            self.execution = ExecutionState(**data['execution'])
        if 'signals' in data:
            self.signals = SignalsState(**data['signals'])
        if 'targets' in data:
            self.targets = NutritionalTargets(**data['targets'])


def get_nutrition_state(user_id: str) -> NutritionState:
    """Get or create nutrition state for user."""
    state = NutritionState.load(user_id)
    if state is None:
        state = NutritionState(user_id)
        state.save()
    return state
