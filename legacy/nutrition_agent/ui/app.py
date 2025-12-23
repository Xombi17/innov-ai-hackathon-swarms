import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nutrition_agent.agents.coordinator import CoordinatorAgent

st.set_page_config(page_title="Nutrition Agent", layout="wide")

# Custom CSS for that "Modern" look
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    .warning {
        color: #FFC107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🥗 Nutrition Agent Swarm")
    st.markdown("### Autonomous Decision System for Real-World Nutrition")

    # Sidebar: User Context
    with st.sidebar:
        st.header("1. Define Constraints")
        budget = st.slider("Daily Budget ($)", 10.0, 50.0, 20.0, step=1.0)
        time_avail = st.slider("Prep Time Available (mins/meal)", 5, 60, 30, step=5)
        workout = st.selectbox("Today's Intensity", ["rest", "light", "heavy"])
        
        if st.button("Generate Plan"):
            st.session_state['coordinator'] = CoordinatorAgent()
            plan, context = st.session_state['coordinator'].initialize_day(budget, time_avail, workout)
            st.session_state['plan'] = plan
            st.session_state['context'] = context
            st.session_state['logs'] = ["Agent Swarm Initialized...", "Fitness Agent requested daily targets.", f"Nutrition Agent optimizing for ${budget} and {time_avail}m."]

    # Main Area
    if 'plan' in st.session_state:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📅 Optimized Meal Plan")
            
            plan = st.session_state['plan']
            total_cal = 0
            total_protein = 0
            total_cost = 0

            cols = st.columns(3)
            for i, (meal_type, food) in enumerate(plan.items()):
                with cols[i]:
                    st.markdown(f"""
                    <div class="card">
                        <h4>{meal_type.capitalize()}</h4>
                        <h3>{food.name}</h3>
                        <p>⏱️ {food.prep_time}m | 💰 ${food.cost}</p>
                        <p>🔥 {food.calories}kcal | 🥩 {food.protein}g</p>
                    </div>
                    """, unsafe_allow_html=True)
                    total_cal += food.calories
                    total_protein += food.protein
                    total_cost += food.cost
            
            # Metrics
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Calories", total_cal)
            m2.metric("Total Protein", f"{total_protein}g")
            m3.metric("Cost Used", f"${total_cost:.2f}")

        with col2:
            st.subheader("🤖 Agent Reasoning")
            for log in st.session_state.get('logs', []):
                st.info(log)
            
            st.markdown("### 🧯 Simulation: Failure Events")
            st.markdown("Testing the agent's ability to **recover** from deviations.")
            
            if st.button("🚨 Constraint Violation: Missed Lunch"):
                msg = st.session_state['coordinator'].handle_exception("missed_lunch", st.session_state['context'])
                st.session_state['logs'].append("USER EVENT: Missed Lunch")
                st.session_state['logs'].append(msg)
                st.rerun()

    else:
        st.info("👈 Please set your constraints and click 'Generate Plan' to start the swarm.")

if __name__ == "__main__":
    main()
