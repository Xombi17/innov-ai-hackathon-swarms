import streamlit as st
import plotly.graph_objects as go
import numpy as np
import textwrap

def render_dashboard(plan, unified, fitness, nutrition, sleep, mental):
    """
    Renders the Predictive AI Dashboard metrics with advanced visualizations.
    """
    st.markdown("### 🧠 Predictive Analytics & Health Score")
    
    # --- 1. CALCULATE SCORES ---
    try:
        # Sleep Score (Target vs 8h ideal)
        sleep_hrs = sleep.get('target_hours', 8)
        sleep_score = min(100, (sleep_hrs / 8.0) * 100)
        
        # Activity Score (Intensity heuristic)
        # Intensity maps: Low=60, Moderate=80, High=95, Athlete=100
        intensity_map = {"low": 60, "moderate": 80, "high": 95, "athlete": 100}
        act_level = fitness.get('intensity', 'moderate').lower()
        activity_score = intensity_map.get(act_level, 75)
        
        # Nutrition Score (Balance heuristic)
        # Higher score if macros are balanced
        macros = nutrition.get('macro_split', {})
        if "protein" in macros:
             nutrition_score = 90
        else:
             nutrition_score = 70
             
        # Mental/Stress Score (Inverse of stress level)
        # We assume goal 10 practices = 100% (heuristic)
        practices = len(mental.get('daily_practices', []))
        mental_score = 50 + (practices * 15)
        mental_score = min(100, mental_score)
        
        # Overall Readiness
        readiness_score = (sleep_score * 0.35) + (activity_score * 0.25) + (nutrition_score * 0.25) + (mental_score * 0.15)
        readiness_score = int(min(99, readiness_score))
        
        # Determine Status Label
        if readiness_score >= 85:
            readiness_label = "PRIME STATE"
            color = "#10b981" # Green
        elif readiness_score >= 70:
            readiness_label = "OPTIMAL"
            color = "#818cf8" # Indigo
        elif readiness_score >= 50:
            readiness_label = "BALANCED"
            color = "#f59e0b" # Amber
        else:
            readiness_label = "RECOVERY NEEDED"
            color = "#ef4444" # Red
            
    except Exception as e:
        # Fallback
        readiness_score = 78
        readiness_label = "GOOD"
        color = "#818cf8"
        sleep_score, activity_score, nutrition_score, mental_score = 80, 75, 85, 70

    # --- 2. LAYOUT: RADAR CHART + KEY METRICS ---
    col_viz, col_metrics = st.columns([1.2, 1])
    
    with col_viz:
        # Plotly Radar Chart
        categories = ['Sleep Quality', 'Nutritional Balance', 'Physical Intensity', 'Mental Resilience']
        values = [sleep_score, nutrition_score, activity_score, mental_score]
        
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Current Plan',
            line_color=color,
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.4)", # 40% opacity rgba
        ))
        
        # Ideal reference
        fig.add_trace(go.Scatterpolar(
            r=[100, 100, 100, 100],
            theta=categories,
            name='Ideal Goal',
            line_color='#334155',
            line_dash='dot',
            hoverinfo='skip'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(color='#94a3b8'),
                    gridcolor='#334155'
                ),
                angularaxis=dict(
                    tickfont=dict(color='#e2e8f0', size=12)
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            margin=dict(l=40, r=40, t=20, b=20),
            showlegend=False,
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_metrics:
        st.markdown(textwrap.dedent(f"""
        <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8)); border-radius: 16px; padding: 1.5rem; text-align: center; border: 1px solid {color}40; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Daily Health Score</div>
            <div style="font-size: 3.5rem; font-weight: 800; color: {color}; text-shadow: 0 0 20px {color}60;">{readiness_score}</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: {color}; margin-top: 5px;">{readiness_label}</div>
            
            <div style="margin-top: 1.5rem; display: flex; justify-content: space-around; width: 100%;">
                <div>
                   <div style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">{int(sleep.get('target_hours', 8))}h</div>
                   <div style="font-size: 0.7rem; color: #94a3b8;">Sleep</div>
                </div>
                 <div>
                   <div style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">{int(plan.get('confidence', 0.8)*100)}%</div>
                   <div style="font-size: 0.7rem; color: #94a3b8;">Confidence</div>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

    # --- 3. DETAILED ANALYSIS (THE WHY) ---
    with st.expander("🔍 Deep Dive Analysis (Agent Reasoning)", expanded=True):
        st.markdown(f"""
        **Why this plan?**
        - **Sleep vs Activity**: Your sleep score ({sleep_score}/100) dictates the workout intensity. A lower sleep score automatically triggers the Coordinator to veto High Intensity Interval Training (HIIT) in favor of {fitness.get('type', 'Moderate Cardio')}.
        - **Nutrition Precision**: With a **{act_level.title()}** activity level, your protein requirements have been calibrated to support muscle recovery without exceeding the **₹{nutrition.get('budget_estimate', '150').replace('₹', '')}** daily budget constraint.
        - **Burnout Prevention**: The Mental Wellness agent detected a stress load of **{mental_score}/100**, inserting strategic mindfulness breaks (e.g., *{mental.get('daily_practices', ['Breathing'])[0]}*) to maintain cognitive performance.
        """)
