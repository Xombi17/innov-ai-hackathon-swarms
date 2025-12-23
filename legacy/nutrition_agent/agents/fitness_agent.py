class FitnessAgent:
    """
    The Coach.
    Provides signals about calorie/protein demand.
    """
    def __init__(self):
        self.name = "Fitness Agent"

    def get_daily_goals(self, workout_intensity: str):
        """
        Returns {calories: int, protein: int} based on intensity.
        intensity: 'rest', 'light', 'heavy'
        """
        if workout_intensity == "heavy":
            return {"calories": 2500, "protein": 150}
        elif workout_intensity == "light":
            return {"calories": 2200, "protein": 120}
        else: # rest
            return {"calories": 1800, "protein": 100}

    def recommend_recovery_meal(self):
        return "High Protein, Moderate Carb"
