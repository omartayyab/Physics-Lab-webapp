import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Page Configuration ---
st.set_page_config(page_title="Physics Lab Dashboard", layout="wide")

# --- 2. Left-Hand Pane (Sidebar) Setup ---
with st.sidebar:
    st.header("⚙️ Experiment Parameters")
    
    # Pendulum Length (L) input
    st.number_input("Pendulum Length (L) [meters]", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    
    # Gravity (g) input
    st.number_input("Gravity (g) [m/s²]", min_value=1.0, max_value=25.0, value=9.81, step=0.01)
    
    st.markdown("---")
    st.info("Note: These parameters will be used in Phase 2. Right now, we are just displaying the static dummy data!")

# --- 3. Main Dashboard Setup ---
st.title("Pendulum Physics Lab")
st.markdown("Phase 1: Static Wireframe Design")

# --- 4. Load the Static Data ---
try:
    # Read the CSV we created earlier
    df = pd.read_csv("dummy_data.csv")
    
    # --- 5. Create Interactive Plotly Charts ---
    # We use columns to put the charts side-by-side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Angle vs. Time")
        # Create a line chart using Plotly Express
        fig_angle = px.line(df, x="Time", y="Angle", 
                            labels={"Time": "Time (s)", "Angle": "Angle (Degrees)"},
                            markers=True)
        # Tweak the line color and width
        fig_angle.update_traces(line_color="#1f77b4", line_width=3)
        # Render the chart in Streamlit
        st.plotly_chart(fig_angle, use_container_width=True)
        
    with col2:
        st.subheader("Angular Velocity vs. Time")
        fig_vel = px.line(df, x="Time", y="Angular_Velocity", 
                          labels={"Time": "Time (s)", "Angular_Velocity": "Velocity (deg/s)"},
                          markers=True)
        fig_vel.update_traces(line_color="#ff7f0e", line_width=3)
        st.plotly_chart(fig_vel, use_container_width=True)
        
    # Add a dropdown expander to view the raw numbers if needed
    with st.expander("View Raw Data Table"):
        st.dataframe(df, use_container_width=True)

except FileNotFoundError:
    st.error("Could not find `dummy_data.csv`. Make sure it's saved in the same folder!")