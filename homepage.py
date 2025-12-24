import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Skip2Smooth Video Processor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 8px;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🎬 Skip2Smooth")
    st.subheader("Intelligent Video Keyframe Selector & Processor")

if __name__ == "__main__":
    main()