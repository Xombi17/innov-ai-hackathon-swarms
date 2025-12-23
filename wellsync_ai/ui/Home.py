import streamlit as st
import requests
import json
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

# Page Config
st.set_page_config(
    page_title="WellSync AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS & THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --primary: #6366f1;
        --secondary: #8b5cf6;
        --accent: #10b981;
        --background: #0f172a;
        --surface: #1e293b;
        --text: #f8fafc;
    }

    /* GLOBAL STYLES */
    .stApp {
        background-color: var(--background);
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        font-family: 'Outfit', sans-serif;
        color: var(--text);
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        letter-spacing: -0.03em;
    }

    /* GLASSMORPHISM CARDS */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 1rem;
    }

    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.3);
        background: rgba(30, 41, 59, 0.85);
    }
    
    .input-label {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .big-stat {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(to right, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">☀️ Morning Check-in</h1>
    <p style="color: #94a3b8; font-size: 1.1rem;">
        Good morning! Tell us how you're feeling so our agents can adapt your plan.
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize Session State
if "daily_checkin" not in st.session_state:
    st.session_state.daily_checkin = {}

with st.form("daily_checkin_form"):
    
    # === ROW 1: SLEEP & ENERGY ===
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("""
        <div class="glass-card">
            <div class="input-label">💤 Last Night's Sleep</div>
        """, unsafe_allow_html=True)
        
        sleep_hours = st.slider("Hours Slept", 0.0, 12.0, 7.0, 0.5)
        sleep_quality = st.select_slider("Sleep Quality", options=["Terrible", "Poor", "Fair", "Good", "Excellent"], value="Good")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div class="input-label">🔋 Morning Energy</div>
        """, unsafe_allow_html=True)
        
        energy_level = st.select_slider("Energy Level", options=["Exhausted", "Low", "Moderate", "High", "Energized"], value="Moderate")
        soreness = st.radio("Muscle Soreness?", ["None", "Mild", "Moderate", "Severe"], horizontal=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # === ROW 2: NUTRITION & MENTAL ===
    c3, c4 = st.columns(2)
    
    with c3:
        st.markdown("""
        <div class="glass-card">
            <div class="input-label">🍽️ Nutrition Context</div>
        """, unsafe_allow_html=True)
        
        last_meal_time = st.time_input("Last Meal Time (Yesterday)", datetime.strptime("20:00", "%H:%M").time())
        missed_meals = st.checkbox("Missed any meals yesterday?")
        overate = st.checkbox("Overate yesterday?")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="glass-card">
            <div class="input-label">🧠 Mental State</div>
        """, unsafe_allow_html=True)
        
        stress = st.slider("Current Stress (1-10)", 1, 10, 3)
        mood = st.select_slider("Current Mood", options=["Stressed", "Anxious", "Neutral", "Focused", "Happy"], value="Neutral")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # === ROW 3: CONTEXT ===
    st.markdown("""
    <div class="glass-card">
        <div class="input-label">📝 Additional Context (Agents read this)</div>
    """, unsafe_allow_html=True)
    
    notes = st.text_area("Anything else?", placeholder="e.g., Traveling today, have a headache, exam week...", height=80)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # === SUBMIT ===
    submitted = st.form_submit_button("🚀 Generate Today's Plan", type="primary", use_container_width=True)

if submitted:
    # Save to session state
    st.session_state.daily_checkin = {
        "sleep": {
            "hours": sleep_hours,
            "quality": sleep_quality.lower(),
            "wake_time": datetime.now().strftime("%H:%M") # Approx
        },
        "recovery": {
            "energy_level": energy_level.lower(),
            "soreness": soreness.lower()
        },
        "nutrition": {
            "last_meal": str(last_meal_time),
            "missed_meals": missed_meals,
            "overate": overate
        },
        "mental": {
            "stress_level": stress,
            "mood": mood.lower()
        },
        "context_notes": notes,
        "timestamp": time.time()
    }
    
    st.success("Check-in saved! Redirecting to plan generation...")
    st.switch_page("pages/2_Wellness_Plan.py")

# --- FOOTER ---
if not st.session_state.daily_checkin:
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #64748b; font-size: 0.9rem;">
        No check-in today? Agents will use your historical average.
    </div>
    """, unsafe_allow_html=True)
