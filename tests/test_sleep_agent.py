"""
Test suite for SleepAgent implementation.

Tests core functionality of the Sleep & Recovery Agent including:
- Agent initialization and configuration
- Sleep debt calculation algorithms
- Circadian rhythm assessment
- Recovery constraint generation
- Sleep schedule optimization
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from wellsync_ai.agents.sleep_agent import SleepAgent, create_sleep_agent


class TestSleepAgentInitialization:
    """Test SleepAgent initialization and basic functionality."""
    
    def test_create_sleep_agent(self):
        """Test that SleepAgent can be created with factory function."""
        agent = create_sleep_agent()
        
        assert agent.agent_name == "SleepAgent"
        assert agent.domain == "sleep"
        assert agent.confidence_threshold == 0.7
        assert agent.sleep_need_baseline == 8.0
        assert hasattr(agent, 'sleep_debt_history')
        assert hasattr(agent, 'circadian_markers')
        assert hasattr(agent, 'recovery_indicators')
    
    def test_sleep_agent_with_custom_threshold(self):
        """Test SleepAgent creation with custom confidence threshold."""
        agent = create_sleep_agent(confidence_threshold=0.8)
        
        assert agent.confidence_threshold == 0.8
        assert agent.agent_name == "SleepAgent"
        assert agent.domain == "sleep"
    
    def test_sleep_agent_system_prompt(self):
        """Test that SleepAgent has appropriate system prompt."""
        agent = create_sleep_agent()
        
        # Check that system prompt contains key sleep-related concepts
        prompt = agent.system_prompt
        assert "sleep and recovery expert" in prompt.lower()
        assert "sleep debt" in prompt.lower()
        assert "circadian rhythm" in prompt.lower()
        assert "recovery status" in prompt.lower()
        assert "constraints_for_others" in prompt


class TestSleepDebtCalculation:
    """Test sleep debt calculation algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_calculate_sleep_debt_no_history(self):
        """Test sleep debt calculation with no history."""
        sleep_history = {'recent_nights': []}
        
        debt = self.agent._calculate_sleep_debt(sleep_history)
        
        assert debt == 0.0
    
    def test_calculate_sleep_debt_adequate_sleep(self):
        """Test sleep debt calculation with adequate sleep."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 8.0,
                    'quality_score': 10,  # Perfect quality
                    'individual_need': 8.0
                },
                {
                    'duration_hours': 8.5,
                    'quality_score': 10,  # Perfect quality
                    'individual_need': 8.0
                }
            ]
        }
        
        debt = self.agent._calculate_sleep_debt(sleep_history)
        
        # Should be minimal debt since sleep is adequate with good quality
        assert debt < 0.1
    
    def test_calculate_sleep_debt_insufficient_sleep(self):
        """Test sleep debt calculation with insufficient sleep."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 6.0,
                    'quality_score': 7,
                    'individual_need': 8.0
                },
                {
                    'duration_hours': 5.5,
                    'quality_score': 6,
                    'individual_need': 8.0
                }
            ]
        }
        
        debt = self.agent._calculate_sleep_debt(sleep_history)
        
        # Should have significant debt
        assert debt > 1.0
    
    def test_calculate_sleep_debt_poor_quality(self):
        """Test sleep debt calculation with poor sleep quality."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 8.0,
                    'quality_score': 4,  # Poor quality
                    'individual_need': 8.0
                }
            ]
        }
        
        debt = self.agent._calculate_sleep_debt(sleep_history)
        
        # Poor quality should increase effective debt
        assert debt > 0.5


class TestCircadianAssessment:
    """Test circadian rhythm assessment functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_assess_circadian_alignment_consistent_schedule(self):
        """Test circadian assessment with consistent sleep schedule."""
        sleep_history = {
            'recent_nights': [
                {'bedtime': '22:00', 'wake_time': '06:00'},
                {'bedtime': '22:15', 'wake_time': '06:15'},
                {'bedtime': '21:45', 'wake_time': '05:45'},
                {'bedtime': '22:00', 'wake_time': '06:00'},
                {'bedtime': '22:30', 'wake_time': '06:30'},
                {'bedtime': '22:00', 'wake_time': '06:00'},
                {'bedtime': '22:15', 'wake_time': '06:15'}
            ]
        }
        
        alignment = self.agent._assess_circadian_alignment(sleep_history, {})
        
        assert alignment in ['good', 'excellent']
    
    def test_assess_circadian_alignment_inconsistent_schedule(self):
        """Test circadian assessment with inconsistent sleep schedule."""
        sleep_history = {
            'recent_nights': [
                {'bedtime': '22:00', 'wake_time': '06:00'},
                {'bedtime': '01:00', 'wake_time': '09:00'},
                {'bedtime': '23:30', 'wake_time': '07:30'},
                {'bedtime': '20:00', 'wake_time': '04:00'},
                {'bedtime': '02:00', 'wake_time': '10:00'},
                {'bedtime': '21:00', 'wake_time': '05:00'},
                {'bedtime': '00:30', 'wake_time': '08:30'}
            ]
        }
        
        alignment = self.agent._assess_circadian_alignment(sleep_history, {})
        
        assert alignment in ['poor', 'fair']
    
    def test_assess_circadian_alignment_insufficient_data(self):
        """Test circadian assessment with insufficient data."""
        sleep_history = {
            'recent_nights': [
                {'bedtime': '22:00', 'wake_time': '06:00'},
                {'bedtime': '22:15', 'wake_time': '06:15'}
            ]
        }
        
        alignment = self.agent._assess_circadian_alignment(sleep_history, {})
        
        assert alignment == "insufficient_data"


