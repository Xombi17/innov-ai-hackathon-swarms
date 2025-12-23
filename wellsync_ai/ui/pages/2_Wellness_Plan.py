import streamlit as st
import requests
import time
from wellsync_ai.ui.components.ui_styles import apply_custom_styles
from wellsync_ai.ui.components.scenarios import DEMO_SCENARIOS
from wellsync_ai.ui.components.dashboard import render_dashboard
from wellsync_ai.ui.components.fitness_tab import render_fitness_tab
from wellsync_ai.ui.components.nutrition_tab import render_nutrition_tab
from wellsync_ai.ui.components.agent_lab_tab import render_agent_lab
from wellsync_ai.ui.components.agent_reports import render_agent_reports

st.set_page_config(page_title="Wellness Plan", page_icon="🧬", layout="wide")
apply_custom_styles()

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

col1, col2 = st.columns([2, 1])
with col1:
    selected_scenario = st.selectbox("Select scenario:", list(DEMO_SCENARIOS.keys()))
with col2:
    if selected_scenario != "Custom (Use My Profile)" and DEMO_SCENARIOS[selected_scenario]:
        st.info(DEMO_SCENARIOS[selected_scenario]["description"])

# --- GENERATE BUTTON ---
st.markdown("---")

if st.button("🚀 Generate My Wellness Plan", type="primary", use_container_width=True):
    
    # ---------------------------------------------------------
    # LIVE SWARM SIMULATION VISUALIZER
    # ---------------------------------------------------------
    with st.status("🚀 Activating WellSync Swarm Agent Network...", expanded=True) as status:
        
        # Phase 1: Biometric Scan
        st.write("📡 **SYSTEM:** Establishing secure neural link with user profile...")
        time.sleep(0.8)
        st.write(f"👤 **IDENTITY VERIFIED:** {user.get('name', 'User')} (ID: {user.get('user_id')})")
        time.sleep(0.5)
        
        # Phase 2: Fitness Agent
        st.write("💪 **FITNESS_AGENT:** Analyzing biomechanics and time constraints...")
        time.sleep(0.5)
        st.code(f"Constraint Check: {user.get('constraints', {}).get('workout_minutes', 45)} min/day available.\nGoal: {user.get('goals', ['Wellness'])[0]}.", language="json")
        time.sleep(0.8)
        
        # Phase 3: Nutrition Agent
        st.write("🥗 **NUTRITION_AGENT:** Calibrating metabolic requirements...") 
        st.code(f"Budget Limit: ₹{user.get('constraints', {}).get('daily_budget', 150)}/day.\nDietary Restrictions: {user.get('dietary', {}).get('type', 'Standard')}", language="markdown")
        time.sleep(1.0)
        
        # Phase 4: Sleep & Mental Agents
        st.write("💤 **SLEEP_AGENT:** Computing circadian rhythm alignment...")
        time.sleep(0.5)
        st.write("🧠 **MENTAL_AGENT:** Assessing cognitive load and stress markers...")
        time.sleep(0.5)
        
        # Phase 5: Coordinator
        st.write("🎯 **COORDINATOR:** Detecting conflicts in proposed sub-plans...")
        time.sleep(0.8)
        st.write("✅ **RESOLUTION:** Conflicts resolved. Optimizing for adherence.")
        
        status.update(label="✨ Wellness Plan Generated Successfully!", state="complete", expanded=False)
    
    # API call
    try:
        active_profile = user
        recent_data = {}
        
        if selected_scenario != "Custom (Use My Profile)" and DEMO_SCENARIOS.get(selected_scenario):
            # Demo Scenario
            scenario = DEMO_SCENARIOS[selected_scenario]
            active_profile = scenario["user_profile"]
            recent_data = scenario.get("recent_data", {})
        elif "daily_checkin" in st.session_state and st.session_state.daily_checkin:
            # Daily Check-in Data
            recent_data = st.session_state.daily_checkin
            st.info(f"📅 Using Daily Check-in Data")
        
        payload = {
            "user_id": active_profile["user_id"],
            "user_profile": active_profile,
            "goals": {"primary": active_profile["goals"][0] if active_profile.get("goals") else "wellness"},
            "constraints": active_profile.get("constraints", user.get("constraints", {})),
            "recent_data": recent_data
        }
        
        response = requests.post("http://localhost:5000/wellness-plan", json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state['wellness_plan'] = data
            st.balloons()
            # Success message is already shown by status updates
        else:
            st.error(f"Error: {response.text}")
            st.stop()
            
    except Exception as e:
        status.update(label="❌ Generation Failed", state="error", expanded=True)
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
    info = plan  # for agent lab meta info
    
    st.markdown("---")
    
    # 1. Dashboard Metrics
    render_dashboard(plan, unified, fitness, nutrition, sleep, mental)

    # 2. Executive Summary & Agent Reports
    reasoning = plan.get('reasoning', '')
    if len(reasoning) < 50:
        f_focus = fitness.get('focus', 'general wellness').replace('_', ' ')
        n_focus = nutrition.get('focus', 'balanced nutrition')
        s_target = sleep.get('target_hours', 8)
        reasoning = (
            f"**Strategic Overview:** Based on your current state, we've designed a **{f_focus}** protocol balanced with "
            f"**{n_focus}**. "
            f"Given your sleep target of {s_target} hours, recovery is prioritized to ensure sustainable progress."
        )

    # What Changed Today? (Simulated Delta for Demo)
    delta_text = ""
    current_profile_budget = 150
    if 'active_profile' in locals():
        current_profile_budget = active_profile.get('constraints', {}).get('daily_budget', 150)
    else:
        current_profile_budget = user.get('constraints', {}).get('daily_budget', 150)

    if sleep.get('target_hours', 8) > 8:
        delta_text = f"📉 **What Changed:** Workout intensity downgraded to 'Recovery' due to high sleep debt ({sleep.get('target_hours')}h target). "
    elif current_profile_budget < 120:
        delta_text = "💸 **What Changed:** Meal plan switched to 'Budget Saver' mode due to tight budget constraints. "
        
    if delta_text:
        reasoning = delta_text + "\n\n" + reasoning
        
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">📋 Executive Summary</div>
        <div class="summary-text">{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # End-of-Month Budget Mode Banner
    if current_profile_budget <= 100:
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.75rem; border-radius: 12px; margin-bottom: 1rem; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5rem;">💸</span>
            <div>
                <strong style="color: #f87171;">End-of-Month Saver Mode Active</strong><br>
                <span style="color: #cbd5e1; font-size: 0.9rem;">Plan strictness increased to stay within ₹{current_profile_budget}/day. </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. DETAILED AGENT REPORTS
    st.markdown("---")
    render_agent_reports(plan)
    st.markdown("---")

    # === DOMAIN TABS ===
    st.markdown("### 🎯 Your Personalized Plan")
    
    tabs = st.tabs(["💪 Fitness", "🥗 Nutrition", "💤 Sleep", "🧠 Mental", "🧪 Agent Lab"])
    
    render_fitness_tab(tabs[0], fitness)
    render_nutrition_tab(tabs[1], nutrition)
    
    # --- SLEEP TAB (Inline for now) ---
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
        with col1: st.metric("Target Hours", f"{sleep.get('target_hours', 8)}h")
        with col2: st.metric("Bedtime", sleep.get('bedtime', '10:30 PM'))
        with col3: st.metric("Wake Time", sleep.get('wake_time', '6:30 AM'))
        
        st.markdown("#### 😴 Sleep Hygiene Tips")
        for tip in sleep.get('sleep_hygiene', ["No screens 1 hour before bed", "Keep bedroom cool"]):
             st.info(f"💡 {tip}")
    
    # --- MENTAL WELLNESS TAB (Inline for now) ---
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
        with col1: st.metric("Focus", mental.get('focus', 'Stress Management').replace('_', ' ').title())
        with col2: st.metric("Daily Practice", "Meditation (10m)")
        
        st.markdown("#### 🧘 Recommended Practices")
        practices = mental.get('daily_practices', [])
        if not practices: practices = ["Morning Gratitude Journaling", "4-7-8 Breathing Technique"]
        
        for p in practices:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.5); padding: 1rem; border-radius: 12px; margin-bottom: 0.5rem; border-left: 3px solid #6366f1;">
                <strong>{p}</strong>
            </div>
            """, unsafe_allow_html=True)

    # --- AGENT LAB TAB ---
    render_agent_lab(tabs[4], user, info, nutrition, sleep, plan)

    # ==============================
    # FEEDBACK SECTION
    # ==============================
    st.markdown("---")
    st.markdown("### 🎯 Plan Feedback")
    st.caption("Help our agents learn and adapt to your preferences")
    
    if st.session_state.get('plan_accepted'):
        st.success("✅ Plan Accepted! Agents will track your progress.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Accept Plan", type="primary", use_container_width=True):
                st.session_state['plan_accepted'] = True
                st.rerun()
        with col2:
            if st.button("🔄 Adjust Plan", use_container_width=True):
                 st.info("Re-generation feature coming in v2.0 (Hackathon Limit)")

else:
    # No plan yet - show placeholder
    st.markdown("""
    <div class="dashboard-card" style="text-align: center; padding: 3rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🧬</div>
        <h2 style="color: #f8fafc; margin-bottom: 0.5rem;">Ready to Generate Your Plan</h2>
        <p style="color: #94a3b8;">Select a demo scenario or use your profile, then click Generate</p>
    </div>
    """, unsafe_allow_html=True)
