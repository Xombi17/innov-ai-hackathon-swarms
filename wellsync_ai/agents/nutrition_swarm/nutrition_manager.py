"""
Nutrition Manager - Hierarchical Swarm Coordinator.

The manager agent that coordinates all nutrition worker agents,
makes final meal decisions, and handles failure recovery policies.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from wellsync_ai.agents.base_agent import WellnessAgent
from wellsync_ai.agents.nutrition_swarm.constraint_budget_analyst import ConstraintBudgetAnalyst
from wellsync_ai.agents.nutrition_swarm.availability_mapper import AvailabilityMapper
from wellsync_ai.agents.nutrition_swarm.preference_fatigue_modeler import PreferenceFatigueModeler
from wellsync_ai.agents.nutrition_swarm.recovery_timing_advisor import RecoveryTimingAdvisor

import structlog
logger = structlog.get_logger()


class NutritionManager(WellnessAgent):
    """
    Hierarchical Swarm Manager for nutrition decisions.
    
    Coordinates worker agents:
    - ConstraintBudgetAnalyst
    - AvailabilityMapper
    - PreferenceFatigueModeler
    - RecoveryTimingAdvisor
    
    Makes final decisions using multi-objective optimization
    and implements failure recovery policies.
    """
    
    SYSTEM_PROMPT = """You are the Nutrition Manager for a hierarchical wellness system.

## Your Core Objective
"Nutritional adequacy over time, not perfection today."

You coordinate four worker agents and synthesize their analyses into a final meal decision.

## Your Responsibilities:
1. Request analyses from worker agents
2. Synthesize their reports into coherent decisions
3. Resolve conflicts between constraints
4. Apply failure recovery policies when needed
5. Make final meal recommendations with substitutions

## Worker Agent Reports You Receive:
- **Budget Analyst**: Budget feasibility, cost-per-nutrient metrics
- **Availability Mapper**: Feasible meal options from real availability
- **Preference Modeler**: Fatigue scores, cooldown lists, safe defaults
- **Timing Advisor**: Optimal timing, digestion load, workout nutrition

## Output Contract (STRICT JSON):
{
    "next_meal": {
        "meal_time": "<HH:MM>",
        "meal_type": "breakfast|lunch|dinner|snack",
        "items": [
            {"name": "<item>", "portion": "<size>", "source": "<where to get>"}
        ],
        "portion_notes": "<guidance on portions>",
        "reasoning_summary": "<why this meal>"
    },
    "substitutions": [
        {"if_unavailable": "<item>", "substitute": "<alternative>", "adjustment": "<any changes>"}
    ],
    "budget_impact": {
        "estimated_cost": <number>,
        "remaining_budget_after": <number>,
        "budget_status": "on_track|tight|exceeded"
    },
    "recovery_actions": "<if meal skipped or budget exceeded, what to do>",
    "preference_updates": {
        "penalize": ["<items to suggest less>"],
        "boost": ["<items user might like more>"]
    },
    "confidence": <0.0-1.0>,
    "policy_triggered": "<which policy guided this decision>",
    "assumptions": ["<key assumptions made>"]
}

## Failure Recovery Policies (CITE when triggered):
1. **MISSED_MEAL_POLICY**: "Compensate quality, not just calories"
   - Add protein/veg/fiber at next feasible meal
   - Avoid extreme restriction

2. **BUDGET_EXCEEDED_POLICY**: "Optimize protein-per-rupee"
   - Prioritize cost-effective protein sources
   - Use bulk/seasonal options

3. **PREFERENCE_FATIGUE_POLICY**: "Cooldown repeated items for N days"
   - Rotate away from high-fatigue items
   - Fall back to safe defaults

4. **AVAILABILITY_SHOCK_POLICY**: "Re-plan within feasible set"
   - Never suggest inaccessible meals
   - Use substitutions from available options