class TestRecoveryStatus:
    """Test recovery status assessment functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_assess_recovery_status_excellent(self):
        """Test recovery status assessment for excellent recovery."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 8.0,
                    'quality_score': 10,  # Perfect quality
                    'bedtime': '22:00',
                    'wake_time': '06:00'
                } for _ in range(7)
            ]
        }
        
        status = self.agent._assess_recovery_status(sleep_history, 30, {'stress_level': 2})
        
        assert status in ['good', 'excellent']
    
    def test_assess_recovery_status_poor(self):
        """Test recovery status assessment for poor recovery."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 5.0,
                    'quality_score': 4,
                    'bedtime': '01:00',
                    'wake_time': '06:00'
                } for _ in range(7)
            ]
        }
        
        status = self.agent._assess_recovery_status(sleep_history, 80, {'stress_level': 8})
        
        assert status in ['poor', 'fair']


class TestRecoveryConstraints:
    """Test recovery constraint generation for other agents."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_generate_recovery_constraints_poor_recovery(self):
        """Test constraint generation for poor recovery status."""
        constraints = self.agent.generate_recovery_constraints(
            recovery_status="poor",
            sleep_debt=5.0,
            fitness_load=70
        )
        
        # Should have restrictive fitness constraints
        fitness_constraints = constraints['fitness_constraints']
        assert fitness_constraints['max_intensity'] == 'light'
        assert fitness_constraints['max_duration_minutes'] <= 30
        assert fitness_constraints['required_rest_days'] >= 2
        
        # Should have nutrition timing constraints
        nutrition_constraints = constraints['nutrition_timing']
        assert 'avoid_caffeine_after' in nutrition_constraints
        assert nutrition_constraints['increase_meal_frequency'] is True
        
        # Should have mental wellness limits
        mental_constraints = constraints['mental_wellness_limits']
        assert mental_constraints['reduce_decision_complexity'] is True
    
    def test_generate_recovery_constraints_excellent_recovery(self):
        """Test constraint generation for excellent recovery status."""
        constraints = self.agent.generate_recovery_constraints(
            recovery_status="excellent",
            sleep_debt=0.5,
            fitness_load=40
        )
        
        # Should allow maximum training
        fitness_constraints = constraints['fitness_constraints']
        assert fitness_constraints['max_intensity'] == 'maximum'
        assert fitness_constraints['can_handle_increased_load'] is True
        
        # Should allow normal nutrition timing
        nutrition_constraints = constraints['nutrition_timing']
        assert nutrition_constraints['normal_meal_timing'] is True
        
        # Should allow normal cognitive load
        mental_constraints = constraints['mental_wellness_limits']
        assert mental_constraints['normal_cognitive_load'] is True


