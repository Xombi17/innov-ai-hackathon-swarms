import streamlit as st
import time
import requests
import asyncio
from wellsync_ai.ui.components.ui_styles import apply_custom_styles
from wellsync_ai.ui.components.scenarios import DEMO_SCENARIOS
import graphviz

st.set_page_config(page_title="Agent Simulation Lab", page_icon="🧪", layout="wide")
apply_custom_styles()

# --- HEADER ---
st.markdown("""
<div style="text-align: center; padding: 2rem 0 1rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #22c55e, #10b981, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
        🧪 Simulation Lab
    </h1>
    <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem;">
        Advanced Agent Swarm Intelligence Playground
    </p>
</div>
""", unsafe_allow_html=True)

# Ensure Profile Exists or Use Demo
if "user_profile" not in st.session_state:
    st.info("💡 Loading default demo profile for simulation...")
    st.session_state.user_profile = DEMO_SCENARIOS["😴 Sleep Debt + Intense Workout"]["user_profile"]

user = st.session_state.user_profile

def get_graph(phase="idle", conflict=False):
    """
    Generates a dynamic Graphviz chart based on the simulation phase.
    Phases: idle, analyzing, collaboration, conflict, resolved
    """
    g = graphviz.Digraph()
    g.attr(bgcolor='#0f172a', rankdir='TB')
    g.attr('node', fontname='Helvetica', fontcolor='white', style='filled')
    g.attr('edge', color='#94a3b8')

    # Colors
    c_idle = '#1e293b'
    c_active = '#f59e0b' # Amber
    c_conflict = '#ef4444' # Red
    c_resolved = '#22c55e' # Green
    c_coord = '#3b82f6' # Blue

    # Coordinator
    coord_color = c_coord
    if phase == "conflict": coord_color = c_conflict
    elif phase == "resolved": coord_color = c_resolved
    
    g.node('COORD', '🧠 Coordinator', fillcolor=coord_color, shape='box', fontsize='14')

    # Sub-Agents
    agent_color = c_idle
    if phase in ["analyzing", "collaboration", "conflict"]: agent_color = c_active
    elif phase == "resolved": agent_color = c_resolved

    with g.subgraph() as s:
        s.attr(rank='same')
        s.node('FIT', '💪 Fitness', fillcolor=agent_color, shape='ellipse')
        s.node('NUT', '🥗 Nutrition', fillcolor=agent_color, shape='ellipse')
        s.node('SLP', '💤 Sleep', fillcolor=agent_color, shape='ellipse')
        s.node('MEN', '🧠 Mental', fillcolor=agent_color, shape='ellipse')

    # Edges
    if phase != "idle":
        g.edge('FIT', 'COORD', color='#f59e0b', penwidth='2')
        g.edge('NUT', 'COORD', color='#f59e0b', penwidth='2')
        g.edge('SLP', 'COORD', color='#f59e0b', penwidth='2')
        g.edge('MEN', 'COORD', color='#f59e0b', penwidth='2')
    
    if phase == "conflict":
         g.edge('COORD', 'FIT', label="VETO", color='#ef4444', fontcolor='#ef4444', penwidth='3')
         
    if phase == "resolved":
         g.edge('COORD', 'FIT', color='#22c55e', penwidth='2')
         g.edge('COORD', 'NUT', color='#22c55e', penwidth='2')

    return g

# --- LAYOUT ---
col_ui, col_viz = st.columns([1, 2])

with col_ui:
    st.markdown("### 🎛️ Input Signals")
    st.caption("Inject synthetic signals to trigger swarm behavior.")
    
    with st.container(border=True):
        st.markdown("#### 💤 Sleep Agent Signals")
        sim_sleep = st.slider("Sleep Duration (hrs)", 3.0, 10.0, 6.0, 0.5, help="Simulate sleep deprivation or excess.")
        
        st.markdown("#### 🥗 Nutrition Agent Signals")
        sim_budget = st.slider("Daily Budget (₹)", 50, 500, 150, 10, help="Test adaptability to financial constraints.")
        
        st.markdown("#### 🧠 Mental Agent Signals")
        sim_stress = st.select_slider("Stress Level", ["Low", "Moderate", "High", "Critical"], value="High")

    st.markdown("### 🎬 Scenario Presets")
    scenario = st.selectbox("Load Preset:", ["Custom"] + list(DEMO_SCENARIOS.keys())[1:])
    
    if st.button("🚀 Run Swarm Simulation", type="primary", use_container_width=True):
        st.session_state['run_sim'] = True
        st.session_state['sim_params'] = {
            "sleep": sim_sleep,
            "budget": sim_budget,
            "stress": sim_stress
        }

with col_viz:
    st.markdown("### 🧠 Swarm Neural Network")
    
    viz_container = st.empty()
    log_container = st.container(border=True, height=200)
    
    if st.session_state.get('run_sim'):
        params = st.session_state['sim_params']
        
        # 1. IDLE
        viz_container.graphviz_chart(get_graph("idle"), use_container_width=True)
        time.sleep(0.5)
        
        # 2. ANALYZING (Parallel Execution)
        viz_container.graphviz_chart(get_graph("analyzing"), use_container_width=True)
        log_container.info("📡 **PHASE 1: PARALLEL ANALYSIS**\n\nAgents detected input signals. Spinning up parallel inference threads...")
        time.sleep(1.5)
        
        # 3. COLLABORATION (Sending to Coordinator)
        # Determine logs
        sleep_log = "⚠️ Sleep Debt Detected" if params['sleep'] < 6 else "✅ Sleep Normal"
        budget_log = "💸 Budget Constraint" if params['budget'] < 100 else "✅ Budget Healthy"
        
        viz_container.graphviz_chart(get_graph("collaboration"), use_container_width=True)
        log_container.markdown(f"""
        **📡 PHASE 2: DATA AGGREGATION**
        - **Sleep Agent**: {sleep_log} ({params['sleep']}h)
        - **Nutrition Agent**: {budget_log} (₹{params['budget']})
        - **Mental Agent**: Stress Level {params['stress']}
        
        *Sending discrete proposals to Coordinator...*
        """)
        time.sleep(2.0)
        
        # 4. CONFLICT / RESOLUTION
        conflict = False
        if params['sleep'] < 6 or params['budget'] < 100:
            conflict = True
            
        if conflict:
            viz_container.graphviz_chart(get_graph("conflict"), use_container_width=True)
            log_container.error(f"""
            **🔴 PHASE 3: CONFLICT DETECTED**
            
            **Coordinator Alert:** Proposed Fitness Plan (High Intensity) conflicts with Sleep Agent data (Recovery Needed).
            
            *Initiating Veto Protocol...*
            """)
            time.sleep(2.5)
            
        # 5. RESOLVED
        viz_container.graphviz_chart(get_graph("resolved"), use_container_width=True)
        
        final_msg = "**✅ PHASE 4: CONSENSUS REACHED**\n\n"
        if params['sleep'] < 6:
            final_msg += "-> Switched to **RECOVERY MODE** (Yoga/Light Cardio)\n"
        if params['budget'] < 100:
            final_msg += "-> Switched to **BUDGET MEAL PLAN** (Local Ingredients)"
        
        if not conflict:
            final_msg += "-> All systems nominal. **PERFORMANCE MODE** activated."
            
        log_container.success(final_msg)
        st.session_state['run_sim'] = False # Reset for next run
        
    else:
        viz_container.graphviz_chart(get_graph("idle"), use_container_width=True)
        log_container.caption("Waiting for simulation start...")
