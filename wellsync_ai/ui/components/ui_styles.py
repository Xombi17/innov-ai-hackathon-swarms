import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --primary: #6366f1;
            --primary-light: #818cf8;
            --secondary: #8b5cf6;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --background: #0f172a;
            --surface: #1e293b;
            --surface-light: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: rgba(99, 102, 241, 0.2);
        }

        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            font-family: 'Inter', sans-serif;
        }
        
        /* Hide Streamlit branding but keep menu accessible */
        footer {visibility: hidden;}
        header {visibility: visible;}
        
        /* Dashboard Card */
        .dashboard-card {
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        
        .dashboard-card:hover {
            transform: translateY(-2px);
            border-color: var(--primary-light);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
        }
        
        /* Metric Card */
        .metric-card {
            background: linear-gradient(145deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
            font-weight: 500;
        }
        
        /* Domain Card */
        .domain-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .domain-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 1rem;
        }
        
        .domain-icon {
            font-size: 2rem;
        }
        
        .domain-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
        }
        
        /* Item Row */
        .item-row {
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            background: rgba(99, 102, 241, 0.05);
            border-radius: 12px;
            margin: 0.5rem 0;
            border-left: 3px solid var(--primary);
        }
        
        .item-row:hover {
            background: rgba(99, 102, 241, 0.1);
        }
        
        /* Confidence Badge */
        .confidence-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .confidence-high {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }
        
        .confidence-medium {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }
        
        .confidence-low {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }
        
        /* Summary Box */
        .summary-box {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1));
            border: 1px solid var(--primary);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        
        .summary-title {
            font-size: 0.9rem;
            color: var(--primary-light);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.75rem;
        }
        
        .summary-text {
            color: var(--text-primary);
            line-height: 1.7;
            font-size: 1rem;
        }
        
        /* Agent Card */
        .agent-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .agent-name {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        /* Progress Ring (CSS) */
        .progress-ring {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: conic-gradient(var(--primary) var(--progress), var(--surface) 0);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
        }
        
        .progress-ring-inner {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: var(--background);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: var(--text-primary);
        }
        
        /* Workout Session */
        .workout-session {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
            border-left: 4px solid #22c55e;
            border-radius: 0 12px 12px 0;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
        }
        
        .workout-day {
            font-weight: 700;
            color: #22c55e;
            font-size: 0.9rem;
        }
        
        .workout-type {
            font-size: 1.1rem;
            color: var(--text-primary);
            font-weight: 600;
        }
        
        /* Meal Card */
        .meal-card {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05));
            border-left: 4px solid #f59e0b;
            border-radius: 0 12px 12px 0;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
        }
        
        .meal-time {
            font-weight: 600;
            color: #f59e0b;
            font-size: 0.85rem;
        }
        
        .meal-name {
            font-size: 1.1rem;
            color: var(--text-primary);
            font-weight: 600;
        }
        
        /* Sleep Card */
        .sleep-card {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(139, 92, 246, 0.05));
            border-left: 4px solid #8b5cf6;
            border-radius: 0 12px 12px 0;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
        }
        
        /* Conflict Alert */
        .conflict-alert {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            color: #f87171;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            display: flex;
            align-items: start;
            gap: 12px;
        }
        
        .resolution-box {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid #22c55e;
            color: #4ade80;
            padding: 1rem;
            border-radius: 12px;
            margin-top: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
