import streamlit as st
import requests
import json

st.set_page_config(page_title="User Profile", page_icon="👤", layout="wide")

# --- PREMIUM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary: #6366f1;
        --primary-light: #818cf8;
        --background: #0f172a;
        --surface: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
    }

    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    .section-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
    
    .section-label {
        color: #818cf8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 1rem;
    }
    
    .hint-text {
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0;">
    <h1 style="font-size: 2.25rem; font-weight: 800; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        👤 Your Wellness Profile
    </h1>
    <p style="color: #94a3b8; font-size: 1rem;">
        Tell our agents about yourself. This creates your <b>constraint context</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# Initialize session state with India-first defaults
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "user_id": "user_" + str(hash("demo"))[:8],
        "name": "",
        "age": 25,
        "weight": 65,
        "height": 170,
        "gender": "Male",
        "activity_level": "moderate",
        "goals": ["energy", "maintain_weight"],
        "constraints": {
            "daily_budget": 150,  # ₹
            "workout_minutes": 45,
            "food_source": "home",
            "time_availability": "moderate"
        },
        "dietary": {
            "preference": "non_veg",
            "veg_days": ["Monday", "Thursday"],
            "fasting_days": [],
            "avoid_foods": ["beef", "pork"]
        }
    }

current = st.session_state.user_profile

with st.form("profile_form"):
    
    # === SECTION 1: BASIC INFO ===
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">STEP 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🙋 Basic Information</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Your Name", value=current.get("name", ""), placeholder="e.g., Arjun")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                             index=["Male", "Female", "Other"].index(current.get("gender", "Male")))
    with c2:
        age = st.number_input("Age", value=current.get("age", 25), min_value=15, max_value=80)
        height = st.number_input("Height (cm)", value=current.get("height", 170), min_value=100, max_value=220)
    with c3:
        weight = st.number_input("Weight (kg)", value=current.get("weight", 65), min_value=30, max_value=200)
        activity = st.selectbox("Activity Level", 
            ["sedentary", "light", "moderate", "active", "athlete"],
            index=["sedentary", "light", "moderate", "active", "athlete"].index(current.get("activity_level", "moderate")))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SECTION 2: GOALS ===
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">STEP 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎯 Wellness Goals</div>', unsafe_allow_html=True)
    
    goals = st.multiselect(
        "What do you want to achieve?",
        ["weight_loss", "muscle_gain", "maintain_weight", "energy", "better_sleep", 
         "reduce_stress", "focus", "marathon_training"],
        default=current.get("goals", ["energy"])
    )
    st.markdown('<p class="hint-text">Select up to 3 primary goals</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SECTION 3: DIETARY PREFERENCES (INDIA-FIRST) ===
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">STEP 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🍽️ Dietary Preferences</div>', unsafe_allow_html=True)
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        diet_pref = st.selectbox("Diet Type", 
            ["vegetarian", "non_veg", "eggetarian", "vegan"],
            index=["vegetarian", "non_veg", "eggetarian", "vegan"].index(
                current.get("dietary", {}).get("preference", "non_veg")))
        
        if diet_pref == "non_veg":
            veg_days = st.multiselect(
                "Veg-only days (Optional)",
                ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                default=current.get("dietary", {}).get("veg_days", ["Monday", "Thursday"]),
                help="Many Indians eat non-veg only on specific days"
            )
        else:
            veg_days = []
    
    with col_d2:
        fasting_days = st.multiselect(
            "Fasting days (Optional)",
            ["Monday", "Tuesday", "Thursday", "Saturday", "Ekadashi"],
            default=current.get("dietary", {}).get("fasting_days", []),
            help="Religious fasting days"
        )
        
        avoid_foods = st.multiselect(
            "Foods to avoid",
            ["Beef", "Pork", "Eggs", "Onion", "Garlic", "Mushroom", "Dairy"],
            default=[f.title() for f in current.get("dietary", {}).get("avoid_foods", ["Beef", "Pork"]) if f.title() in ["Beef", "Pork", "Eggs", "Onion", "Garlic", "Mushroom", "Dairy"]]
        )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SECTION 4: CONSTRAINTS ===
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">STEP 4</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚙️ Real-World Constraints</div>', unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        budget = st.slider("Daily Food Budget (₹)", 50, 500, 
                          current.get("constraints", {}).get("daily_budget", 150), step=10)
        st.markdown('<p class="hint-text">₹50 = very tight, ₹200+ = comfortable</p>', unsafe_allow_html=True)
        
        food_source = st.selectbox("Where do you eat?",
            ["home", "hostel_mess", "office_canteen", "tiffin_service", "mixed"],
            index=["home", "hostel_mess", "office_canteen", "tiffin_service", "mixed"].index(
                current.get("constraints", {}).get("food_source", "home")),
            help="This affects meal flexibility"
        )
    
    with col_c2:
        workout_time = st.slider("Workout Time Available (mins)", 15, 90, 
                                current.get("constraints", {}).get("workout_minutes", 45), step=5)
        
        time_avail = st.selectbox("Time Flexibility",
            ["very_limited", "limited", "moderate", "flexible"],
            index=["very_limited", "limited", "moderate", "flexible"].index(
                current.get("constraints", {}).get("time_availability", "moderate")),
            help="How flexible is your daily schedule?"
        )
    
    # Commute (optional)
    has_commute = st.checkbox("I have a long commute (1+ hours daily)")
    if has_commute:
        commute_hours = st.slider("Daily commute hours", 1.0, 4.0, 2.0, step=0.5)
    else:
        commute_hours = 0
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # === SUBMIT ===
    submitted = st.form_submit_button("💾 Save Profile & Continue", type="primary", use_container_width=True)

if submitted:
    if not name.strip():
        st.error("Please enter your name!")
    else:
        st.session_state.user_profile = {
            "user_id": "user_" + str(hash(name))[:8],
            "name": name,
            "age": age,
            "weight": weight,
            "height": height,
            "gender": gender,
            "activity_level": activity,
            "goals": goals[:3],  # Max 3 goals
            "constraints": {
                "daily_budget": budget,
                "workout_minutes": workout_time,
                "food_source": food_source,
                "time_availability": time_avail,
                "commute_hours": commute_hours
            },
            "dietary": {
                "preference": diet_pref,
                "veg_days": veg_days if diet_pref == "non_veg" else [],
                "fasting_days": fasting_days,
                "avoid_foods": [f.lower() for f in avoid_foods]
            }
        }
        st.balloons()
        st.success(f"✅ Profile saved for **{name}**! Now go to **Wellness Plan** to generate your schedule.")

# --- SHOW CURRENT PROFILE ---
if current.get("name"):
    st.markdown("---")
    st.markdown("### 📋 Your Current Profile")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Name", current.get("name", "Not set"))
        st.metric("Goals", ", ".join(current.get("goals", [])[:2]) or "Not set")
    with col2:
        st.metric("Budget", f"₹{current.get('constraints', {}).get('daily_budget', 0)}/day")
        st.metric("Food Source", current.get("constraints", {}).get("food_source", "home").replace("_", " ").title())
    with col3:
        st.metric("Diet", current.get("dietary", {}).get("preference", "non_veg").replace("_", " ").title())
        veg_d = current.get("dietary", {}).get("veg_days", [])
        st.metric("Veg Days", ", ".join(veg_d[:2]) if veg_d else "None")
