# Nutrition Agent System Design

## Architecture Overview

The system follows a multi-agent swarm architecture where independent agents collaborate to solve the complex problem of dynamic nutrition planning under constraints.

### Core Components

1.  **Streamlit UI (Frontend)**:
    -   Captures user constraints (Budget, Time, Preferences).
    -   Displays the meal plan and agent reasoning.
    -   Allows users to simulate failure events (e.g., "Missed Lunch").

2.  **Swarm Orchestrator (Coordinator Agent)**:
    -   Receives inputs from the UI.
    -   Delegates tasks to specialized agents.
    -   Synthesizes the final plan.

3.  **Specialized Agents**:
    -   **Nutrition Agent (The Architect)**: Responsible for selecting meals that meet nutritional goals within budget and time limits.
    -   **Fitness Agent (The Coach)**: Provides calorie and macro adjustments based on workout intensity and recovery needs.

4.  **Data Layer (Mock)**:
    -   `FoodDatabase`: A collection of food items with attributes (cost, prep_time, macros, tags).
    -   `UserProfile`: Stores user stats (age, weight, goal) and dynamic state (budget_used, current_hunger).

## Agent Workflow

1.  **Initialization**: User logs in or sets initial constraints.
2.  **Planning Loop**:
    -   `Coordinator` asks `Fitness Agent` for daily targets.
    -   `Coordinator` passes targets + constraints (Budget: $X, Time: Y mins) to `Nutrition Agent`.
    -   `Nutrition Agent` generates a `MealPlan`.
3.  **Execution & Recovery**:
    -   User logs "Missed Meal" or "Budget Cut".
    -   `Coordinator` triggers a re-plan.
    -   `Nutrition Agent` adjusts remaining meals (e.g., cheaper dinner if budget is tight).

## Data Models

### UserContext
-   `daily_budget`: float
-   `time_available`: int (minutes)
-   `preferences`: List[str]
-   `current_state`: Dict (e.g., {'calories_consumed': 500})

### FoodItem
-   `name`: str
-   `cost`: float
-   `prep_time`: int
-   `calories`: int
-   `protein`: int
-   `tags`: List[str] (e.g., "quick", "vegan")

## Technology Stack
-   **Langauge**: Python 3.9+
-   **Framework**: Swarms (or custom agent loop if swarms lib has issues)
-   **UI**: Streamlit
-   **Data**: In-memory / Pandas