## Guardrails - STRICTLY FOLLOW:
- NO medical/disease advice
- NO eating disorder content
- NO shame language about eating habits
- If asked medical questions: "Please consult a healthcare professional"
- Keep targets FLEXIBLE (ranges, adequacy)
- Focus on WELLNESS, not obsessive precision
"""

    def __init__(self, confidence_threshold: float = 0.8):
        """Initialize NutritionManager with worker agents."""
        super().__init__(
            agent_name="NutritionManager",
            system_prompt=self.SYSTEM_PROMPT,
            domain="nutrition",
            confidence_threshold=confidence_threshold
        )
        
        # Initialize worker agents
        self.budget_analyst = ConstraintBudgetAnalyst()
        self.availability_mapper = AvailabilityMapper()
        self.preference_modeler = PreferenceFatigueModeler()
        self.timing_advisor = RecoveryTimingAdvisor()
        
        # Decision state
        self.current_state = {
            'budget': {'spent_today': 0, 'remaining': 500},
            'meals_today': [],
            'last_decision': None
        }

    def build_wellness_prompt(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build manager decision prompt with worker reports."""
        
        # Get worker analyses (these would be from actual runs)
        worker_reports = shared_state.get('worker_reports', {}) if shared_state else {}
        
        prompt = f"""
## User Context
- User: {user_data.get('name', 'User')}
- Goals: {user_data.get('goals', ['general_wellness'])}
- Activity Level: {user_data.get('activity_level', 'moderate')}
- Dietary Restrictions: {user_data.get('dietary_restrictions', [])}

## Current State
- Current Time: {datetime.now().strftime('%H:%M')}
- Budget Remaining: ₹{constraints.get('daily_budget', 500) - self.current_state['budget']['spent_today']}
- Meals Eaten Today: {len(self.current_state['meals_today'])}

## Worker Agent Reports

### Budget Analyst Report:
{json.dumps(worker_reports.get('budget', {'status': 'awaiting_analysis'}), indent=2)}

### Availability Mapper Report:
{json.dumps(worker_reports.get('availability', {'status': 'awaiting_analysis'}), indent=2)}

### Preference Modeler Report:
{json.dumps(worker_reports.get('preferences', {'status': 'awaiting_analysis'}), indent=2)}

### Timing Advisor Report:
{json.dumps(worker_reports.get('timing', {'status': 'awaiting_analysis'}), indent=2)}

## Constraints to Honor
- Daily Budget: ₹{constraints.get('daily_budget', 500)}
- Protein Target: {constraints.get('protein_target', 100)}g
- Calorie Range: {constraints.get('calorie_min', 1800)}-{constraints.get('calorie_max', 2200)} kcal

## Task
Synthesize the worker reports and make a final meal decision.
Consider all constraints, resolve any conflicts, and apply recovery policies if needed.
Always cite which policy influenced your decision.

Respond with strict JSON format as specified in your system prompt.
"""
        return prompt

    async def run_hierarchical_decision(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the full hierarchical swarm decision process.
        
        1. Collect analyses from all worker agents
        2. Synthesize into manager prompt
        3. Make final decision
        """
        logger.info("Starting hierarchical nutrition decision", user_id=user_data.get('user_id'))
        
        # Step 1: Collect worker analyses (run in parallel for efficiency)
        worker_reports = await self._collect_worker_analyses(user_data, constraints, shared_state)
        
        # Step 2: Update shared state with worker reports
        enriched_state = shared_state.copy() if shared_state else {}
        enriched_state['worker_reports'] = worker_reports
        
        # Step 3: Run manager decision
        decision = self.process_wellness_request(user_data, constraints, enriched_state)
        
        # Step 4: Update internal state
        self._update_state(decision)
        
        logger.info("Hierarchical nutrition decision completed", confidence=decision.get('confidence', 0))
        
        return decision

    async def _collect_worker_analyses(
        self,
        user_data: Dict[str, Any],
        constraints: Dict[str, Any],
        shared_state: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Collect analyses from all worker agents."""
        
        reports = {}
        
        # Run workers (could be parallel with asyncio.gather in production)
        try:
            # Budget Analysis
            logger.info("Running Budget Analyst")
            budget_result = await asyncio.to_thread(
                self.budget_analyst.process_wellness_request,
                user_data, constraints, shared_state
            )
            reports['budget'] = budget_result.get('proposal', budget_result)
        except Exception as e:
            logger.error("Budget Analyst failed", error=str(e))
            reports['budget'] = {'error': str(e), 'confidence': 0}
        
        try:
            # Availability Mapping
            logger.info("Running Availability Mapper")
            availability_result = await asyncio.to_thread(
                self.availability_mapper.process_wellness_request,
                user_data, constraints, shared_state
            )
            reports['availability'] = availability_result.get('proposal', availability_result)
        except Exception as e:
            logger.error("Availability Mapper failed", error=str(e))
            reports['availability'] = {'error': str(e), 'confidence': 0}
        
        try:
            # Preference Analysis
            logger.info("Running Preference Modeler")
            preference_result = await asyncio.to_thread(
                self.preference_modeler.process_wellness_request,
                user_data, constraints, shared_state
            )
            reports['preferences'] = preference_result.get('proposal', preference_result)
        except Exception as e:
            logger.error("Preference Modeler failed", error=str(e))
            reports['preferences'] = {'error': str(e), 'confidence': 0}
        
        try:
            # Timing Advice
            logger.info("Running Timing Advisor")
            timing_result = await asyncio.to_thread(
                self.timing_advisor.process_wellness_request,
                user_data, constraints, shared_state
            )
            reports['timing'] = timing_result.get('proposal', timing_result)
        except Exception as e:
            logger.error("Timing Advisor failed", error=str(e))
            reports['timing'] = {'error': str(e), 'confidence': 0}
        
        return reports

    def _update_state(self, decision: Dict[str, Any]) -> None:
        """Update internal state after decision."""
        if decision.get('next_meal'):
            self.current_state['meals_today'].append({
                'meal_time': decision['next_meal'].get('meal_time'),
                'items': decision['next_meal'].get('items', []),
                'timestamp': datetime.now().isoformat()
            })
        
        if decision.get('budget_impact'):
            cost = decision['budget_impact'].get('estimated_cost', 0)
            self.current_state['budget']['spent_today'] += cost
            self.current_state['budget']['remaining'] -= cost
        
        self.current_state['last_decision'] = decision

    def apply_missed_meal_policy(self, missed_meal: str) -> Dict[str, Any]:
        """Apply recovery policy for missed meal."""
        return {
            'policy': 'MISSED_MEAL_POLICY',
            'action': 'compensate_quality',
            'recommendations': [
                'Add extra protein at next meal',
                'Include fiber-rich vegetables',
                'Avoid compensating with excessive calories'
            ]
        }

    def apply_budget_exceeded_policy(self, overage: float) -> Dict[str, Any]:
        """Apply recovery policy for budget exceeded."""
        return {
            'policy': 'BUDGET_EXCEEDED_POLICY',
            'action': 'optimize_cost_efficiency',
            'recommendations': [
                'Switch to budget protein sources (eggs, dal, soya)',
                'Use seasonal vegetables',
                'Consider meal prep for cost savings'
            ],
            'savings_target': overage
        }


def create_nutrition_manager(confidence_threshold: float = 0.8) -> NutritionManager:
    """Factory function to create NutritionManager instance."""
    return NutritionManager(confidence_threshold=confidence_threshold)
