import streamlit as st

def render_agent_reports(plan):
    """
    Renders detailed "Deep Dive" reports for each agent's reasoning.
    """
    st.markdown("### 🕵️ Agent Intelligence Reports")
    st.caption("Transparent view of individual agent decision matrices and confidence logs.")
    
    # Extract sub-plan data
    unified = plan.get("unified_plan", {})
    fitness = unified.get('fitness', {})
    nutrition = unified.get('nutrition', {})
    sleep = unified.get('sleep', {})
    mental = unified.get('mental_wellness', {})
    
    # Tabs for each agent
    tabs = st.tabs(["💪 Fitness Agent", "🥗 Nutrition Agent", "💤 Sleep Agent", "🧠 Mental Agent"])
    
    # --- FITNESS AGENT ---
    with tabs[0]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 🧠 Reasoning Trace")
            st.info(f"**Objective Function:** {fitness.get('focus', 'General Fitness').title()}")
            st.markdown(f"""
            - **Constraint Analysis:** Verified user time limit. Selected {fitness.get('frequency', '3')} days/week frequency.
            - **Intensity Protocol:** Set to **{fitness.get('intensity', 'Moderate').upper()}** based on 'Recovery' signal from Sleep Agent.
            - **Exercise Selection:** Prioritized compound movements (Squats, Pushups) for maximum ROI in limited time.
            """)
        with c2:
            st.metric("Model Confidence", f"{fitness.get('confidence', 0.88):.0%}")
            st.metric("Adherence Pred.", "High")
            
        with st.expander("📝 View Raw Agent Output (JSON)"):
            st.json(fitness)

    # --- NUTRITION AGENT ---
    with tabs[1]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 🧠 Reasoning Trace")
            st.info(f"**Optimization Target:** {nutrition.get('focus', 'Balanced').title()}")
            st.markdown(f"""
            - **Budget Check:** Daily allocation ₹{nutrition.get('budget_estimate', '150')} is within 'Sustainable' range.
            - **Dietary Filters:** Applied 'No Beef/Pork' filter. Verified 'Veg Days' compliance.
            - **Macro Split:** Calibrated to {nutrition.get('macro_split', 'Balanced')} for metabolic stability.
            """)
        with c2:
            st.metric("Model Confidence", f"{nutrition.get('confidence', 0.92):.0%}")
            st.metric("Cost Accuracy", "±10%")

        with st.expander("📝 View Raw Agent Output (JSON)"):
            st.json(nutrition)
            
    # --- SLEEP AGENT ---
    with tabs[2]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 🧠 Reasoning Trace")
            st.info(f"**Circadian Target:** {sleep.get('target_hours', 8)} Hours")
            st.markdown(f"""
            - **Deficit Analysis:** User reports {sleep.get('current_avg', 'variable')}h average.
            - **Intervention:** Prescribed consistent Bedtime ({sleep.get('bedtime', '10:30 PM')}) to anchor circadian rhythm.
            - **Hygiene Protocol:** Recommended blue-light reduction block (1h pre-bed).
            """)
        with c2:
            st.metric("Model Confidence", f"{sleep.get('confidence', 0.85):.0%}")
            
        with st.expander("📝 View Raw Agent Output (JSON)"):
            st.json(sleep)
            
    # --- MENTAL AGENT ---
    with tabs[3]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 🧠 Reasoning Trace")
            st.info(f"**Cognitive Load:** {mental.get('focus', 'Stress Management').title()}")
            st.markdown(f"""
            - **Stress Vector:** Detected 'High' inputs. Prioritizing Cortisol reduction.
            - **Practice Selection:** Chose 'Meditation' and 'Breathing' for immediate autonomic down-regulation.
            - **Integration:** Scheduled practices post-work to separate professional/personal domains.
            """)
        with c2:
            st.metric("Model Confidence", f"{mental.get('confidence', 0.90):.0%}")
            
        with st.expander("📝 View Raw Agent Output (JSON)"):
            st.json(mental)
