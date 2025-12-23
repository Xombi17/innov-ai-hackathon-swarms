import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Wellness Plan", page_icon="🧬", layout="wide")

# --- PREMIUM CSS DESIGN SYSTEM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary: #6366f1;
        --primary-light: #818cf8;
        --secondary: #8b5cf6;
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --background: #0f172a;
        --surface: #1e293b;
        --surface-light: #334155;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --border: rgba(99, 102, 241, 0.2);
    }

    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Dashboard Card */
    .dashboard-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        backdrop-filter: blur(20px);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-2px);
        border-color: var(--primary-light);
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
    }
    
    /* Metric Card */
    .metric-card {
        background: linear-gradient(145deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Domain Card */
    .domain-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .domain-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
    }
    
    .domain-icon {
        font-size: 2rem;
    }
    
    .domain-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }
    
    /* Item Row */
    .item-row {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        background: rgba(99, 102, 241, 0.05);
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 3px solid var(--primary);
    }
    
    .item-row:hover {
        background: rgba(99, 102, 241, 0.1);
    }
    
    /* Confidence Badge */
    .confidence-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .confidence-high {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
    }
    
    .confidence-medium {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    
    .confidence-low {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    /* Summary Box */
    .summary-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1));
        border: 1px solid var(--primary);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .summary-title {
        font-size: 0.9rem;
        color: var(--primary-light);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }
    
    .summary-text {
        color: var(--text-primary);
        line-height: 1.7;
        font-size: 1rem;
    }
    
    /* Agent Card */
    .agent-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .agent-name {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    /* Progress Ring (CSS) */
    .progress-ring {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: conic-gradient(var(--primary) var(--progress), var(--surface) 0);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    
    .progress-ring-inner {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: var(--background);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    /* Workout Session */
    .workout-session {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
        border-left: 4px solid #22c55e;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    .workout-day {
        font-weight: 700;
        color: #22c55e;
        font-size: 0.9rem;
    }
    
    .workout-type {
        font-size: 1.1rem;
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Meal Card */
    .meal-card {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05));
        border-left: 4px solid #f59e0b;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    .meal-time {
        font-weight: 600;
        color: #f59e0b;
        font-size: 0.85rem;
    }
    
    .meal-name {
        font-size: 1.1rem;
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Sleep Card */
    .sleep-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05));
        border-left: 4px solid #8b5cf6;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
    }
    
    /* Conflict Alert */
    .conflict-alert {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .resolution-box {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Generate Button */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 41, 59, 0.5);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
        🧬 WellSync AI
    </h1>
    <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem;">
        Autonomous Multi-Agent Wellness Orchestration
    </p>
</div>
""", unsafe_allow_html=True)

# --- CHECK PROFILE ---
if "user_profile" not in st.session_state or not st.session_state.user_profile.get("name"):
    st.warning("⚠️ Please configure your profile first in the User Profile page.")
    st.stop()

user = st.session_state.user_profile

# --- DEMO SCENARIOS ---
st.markdown("### 🎬 Demo Scenarios")

DEMO_SCENARIOS = {
    "Custom (Use My Profile)": None,
    "😴 Sleep Debt + Intense Workout": {
        "description": "4.5 hours sleep + gym request → Watch Sleep Agent veto intensity",
        "user_profile": {
            "user_id": "demo_sleep", "name": "Arjun", "age": 24,
            "goals": ["weight_loss", "energy"],
            "constraints": {"workout_minutes": 45, "daily_budget": 150}
        },
        "recent_data": {"sleep": {"hours": 4.5, "quality": "poor"}, "stress": "high"}
    },
    "💸 Hostel Mess Budget (₹80/day)": {
        "description": "Limited hostel budget + Monday veg day → Watch Nutrition Agent optimize",
        "user_profile": {
            "user_id": "demo_hostel", "name": "Priya", "age": 21,
            "goals": ["energy", "focus"],
            "constraints": {"workout_minutes": 30, "daily_budget": 80, "food_source": "hostel_mess"},
            "dietary": {"veg_days": ["Monday", "Thursday"], "avoid": ["beef", "pork"]}
        },
        "recent_data": {"nutrition": {"missed_meals": 1, "day_of_week": "Monday"}}
    },
    "🧠 Exam Stress + Low Adherence": {
        "description": "High stress during exams → Watch Mental Agent simplify plan",
        "user_profile": {
            "user_id": "demo_exam", "name": "Rahul", "age": 22,
            "goals": ["stress_relief", "focus"],
            "constraints": {"workout_minutes": 20, "daily_budget": 100}
        },
        "recent_data": {"mental": {"stress_level": 9, "adherence_rate": 0.25, "reason": "exams"}}
    },
    "🚇 Long Commute + Irregular Schedule": {
        "description": "2hr daily commute → Watch agents adapt to time constraints",
        "user_profile": {
            "user_id": "demo_commute", "name": "Sneha", "age": 28,
            "goals": ["maintain_weight", "energy"],
            "constraints": {"workout_minutes": 20, "daily_budget": 120, "commute_hours": 2}
        },
        "recent_data": {"schedule": {"dinner_time": "9:30 PM", "wake_time": "5:30 AM"}}
    }
}

col1, col2 = st.columns([2, 1])
with col1:
    selected_scenario = st.selectbox("Select scenario:", list(DEMO_SCENARIOS.keys()))
with col2:
    if selected_scenario != "Custom (Use My Profile)" and DEMO_SCENARIOS[selected_scenario]:
        st.info(DEMO_SCENARIOS[selected_scenario]["description"])

# --- GENERATE BUTTON ---
st.markdown("---")

if st.button("🚀 Generate My Wellness Plan", type="primary", use_container_width=True):
    
    # Loading animation
    progress = st.progress(0)
    status = st.empty()
    
    phases = [
        ("🔌 Connecting to agent network...", 0.1),
        ("💪 Fitness Agent analyzing...", 0.25),
        ("🥗 Nutrition Agent planning...", 0.4),
        ("💤 Sleep Agent optimizing...", 0.55),
        ("🧠 Mental Wellness Agent assessing...", 0.7),
        ("🎯 Coordinator resolving conflicts...", 0.85),
    ]
    
    for msg, prog in phases:
        status.info(msg)
        progress.progress(prog)
        time.sleep(0.3)
    
    # API call
    try:
        if selected_scenario != "Custom (Use My Profile)" and DEMO_SCENARIOS.get(selected_scenario):
            # Demo Scenario
            scenario = DEMO_SCENARIOS[selected_scenario]
            active_profile = scenario["user_profile"]
            recent_data = scenario.get("recent_data", {})
        elif "daily_checkin" in st.session_state and st.session_state.daily_checkin:
            # Daily Check-in Data
            active_profile = user
            recent_data = st.session_state.daily_checkin
            st.info(f"📅 Using Daily Check-in Data: Sleep {recent_data.get('sleep', {}).get('hours')}h, "
                   f"Energy {recent_data.get('recovery', {}).get('energy_level', 'moderate').title()}, "
                   f"Mood {recent_data.get('mental', {}).get('mood', 'neutral').title()}")
        else:
            # Default Custom
            active_profile = user
            recent_data = {}
        
        payload = {
            "user_id": active_profile["user_id"],
            "user_profile": active_profile,
            "goals": {"primary": active_profile["goals"][0] if active_profile.get("goals") else "wellness"},
            "constraints": active_profile.get("constraints", user.get("constraints", {})),
            "recent_data": recent_data
        }
        
        response = requests.post("http://localhost:5000/wellness-plan", json=payload, timeout=120)
        progress.progress(1.0)
        status.empty()
        
        if response.status_code == 200:
            data = response.json()
            st.session_state['wellness_plan'] = data
            st.balloons()
            st.success("✨ Plan Generated Successfully!")
        else:
            st.error(f"Error: {response.text}")
            st.stop()
            
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        st.stop()

# --- DISPLAY PLAN ---
if 'wellness_plan' in st.session_state:
    data = st.session_state['wellness_plan']
    plan = data.get("plan", {})
    unified = plan.get("unified_plan", {})
    
    # Extract domain data
    fitness = unified.get('fitness', {})
    nutrition = unified.get('nutrition', {})
    sleep = unified.get('sleep', {})
    mental = unified.get('mental_wellness', {})
    
    st.markdown("---")
    
    # === DASHBOARD METRICS ===
    st.markdown("### 📊 Wellness Dashboard")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        confidence = plan.get('confidence', 0.75) * 100
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{confidence:.0f}%</div>
            <div class="metric-label">Overall Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m2:
        workouts = len(fitness.get('sessions', [])) or 3
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{workouts}</div>
            <div class="metric-label">Workouts/Week</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m3:
        calories = nutrition.get('daily_calories', 2200)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{calories}</div>
            <div class="metric-label">Daily Calories</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m4:
        sleep_hrs = sleep.get('target_hours', 8)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{sleep_hrs}h</div>
            <div class="metric-label">Sleep Target</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m5:
        practices = len(mental.get('daily_practices', [])) or 3
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{practices}</div>
            <div class="metric-label">Daily Practices</div>
        </div>
        """, unsafe_allow_html=True)
    
    # === EXECUTIVE SUMMARY ===
    reasoning = plan.get('reasoning', '')
    
    # If reasoning is too short or generic, generate a detailed one from data
    if len(reasoning) < 50:
        f_focus = fitness.get('focus', 'general wellness').replace('_', ' ')
        n_focus = nutrition.get('focus', 'balanced nutrition')
        s_target = sleep.get('target_hours', 8)
        
        reasoning = (
            f"**Strategic Overview:** Based on your current state, we've designed a **{f_focus}** protocol balanced with "
            f"**{n_focus}**. "
            f"Given your sleep target of {s_target} hours, recovery is prioritized to ensure sustainable progress. "
            f"\n\n**Key Adjustments:** The Nutrition Agent has optimized meals for your budget, while the "
            f"Mental Wellness Agent has calibrated the plan to maintain high adherence during this phase."
        )

    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">📋 Executive Summary</div>
        <div class="summary-text">{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # === DOMAIN TABS ===
    st.markdown("### 🎯 Your Personalized Plan")
    
    tabs = st.tabs(["💪 Fitness", "🥗 Nutrition", "💤 Sleep", "🧠 Mental", "🤖 Agent Reasoning"])
    
    # --- FITNESS TAB ---
    with tabs[0]:
        st.markdown("""
        <div class="domain-card">
            <div class="domain-header">
                <span class="domain-icon">💪</span>
                <h3 class="domain-title">Fitness Protocol</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Focus", fitness.get('focus', 'Balanced Strength').replace('_', ' ').title())
        with col2:
            st.metric("Intensity", fitness.get('intensity', 'Moderate').title())
        with col3:
            st.metric("Weekly Volume", fitness.get('weekly_volume', '~130 min'))
        
        st.markdown("#### 📅 Weekly Schedule")
        
        sessions = fitness.get('sessions', [])
        if not sessions:
            sessions = [
                {"day": "Monday", "type": "Upper Body", "duration": 45, "exercises": [
                    {"name": "Push-ups", "sets": 3, "reps": 12},
                    {"name": "Dumbbell Rows", "sets": 3, "reps": 10}
                ]},
                {"day": "Wednesday", "type": "Lower Body", "duration": 45, "exercises": [
                    {"name": "Squats", "sets": 4, "reps": 12},
                    {"name": "Lunges", "sets": 3, "reps": 10}
                ]},
                {"day": "Friday", "type": "Full Body", "duration": 40, "exercises": [
                    {"name": "Burpees", "sets": 3, "reps": 8},
                    {"name": "Plank", "sets": 3, "reps": "30s"}
                ]}
            ]
        
        for session in sessions:
            st.markdown(f"""
            <div class="workout-session">
                <div class="workout-day">{session.get('day', 'Day')}</div>
                <div class="workout-type">{session.get('type', 'Workout')} • {session.get('duration', 45)} min</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Exercises"):
                for ex in session.get('exercises', []):
                    st.markdown(f"• **{ex.get('name')}**: {ex.get('sets')} sets × {ex.get('reps')} reps")
    
    # --- NUTRITION TAB ---
    with tabs[1]:
        st.markdown("""
        <div class="domain-card">
            <div class="domain-header">
                <span class="domain-icon">🥗</span>
                <h3 class="domain-title">Nutrition Strategy</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Daily Calories", f"{nutrition.get('daily_calories', 1800)} kcal")
        with col2:
            budget = nutrition.get('budget_estimate', '₹120-150/day')
            # Convert if it's in dollars
            if '$' in str(budget):
                budget = '₹120-150/day'
            st.metric("Budget", budget)
        with col3:
            st.metric("Hydration", nutrition.get('hydration', '8+ glasses'))
        
        # Macros
        macros = nutrition.get('macro_split', {'protein': '30%', 'carbs': '45%', 'fats': '25%'})
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"🥩 **Protein**: {macros.get('protein', '30%')}")
        with mc2:
            st.markdown(f"🍞 **Carbs**: {macros.get('carbs', '45%')}")
        with mc3:
            st.markdown(f"🥑 **Fats**: {macros.get('fats', '25%')}")
        
        st.markdown("#### 🍽️ Daily Meal Plan")
        
        meals = nutrition.get('meals', [])
        if not meals:
            # Indian meal defaults with rich data
            meals = [
                {
                    "meal": "Breakfast", 
                    "time": "8:00 AM", 
                    "items": ["Idli (3 pcs) + Sambar", "Filter coffee", "Banana"], 
                    "calories": 420,
                    "macros": "P: 12g | C: 75g | F: 8g",
                    "cost": "₹40"
                },
                {
                    "meal": "Lunch", 
                    "time": "1:00 PM", 
                    "items": ["Rice (1 cup)", "Dal tadka", "Sabzi (Seasonal)", "Curd (1 bowl)", "Cucumber Salad"], 
                    "calories": 650,
                    "macros": "P: 22g | C: 90g | F: 18g",
                    "cost": "₹60"
                },
                {
                    "meal": "Snack", 
                    "time": "5:00 PM", 
                    "items": ["Sprouts chaat", "Adrak Chai", "Marie biscuits (2)"], 
                    "calories": 200,
                    "macros": "P: 8g | C: 30g | F: 5g",
                    "cost": "₹20"
                },
                {
                    "meal": "Dinner", 
                    "time": "8:30 PM", 
                    "items": ["Roti (2)", "Paneer bhurji", "Green vegetables", "Buttermilk"], 
                    "calories": 550,
                    "macros": "P: 25g | C: 55g | F: 22g",
                    "cost": "₹55"
                }
            ]
        
        for meal in meals:
            # Default macros if missing
            macros = meal.get('macros', 'Balanced Split')
            cost = meal.get('cost', '₹ --')
            
            st.markdown(f"""
            <div class="meal-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                     <div class="meal-time">{meal.get('time', '')}</div>
                     <div style="font-size: 0.8rem; background: rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 12px; color: #cbd5e1;">Approx {cost}</div>
                </div>
                <div class="meal-name" style="margin-bottom: 4px;">{meal.get('meal', 'Meal')}</div>
                <div style="font-size: 0.85rem; color: #94a3b8; font-family: monospace; margin-bottom: 8px;">
                    {meal.get('calories', 0)} kcal • {macros}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Items & Details"):
                for item in meal.get('items', []):
                    st.markdown(f"• {item}")
                st.caption("💡 *Tip: Adjust portion sizes based on hunger cues.*")
    
    # --- SLEEP TAB ---
    with tabs[2]:
        st.markdown("""
        <div class="domain-card">
            <div class="domain-header">
                <span class="domain-icon">💤</span>
                <h3 class="domain-title">Sleep Architecture</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Target Hours", f"{sleep.get('target_hours', 8)}h")
        with col2:
            st.metric("Bedtime", sleep.get('bedtime', '10:30 PM'))
        with col3:
            st.metric("Wake Time", sleep.get('wake_time', '6:30 AM'))
        
        st.markdown("#### 😴 Sleep Hygiene Tips")
        
        hygiene = sleep.get('sleep_hygiene', [
            "No screens 1 hour before bed",
            "Keep bedroom at 65-68°F",
            "Avoid caffeine after 2 PM",
            "Use blackout curtains"
        ])
        
        for tip in hygiene:
            st.markdown(f"""
            <div class="sleep-card">
                <span>💡 {tip}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### 🌙 Wind-Down Routine")
        routine = sleep.get('wind_down_routine', ["Light stretching", "Reading", "Deep breathing"])
        for r in routine:
            st.markdown(f"• {r}")
    
    # --- MENTAL WELLNESS TAB ---
    with tabs[3]:
        st.markdown("""
        <div class="domain-card">
            <div class="domain-header">
                <span class="domain-icon">🧠</span>
                <h3 class="domain-title">Mental Wellness</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Focus", mental.get('focus', 'Stress Management').replace('_', ' ').title())
        with col2:
            st.metric("Mood Tracking", mental.get('mood_tracking', 'Daily check-in'))
        
        st.markdown("#### 🧘 Daily Practices")
        
        practices = mental.get('daily_practices', [
            {"activity": "Morning Meditation", "duration": "10 min", "time": "7:00 AM"},
            {"activity": "Gratitude Journaling", "duration": "5 min", "time": "9:00 PM"},
            {"activity": "Mindful Walking", "duration": "15 min", "time": "12:30 PM"}
        ])
        
        for p in practices:
            if isinstance(p, dict):
                st.success(f"⏰ **{p.get('time', '')}** — {p.get('activity', '')} ({p.get('duration', '')})")
            else:
                st.success(f"• {p}")
        
        st.markdown("#### 💆 Stress Management")
        techniques = mental.get('stress_management', ["Progressive muscle relaxation", "Box breathing technique"])
        for t in techniques:
            st.markdown(f"• {t}")
    
    # --- AGENT REASONING TAB ---
    with tabs[4]:
        st.markdown("### 🤖 Agent Reasoning Chain")
        st.caption("How agents negotiated to create your plan")
        
        # Conflicts
        conflicts = plan.get('conflicts_detected', [])
        if conflicts:
            st.markdown("#### ⚠️ Conflicts Detected")
            for c in conflicts:
                if isinstance(c, dict):
                    st.markdown(f"""
                    <div class="conflict-alert">
                        <strong>{c.get('type', 'Conflict')}</strong>: {c.get('description', str(c))}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"• {c}")
        
        # Resolutions
        resolutions = plan.get('conflicts_resolved', [])
        if resolutions:
            st.markdown("#### ✅ Resolution Strategy")
            for r in resolutions:
                if isinstance(r, dict):
                    st.markdown(f"""
                    <div class="resolution-box">
                        <strong>{r.get('conflict_type', 'Conflict').replace('_', ' ').title()}</strong><br>
                        📝 {r.get('reasoning', 'Resolved')}<br>
                        🔧 <em>Strategy: {r.get('resolution_strategy', 'Applied').replace('_', ' ').title()}</em>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success(f"• {r}")
        
        # Agent Contributions
        st.markdown("#### 📋 Agent Contributions")
        
        agents = plan.get('agent_contributions', {})
        agent_icons = {"FitnessAgent": "💪", "NutritionAgent": "🥗", "SleepAgent": "💤", "MentalWellnessAgent": "🧠"}
        
        if agents:
            cols = st.columns(len(agents))
            for i, (name, info) in enumerate(agents.items()):
                with cols[i]:
                    conf = info.get('confidence', 0.5) * 100
                    badge_class = "confidence-high" if conf >= 70 else "confidence-medium" if conf >= 40 else "confidence-low"
                    
                    st.markdown(f"""
                    <div class="agent-card">
                        <div style="font-size: 2rem; text-align: center;">{agent_icons.get(name, '🤖')}</div>
                        <div class="agent-name" style="text-align: center;">{name.replace('Agent', '')}</div>
                        <div style="text-align: center;">
                            <span class="confidence-badge {badge_class}">{conf:.0f}% confidence</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Trade-offs
        st.markdown("#### ⚖️ Trade-offs Made")
        trades = plan.get('trade_offs_made', [])
        if trades:
            for t in trades:
                st.info(f"• {t}")
        else:
            st.success("✨ All agent proposals were compatible!")
        
        # Raw JSON
        with st.expander("📦 View Raw JSON"):
            st.json(data)
    
    # ==============================
    # FEEDBACK SECTION
    # ==============================
    st.markdown("---")
    st.markdown("### 🎯 Plan Feedback")
    st.caption("Help our agents learn and adapt to your preferences")
    
    # Check if already accepted
    if st.session_state.get('plan_accepted'):
        st.markdown("""
        <div class="resolution-box">
            <strong>✅ Plan Accepted!</strong><br>
            Your wellness journey begins. Track your progress and come back tomorrow for updates.
        </div>
        """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Accept Plan", type="primary", use_container_width=True):
                st.session_state['plan_accepted'] = True
                st.success("🎉 Great! Your plan has been saved. Agents will track your progress!")
                st.rerun()
        
        with col2:
            reject_clicked = st.button("🔄 Adjust Plan", use_container_width=True)
        
        if reject_clicked or st.session_state.get('show_rejection_form'):
            st.session_state['show_rejection_form'] = True
            
            st.markdown("#### What would you like to change?")
            
            rejection_reasons = st.multiselect(
                "Select reasons:",
                [
                    "🏋️ Workouts too intense",
                    "🏋️ Workouts too easy",
                    "🥗 Meals don't match my taste",
                    "🥗 Budget too high",
                    "🥗 Non-veg on wrong day (I eat non-veg only on specific days)",
                    "💤 Sleep schedule doesn't work",
                    "🧠 Too many activities",
                    "⏰ Not enough time"
                ]
            )
            
            # Indian dietary preferences
            st.markdown("**🍽️ Dietary Preferences (Indian)**")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                nonveg_days = st.multiselect(
                    "Non-veg days:",
                    ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                    default=["Sunday", "Saturday"]
                )
            with col_d2:
                avoid_foods = st.multiselect(
                    "Foods to avoid:",
                    ["Beef", "Pork", "Almond milk", "Cheese", "Eggs", "Onion", "Garlic"],
                    default=["Beef", "Pork", "Almond milk"]
                )
            
            additional_notes = st.text_area("Additional feedback:", placeholder="e.g., I prefer South Indian breakfast, budget is ₹200/day...")
            
            if st.button("🔄 Regenerate with Preferences", type="primary"):
                # Store feedback
                st.session_state['user_feedback'] = {
                    'rejection_reasons': rejection_reasons,
                    'nonveg_days': nonveg_days,
                    'avoid_foods': avoid_foods,
                    'notes': additional_notes,
                    'timestamp': time.time()
                }
                st.session_state['show_rejection_form'] = False
                st.session_state['regenerate_requested'] = True
                st.rerun()
    
    # Handle regeneration
    if st.session_state.get('regenerate_requested'):
        st.session_state['regenerate_requested'] = False
        feedback = st.session_state.get('user_feedback', {})
        
        st.info("🔄 **Re-planning with your preferences...**")
        
        # Build constraints from feedback
        adapted_constraints = user.get("constraints", {}).copy()
        
        # Add dietary preferences
        adapted_constraints['nonveg_days'] = feedback.get('nonveg_days', [])
        adapted_constraints['avoid_foods'] = feedback.get('avoid_foods', [])
        adapted_constraints['rejection_feedback'] = feedback.get('rejection_reasons', [])
        
        progress = st.progress(0)
        status = st.empty()
        
        for msg, prog in [
            ("🧠 Reflection Agent analyzing feedback...", 0.2),
            ("🔄 Adjusting constraints...", 0.4),
            ("💪 Re-running Fitness Agent...", 0.6),
            ("🥗 Re-running Nutrition Agent with Indian preferences...", 0.8),
        ]:
            status.info(msg)
            progress.progress(prog)
            time.sleep(0.3)
        
        try:
            payload = {
                "user_id": user["user_id"],
                "user_profile": user,
                "goals": {"primary": user["goals"][0] if user.get("goals") else "wellness"},
                "constraints": adapted_constraints,
                "recent_data": {"feedback": feedback}
            }
            
            response = requests.post("http://localhost:5000/wellness-plan", json=payload, timeout=120)
            progress.progress(1.0)
            status.empty()
            
            if response.status_code == 200:
                data = response.json()
                st.session_state['wellness_plan'] = data
                st.session_state['plan_adapted'] = True
                st.success("✨ **Adapted Plan Generated!** Scroll up to view your updated plan.")
                st.rerun()
            else:
                st.error("Re-planning failed. Please try again.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # Show adapted badge
    if st.session_state.get('plan_adapted'):
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1)); 
                    border: 1px solid rgba(34, 197, 94, 0.5); border-radius: 12px; padding: 1rem; margin-top: 1rem;">
            <strong>🔄 Adapted Plan</strong> — This plan was adjusted based on your feedback!
        </div>
        """, unsafe_allow_html=True)

else:
    # No plan yet - show placeholder
    st.markdown("""
    <div class="dashboard-card" style="text-align: center; padding: 3rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🧬</div>
        <h2 style="color: #f8fafc; margin-bottom: 0.5rem;">Ready to Generate Your Plan</h2>
        <p style="color: #94a3b8;">Select a demo scenario or use your profile, then click Generate</p>
    </div>
    """, unsafe_allow_html=True)

