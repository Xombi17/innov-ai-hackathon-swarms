"""
Learning Manager for WellSync AI agents.

Handles adaptive learning, preference fatigue detection, and 
baseline adjustment based on user interaction history.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np

from wellsync_ai.data.database import get_database_manager

class LearningManager:
    """
    Manages adaptive learning for wellness agents.
    
    Responsibilities:
    1. Analyze historical interactions for patterns
    2. Detect preference fatigue (repetitive recommendations)
    3. Adjust baseline expectations based on compliance
    4. Provide context-aware insights for prompt generation
    """
    
    def __init__(self, agent_name: str, domain: str):
        self.agent_name = agent_name
        self.domain = domain
        self.db_manager = get_database_manager()
        
    def get_learning_context(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve learning context for the current session.
        
        Returns:
            Dictionary containing:
            - fatigue_warnings: Areas where user might be bored
            - compliance_trends: How well user follows advice
            - adapted_baselines: Adjusted goals based on history
        """
        # Get recent interactions (last 30 days)
        history = self.db_manager.get_agent_memory(
            self.agent_name, 
            "episodic", 
            limit=50
        )
        
        return {
            "fatigue_analysis": self._analyze_preference_fatigue(history),
            "compliance_trends": self._analyze_compliance(history),
            "adapted_baselines": self._calculate_adapted_baselines(history)
        }
        
    def _analyze_preference_fatigue(self, history: List[Dict[str, Any]]) -> List[str]:
        """
        Detect if specific recommendations are being repeated too often.
        """
        warnings = []
        recent_recommendations = []
        
        # Extract recent proposals from history
        for interaction in history[:10]:  # Look at last 10 interactions
            response = interaction.get('agent_response', {})
            # This extraction logic depends on the specific structure of the domain response
            # For now, we'll generic extraction or rely on 'reasoning' keywords
            if 'proposal' in response:
                recent_recommendations.append(str(response['proposal']))
                
        # Simple repetition check
        if len(recent_recommendations) >= 3:
            # Check if the last 3 recommendations were very similar
            last_3 = recent_recommendations[:3]
            # In a real impl, we'd use semantic similarity. For MVP, exact/string match.
            if len(set(last_3)) == 1:
                warnings.append(f"High repetition detected in recent {self.domain} advice. vary recommendations.")
                
        return warnings

    def _analyze_compliance(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Estimate user compliance based on explicit feedback or subsequent state.
        For MVP, we check if users accepted the plan (if that data exists).
        """
        # Placeholder for MVP - assumes 100% compliance until we have explicit feedback loop
        return {"general_compliance": 0.8}

    def _calculate_adapted_baselines(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adjust baselines if user consistently fails to meet constraints.
        E.g. If user never hits 8h sleep, lower baseline to 7h to be realistic.
        """
        # This would analyze recorded constraint violations
        # For phase 1 MVP, we return empty adjustments
        return {}