class TestSleepScheduleOptimization:
    """Test sleep schedule optimization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_optimize_sleep_schedule_basic(self):
        """Test basic sleep schedule optimization."""
        user_data = {
            'sleep_preferences': {
                'preferred_bedtime': '22:30',
                'preferred_wake_time': '06:30'
            },
            'chronotype': 'neutral',
            'sleep_history': {'recent_nights': []}
        }
        
        constraints = {
            'work_schedule': {
                'earliest_start': '07:00'
            },
            'social_schedule': {
                'latest_reasonable_bedtime': '23:30'
            }
        }
        
        schedule = self.agent.optimize_sleep_schedule(user_data, constraints)
        
        assert 'bedtime' in schedule
        assert 'wake_time' in schedule
        assert 'sleep_duration_hours' in schedule
        assert schedule['sleep_duration_hours'] >= 7.0  # Minimum reasonable sleep
        assert schedule['constraints_applied']['work_schedule_respected'] is True
    
    def test_optimize_sleep_schedule_with_debt(self):
        """Test sleep schedule optimization with existing sleep debt."""
        user_data = {
            'sleep_preferences': {
                'preferred_bedtime': '22:30',
                'preferred_wake_time': '06:30'
            },
            'chronotype': 'neutral',
            'sleep_history': {
                'recent_nights': [
                    {
                        'duration_hours': 6.0,
                        'quality_score': 6,
                        'individual_need': 8.0
                    } for _ in range(3)
                ]
            }
        }
        
        constraints = {
            'work_schedule': {'earliest_start': '07:00'},
            'social_schedule': {'latest_reasonable_bedtime': '23:30'}
        }
        
        schedule = self.agent.optimize_sleep_schedule(user_data, constraints)
        
        # Should recommend longer sleep to recover debt
        assert schedule['sleep_duration_hours'] > 8.0
        assert schedule['debt_recovery_time'] > 0


class TestUtilityMethods:
    """Test utility methods and helper functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_time_str_to_minutes(self):
        """Test time string to minutes conversion."""
        assert self.agent._time_str_to_minutes('00:00') == 0
        assert self.agent._time_str_to_minutes('06:30') == 390
        assert self.agent._time_str_to_minutes('22:15') == 1335
        assert self.agent._time_str_to_minutes('invalid') == 0
    
    def test_minutes_to_time_str(self):
        """Test minutes to time string conversion."""
        assert self.agent._minutes_to_time_str(0) == '00:00'
        assert self.agent._minutes_to_time_str(390) == '06:30'
        assert self.agent._minutes_to_time_str(1335) == '22:15'
        assert self.agent._minutes_to_time_str(1500) == '01:00'  # Next day
    
    def test_calculate_std_dev(self):
        """Test standard deviation calculation."""
        assert self.agent._calculate_std_dev([]) == 0.0
        assert self.agent._calculate_std_dev([5]) == 0.0
        
        # Test with known values
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        std_dev = self.agent._calculate_std_dev(values)
        assert 1.5 < std_dev < 2.5  # Approximate expected range


class TestSleepDisorderDetection:
    """Test sleep disorder detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = create_sleep_agent()
    
    def test_detect_sleep_disorders_insufficient_data(self):
        """Test sleep disorder detection with insufficient data."""
        sleep_history = {
            'recent_nights': [
                {'duration_hours': 7, 'quality_score': 8, 'awakenings': 1}
                for _ in range(5)  # Less than 14 nights
            ]
        }
        
        result = self.agent.detect_sleep_disorders(sleep_history)
        
        assert result['insufficient_data'] is True
    
    def test_detect_sleep_disorders_normal_sleep(self):
        """Test sleep disorder detection with normal sleep patterns."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 8,
                    'quality_score': 8,
                    'awakenings': 1,
                    'time_to_sleep_minutes': 15,
                    'bedtime': '22:00'
                } for _ in range(14)
            ]
        }
        
        result = self.agent.detect_sleep_disorders(sleep_history)
        
        assert result['sleep_apnea_risk'] == 'low'
        assert result['insomnia_risk'] == 'low'
        assert result['circadian_disorder_risk'] == 'low'
    
    def test_detect_sleep_disorders_apnea_indicators(self):
        """Test sleep disorder detection with sleep apnea indicators."""
        sleep_history = {
            'recent_nights': [
                {
                    'duration_hours': 8,
                    'quality_score': 4,  # Poor quality despite duration
                    'awakenings': 5,     # Frequent awakenings
                    'time_to_sleep_minutes': 15,
                    'bedtime': '22:00'
                } for _ in range(14)
            ]
        }
        
        result = self.agent.detect_sleep_disorders(sleep_history)
        
        assert result['sleep_apnea_risk'] == 'moderate'
        assert 'sleep study evaluation' in ' '.join(result['recommendations']).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])