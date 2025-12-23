import streamlit as st
import requests
import json

st.set_page_config(page_title="User Profile", page_icon="👤")

st.markdown("# 👤 User Profile & Goals")
st.markdown("Tell the agents about yourself so they can personalize your plan.")

# Initialize session state for user data
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "user_id": "demo_user_01",
        "name": "Alex",
        "age": 28,
        "weight": 70,
        "height": 175,
        "activity_level": "moderate",
        "goals": ["muscle_gain", "better_sleep"],
        "dietary_restrictions": [],
        "constraints": {
            "daily_budget": 30,
            "workout_minutes": 60
        }
    }

with st.form("profile_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Name", value=st.session_state.user_profile["name"])
        age = st.number_input("Age", value=st.session_state.user_profile["age"], min_value=10, max_value=100)
        weight = st.number_input("Weight (kg)", value=st.session_state.user_profile["weight"])
        
    with col2:
        activity = st.selectbox(
            "Activity Level", 
            ["sedentary", "light", "moderate", "active", "athlete"],
            index=["sedentary", "light", "moderate", "active", "athlete"].index(st.session_state.user_profile["activity_level"])
        )
        height = st.number_input("Height (cm)", value=st.session_state.user_profile["height"])
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    st.markdown("### 🎯 Goals & Preferences")
    
    goals = st.multiselect(
        "Wellness Goals",
        ["weight_loss", "muscle_gain", "better_sleep", "reduce_stress", "marathon_training", "maintenance"],
        default=st.session_state.user_profile["goals"]
    )
    
    diet = st.multiselect(
        "Dietary Restrictions",
        ["vegan", "vegetarian", "gluten_free", "dairy_free", "keto", "none"],
        default=st.session_state.user_profile["dietary_restrictions"] if st.session_state.user_profile["dietary_restrictions"] else ["none"]
    )
    
    st.markdown("### 🛑 Constraints")
    col3, col4 = st.columns(2)
    with col3:
        budget = st.slider("Daily Food Budget ($)", 10, 100, 30)
    with col4:
        time_avail = st.slider("Workout Time (mins)", 15, 120, 60)

    submitted = st.form_submit_button("Save Profile & Continue ➡️", type="primary")

    if submitted:
        # Update session state
        st.session_state.user_profile.update({
            "name": name,
            "age": age,
            "weight": weight,
            "height": height,
            "activity_level": activity,
            "goals": goals,
            "dietary_restrictions": [d for d in diet if d != "none"],
            "constraints": {
                "daily_budget": budget,
                "workout_minutes": time_avail
            }
        })
        st.success("Profile saved! Go to the 'Wellness Plan' page to generate your plan.")
