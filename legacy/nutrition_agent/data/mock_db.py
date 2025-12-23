from nutrition_agent.models.food_item import FoodItem

FOOD_DATABASE = [
    # Breakfast
    FoodItem(name="Oats & Banana", cost=1.50, prep_time=5, calories=350, protein=10, tags=["breakfast", "quick", "vegan", "cheap"], meal_type="breakfast"),
    FoodItem(name="Eggs & Toast", cost=2.00, prep_time=15, calories=400, protein=20, tags=["breakfast", "protein"], meal_type="breakfast"),
    FoodItem(name="Greek Yogurt Parfait", cost=3.50, prep_time=5, calories=300, protein=15, tags=["breakfast", "quick", "cold"], meal_type="breakfast"),
    FoodItem(name="Masala Omelette", cost=2.50, prep_time=20, calories=450, protein=25, tags=["breakfast", "spicy", "protein"], meal_type="breakfast"),

    # Lunch
    FoodItem(name="Chicken Rice Bowl", cost=8.00, prep_time=0, calories=600, protein=40, tags=["lunch", "protein", "filling"], meal_type="lunch"),
    FoodItem(name="Veggie Wrap", cost=5.00, prep_time=0, calories=450, protein=10, tags=["lunch", "vegan", "light"], meal_type="lunch"),
    FoodItem(name="Dal Khichdi", cost=3.00, prep_time=30, calories=500, protein=15, tags=["lunch", "cheap", "comfort"], meal_type="lunch"),
    FoodItem(name="Subway Sandwich", cost=7.00, prep_time=0, calories=550, protein=20, tags=["lunch", "quick", "fresh"], meal_type="lunch"),

    # Dinner
    FoodItem(name="Grilled Chicken Salad", cost=9.00, prep_time=20, calories=400, protein=35, tags=["dinner", "light", "protein"], meal_type="dinner"),
    FoodItem(name="Pasta Arrabbiata", cost=6.00, prep_time=25, calories=600, protein=12, tags=["dinner", "comfort", "carb"], meal_type="dinner"),
    FoodItem(name="Protein Shake", cost=2.00, prep_time=2, calories=200, protein=25, tags=["snack", "dinner", "quick", "protein"], meal_type="dinner"),
    FoodItem(name="Instant Noodles with Egg", cost=1.00, prep_time=5, calories=450, protein=10, tags=["dinner", "cheap", "unhealthy"], meal_type="dinner"),
]

def get_foods(meal_type=None, max_cost=None, max_time=None):
    results = FOOD_DATABASE
    if meal_type:
        results = [f for f in results if f.meal_type == meal_type]
    if max_cost is not None:
        results = [f for f in results if f.cost <= max_cost]
    if max_time is not None:
        results = [f for f in results if f.prep_time <= max_time]
    return results
