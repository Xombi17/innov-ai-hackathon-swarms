import streamlit as st
import requests
import json
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

# Page Config
st.set_page_config(
    page_title="WellSync AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #f8fafc;
        background-image: radial-gradient(#e2e8f0 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    .stCard {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
        transition: transform 0.2s ease-in-out;
    }
    
    .stCard:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }

    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f1f5f9);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #cbd5e1;
    }
    
    h1 {
        background: linear-gradient(to right, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.025em;
    }
    
    h2, h3 {
        color: #0f172a;
        font-weight: 600;
        letter-spacing: -0.025em;
    }
    
    .status-ok {
        color: #10b981;
        font-weight: 700;
        background: #ecfdf5;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        display: inline-block;
    }
    
    .status-err {
        color: #ef4444;
        font-weight: 700;
        background: #fef2f2;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        display: inline-block;
    }
    
    /* Custom Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Main Title
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://img.icons8.com/3d-fluency/94/brain.png", width=80) 
with col2:
    st.title("WellSync AI Orchestrator")
    st.markdown("### Autonomous Multi-Agent Wellness System")

st.markdown("---")

# System Status Check
API_URL = "http://localhost:5000"

def check_system_status():
    try:
        # Check API Health
        api_resp = requests.get(f"{API_URL}/health", timeout=2)
        api_status = api_resp.json().get('status') == 'healthy'
        
        # Check Agents (Simulated check via API)
        agent_resp = requests.get(f"{API_URL}/agents/status", timeout=2)
        agents_active = len(agent_resp.json().get('agents', []))
        
        return True, agents_active, "System Operational"
    except Exception as e:
        return False, 0, f"Connection Failed: {str(e)}"

status, active_agents, message = check_system_status()

# Dashboard Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3 style="margin:0">System Status</h3>
        <p class="{'status-ok' if status else 'status-err'}" style="font-size: 1.2rem; margin-top: 0.5rem">
            {'ONLINE' if status else 'OFFLINE'}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3 style="margin:0">Active Agents</h3>
        <p style="font-size: 1.5rem; font-weight: bold; color: #3b82f6; margin-top: 0.5rem">
            5
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3 style="margin:0">LLM Provider</h3>
        <p style="font-size: 1.2rem; font-weight: bold; color: #8b5cf6; margin-top: 0.5rem">
            Gemini Flash
        </p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h3 style="margin:0">Database</h3>
        <p style="font-size: 1.2rem; font-weight: bold; color: #10b981; margin-top: 0.5rem">
            SQLite + Redis
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Hero Section
st.markdown("### 🧬 How it Works")
st.info("""
**WellSync AI** uses a swarm of autonomous agents to build your perfect day.
1.  **Fitness Agent**: Analyzes your recovery and goals to design workouts.
2.  **Nutrition Agent**: Plans meals that fuel your workouts and fit your budget.
3.  **Sleep Agent**: Optimizes your circadian rhythm and rest.
4.  **Mental Wellness**: Ensures your plan supports your cognitive health.
5.  **Coordinator Agent**: Resolves conflicts (e.g., "Too tired for HIIT") to create a unified plan.
""")

if not status:
    st.error(f"⚠️ **API is unreachable.** Please run `python run_api.py` in your terminal.\n\nError: {message}")
else:
    st.success("✅ **System Connected.** Navigate to **'User Profile'** in the sidebar to start generating your plan!")

st.sidebar.success("Select a page above.")
