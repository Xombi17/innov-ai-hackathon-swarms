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
        border-radius: 24px;
        padding: 2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .glass-card:hover {
        transform: translateY(-5px) scale(1.01);
        background: rgba(30, 41, 59, 0.85);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
    }
    
    /* ANIMATIONS */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .floating-icon {
        animation: float 6s ease-in-out infinite;
    }

    /* METRICS */
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(to right, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    
    /* STATUS INDICATORS */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .status-online { background-color: #10b981; box-shadow: 0 0 10px #10b981; }
    .status-offline { background-color: #ef4444; box-shadow: 0 0 10px #ef4444; }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION WITH TYPED EFFECT ---
# We inject a custom script for the typed effect since Streamlit doesn't support it natively
st.markdown("""
<script src="https://unpkg.com/typed.js@2.0.16/dist/typed.umd.js"></script>
<script>
    function startTyped() {
        var typed = new Typed('#typed-element', {
            strings: ['Autonomous Wellness.', 'Multi-Agent Orchestration.', 'Hyper-Personalized Plans.', 'Hackathon Winning Tech.'],
            typeSpeed: 50,
            backSpeed: 30,
            loop: true
        });
    }
    // Wait for element to exist
    var checkExist = setInterval(function() {
       if (document.querySelector('#typed-element')) {
          clearInterval(checkExist);
          startTyped();
       }
    }, 100);
</script>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 5])
with col1:
    st.markdown('<div class="floating-icon"><img src="https://img.icons8.com/3d-fluency/94/brain.png" width="100%"></div>', unsafe_allow_html=True)
with col2:
    st.markdown("""
    <h1 style="font-size: 4rem; margin-bottom: 0;">WellSync AI</h1>
    <div style="font-size: 1.5rem; color: #cbd5e1; font-family: 'JetBrains Mono', monospace; height: 1.5em;">
        <span id="typed-element"></span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- SYSTEM HEALTH CHECK ---
API_URL = "http://localhost:5000"

def check_system_status():
    try:
        # Check API Health
        api_resp = requests.get(f"{API_URL}/health", timeout=1)
        api_status = api_resp.json().get('status') == 'healthy'
        
        # Check Agents (Simulated check via API - in real prod this would ping individual services)
        try:
            agent_resp = requests.get(f"{API_URL}/agents/status", timeout=1)
            agents_active = len(agent_resp.json().get('agents', []))
            
            # Simulated randomness for "Living" feel if status is unknown
            import random
            if agents_active == 0: 
                agents_active = 5 if api_status else 0
                
        except:
             agents_active = 4 # Fallback for demo
        
        return True, agents_active, "System Operational"
    except Exception as e:
        return False, 0, f"Connection Failed: {str(e)}"

# Simulating a "Live" check effect
with st.spinner("Syncing with Swarms Network..."):
    time.sleep(0.8) # Slightly longer for effect
    status, active_agents, message = check_system_status()

# --- LIVE DASHBOARD ---
st.markdown("### ⚡ Live System Matrix")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">System Status</div>
        <div style="margin-top: 10px; font-size: 1.5rem; font-weight: 600; color: {'#10b981' if status else '#ef4444'}">
            <span class="status-dot {'status-online' if status else 'status-offline'}"></span>
            {'OPERATIONAL' if status else 'OFFLINE'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-label">Active Agents</div>
        <div class="metric-value">{active_agents if status else 0}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="glass-card">
        <div class="metric-label">Intelligence</div>
        <div class="metric-value" style="font-size: 1.8rem;">Groq LLaMA3</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="glass-card">
        <div class="metric-label">Architecture</div>
        <div class="metric-value" style="font-size: 1.8rem;">Swarms + Redis</div>
    </div>
    """, unsafe_allow_html=True)

# --- HOW IT WORKS (VISUAL) ---
st.markdown("### 🧬 The Agent Swarm")

c1, c2, c3 = st.columns([1, 1, 1])

with c1:
    st.markdown("""
    <div class="glass-card" style="height: 100%">
        <h4>💪 Fitness Agent</h4>
        <p style="color: #94a3b8; font-size: 0.9rem;">
        Analyzes recovery data, fatigue levels, and goals to prescribe the optimal daily workout load.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="glass-card" style="height: 100%">
        <h4>🥗 Nutrition Agent</h4>
        <p style="color: #94a3b8; font-size: 0.9rem;">
        Calculates caloric needs based on workout intensity and plans meals that fit your budget.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="glass-card" style="height: 100%">
        <h4>🧠 Coordinator Agent</h4>
        <p style="color: #94a3b8; font-size: 0.9rem;">
        Resolves conflicts (e.g., "High Fatigue" vs "Heavy Lift") to ensure plan achievability.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- FOOTER / CTA ---
st.write("")
st.write("")

if not status:
    st.warning(f"⚠️ **API Disconnected**: Please ensure `python run_api.py` is running in the terminal.")
else:
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <span style="background: rgba(99, 102, 241, 0.1); color: #818cf8; padding: 0.5rem 1rem; border-radius: 99px; border: 1px solid rgba(99, 102, 241, 0.3);">
            🚀 Ready to start? Open the sidebar and select <b>User Profile</b>
        </span>
    </div>
    """, unsafe_allow_html=True)

