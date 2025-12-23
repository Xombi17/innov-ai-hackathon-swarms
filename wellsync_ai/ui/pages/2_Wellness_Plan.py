import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Wellness Plan", page_icon="🧬")

st.markdown("# 🧬 Your Wellness Plan")

# Check if profile exists
if "user_profile" not in st.session_state or not st.session_state.user_profile.get("name"):
    st.warning("Please fill out your profile first!")
    st.stop()

# Display User Context
user = st.session_state.user_profile
st.info(f"**Generating Plan for:** {user['name']} | **Goal:** {', '.join(user['goals'])} | **Budget:** ${user.get('constraints', {}).get('daily_budget', 30)}/day")

# Action Button
if st.button("🚀 Activate Agents & Generate Plan", type="primary"):
    
    # Progress Indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulation stages for UX (since we can't get real-time partial updates easily from sync Flask)
    stages = [
        (0.1, "Fitness Agent analyzing recovery..."),
        (0.3, "Nutrition Agent calculating macros..."),
        (0.5, "Sleep Agent optimizing circadian rhythm..."),
        (0.7, "Coordinator Agent resolving conflicts..."),
        (0.9, "Finalizing your personalized plan...")
    ]
    
    # Placeholder for the result
    result_container = st.container()
    
    try:
        # Prepare payload
        payload = {
            "user_id": user["user_id"],
            "user_profile": {
                "name": user["name"],
                "age": user["age"],
                "weight": user["weight"],
                "height": user["height"],
                "activity_level": user["activity_level"],
                "goals": user["goals"],
                "dietary_restrictions": user["dietary_restrictions"]
            },
            "goals": {
                "primary": user["goals"][0] if user["goals"] else "general_wellness",
                "secondary": user["goals"][1:] if len(user["goals"]) > 1 else []
            },
            "constraints": user["constraints"]
        }
        
        # Simulate initial progress while request starts
        for progress, text in stages[:2]:
            status_text.markdown(f"**🔄 {text}**")
            progress_bar.progress(progress)
            time.sleep(0.5)
            
        status_text.markdown("**🔄 Agents are collaborating... (This may take ~30 seconds)**")
        progress_bar.progress(0.4)
        
        # Actual API Call
        response = requests.post(
            "http://localhost:5000/wellness-plan",
            json=payload,
            timeout=120  # Give agents time to think
        )
        
        # Update progress to done
        progress_bar.progress(1.0)
        status_text.empty()
        
        if response.status_code == 200:
            plan_data = response.json()
            
            # --- DISPLAY RESULT ---
            st.balloons()
            
            # Summary Section
            st.markdown("### 📅 Your Daily Plan")
            
            # Safe access to plan content
            plan_content = plan_data.get("plan", {}).get("plan_content", "No plan content generated.")
            if isinstance(plan_content, dict):
                 plan_content = str(plan_content) # Fallback if content is dict
            
            st.markdown(plan_content)
            
            # Agent Insights (Collapsible)
            with st.expander("🔍 Inspect Agent Logic (Debug View)"):
                st.json(plan_data)
                
        else:
            st.error(f"❌ Generation Failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to API. Is `run_api.py` running?")
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
