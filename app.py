import streamlit as st
import pandas as pd
import plotly.express as px
import time
import scipy.signal as signal
import numpy as np
import subprocess
import os
import sys

# Forces a wide, professional layout
st.set_page_config(page_title="PHYS-LAB: Pendulum Kinematics", layout="wide")

# Custom CSS for a "Terminal" feel
st.markdown("""
    <style>
    .stApp { font-family: 'Courier New', Courier, monospace; }
    h1, h2, h3 { border-bottom: 1px solid #30363d; padding-bottom: 10px; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALIZATION ---
if "captured_angle" not in st.session_state: st.session_state.captured_angle = []
if "captured_velocity" not in st.session_state: st.session_state.captured_velocity = []
if "lab_notebook" not in st.session_state: st.session_state.lab_notebook = []
if "cal_notebook" not in st.session_state: st.session_state.cal_notebook = []
if "lab_mode" not in st.session_state: st.session_state.lab_mode = "IDLE"
if "simulation_active" not in st.session_state: st.session_state.simulation_active = False
if "simulation_process" not in st.session_state: st.session_state.simulation_process = None

# --- SIDEBAR (TECHNICAL PARAMETERS) ---
with st.sidebar:
    st.title("CONTROL INTERFACE")
    
    with st.expander("PHYSICAL CONSTANTS", expanded=True):
        length = st.number_input("Length (L) [m]", value=1.000, step=0.001, format="%.3f")
        gravity = st.number_input("Gravity (g) [m/s²]", value=9.807, step=0.001, format="%.3f")
        mass = st.number_input("Mass (m) [kg]", value=0.500, step=0.001, format="%.3f")

    with st.expander("INITIAL CONDITIONS", expanded=True):
        init_angle = st.slider("Release Angle [deg]", -90.0, 90.0, 45.0)
        friction = st.slider("Damping Coeff (b)", 0.00, 1.00, 0.05)

    st.markdown("---")
    if not st.session_state.simulation_active:
        if st.button("EXECUTE SIMULATION", use_container_width=True, type="primary"):
            if st.session_state.simulation_process:
                try: st.session_state.simulation_process.terminate()
                except: pass
            
            st.session_state.captured_angle = []
            st.session_state.captured_velocity = []
            pd.DataFrame(columns=["Time", "Angle", "Angular_Velocity"]).to_csv("live_data.csv", index=False)
            
            env_vars = os.environ.copy()
            env_vars.update({"INIT_ANGLE": str(init_angle), "FRICTION": str(friction), "MASS": str(mass), "LENGTH": str(length), "GRAVITY": str(gravity)})
            
            st.session_state.lab_mode = "SIMULATION"
            st.session_state.simulation_active = True
            st.session_state.simulation_process = subprocess.Popen([sys.executable, "mock_sensor.py"], env=env_vars)
            st.rerun()
    else:
        if st.button("TERMINATE PROCESS", use_container_width=True):
            if st.session_state.simulation_process:
                st.session_state.simulation_process.terminate()
            st.session_state.simulation_active = False
            st.rerun()

# --- MAIN INTERFACE ---
st.title("PENDULUM DYNAMICS ANALYZER")

# GLOBAL MATH
measured_period = 0.0
if st.session_state.captured_angle:
    df_a = pd.DataFrame(st.session_state.captured_angle).sort_values("Time")
    crests = df_a[df_a["Angle"] > 0]
    if len(crests) >= 2:
        measured_period = (crests["Time"].iloc[-1] - crests["Time"].iloc[0]) / (len(crests) - 1)

tab1, tab2, tab3 = st.tabs(["INSTRUMENTATION", "CALIBRATION", "GRAVITY EXPLORER"])

with tab1:
    is_paused = st.toggle("FREEZE DATA STREAM", value=not st.session_state.simulation_active)
    
    try:
        df = pd.read_csv("live_data.csv")
        if not df.empty:
            df = df.sort_values("Time").reset_index(drop=True)
            df_plot = df.tail(500) if st.session_state.simulation_active else df
            
            # Dark theme plots
            fig_a = px.line(df_plot, x="Time", y="Angle", template="plotly_dark", color_discrete_sequence=['#00d4ff'])
            fig_v = px.line(df_plot, x="Time", y="Angular_Velocity", template="plotly_dark", color_discrete_sequence=['#ff4b4b'])
            
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(fig_a, use_container_width=True)
            with c2: st.plotly_chart(fig_v, use_container_width=True)
            
            # Simplified Actions
            if is_paused:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("AUTO-EXTRACT PEAKS"):
                        for col, store in [("Angle", st.session_state.captured_angle)]:
                            pks, _ = signal.find_peaks(df_plot[col], distance=20, prominence=0.5)
                            for i in pks:
                                row = df_plot.iloc[i]
                                st.session_state.captured_angle.append({"Time": row["Time"], "Angle": row[col]})
                        st.rerun()
                with col_btn2:
                    if st.button("RESET PEAK DATA"):
                        st.session_state.captured_angle = []; st.rerun()
    except: st.info("NO ACTIVE DATA STREAM")

with tab2:
    st.header("SECONDS PENDULUM CALIBRATION")
    m1, m2 = st.columns(2)
    with m1:
        st.metric("MEASURED T", f"{round(measured_period, 4)} s", delta=f"{round(measured_period-2.0, 4)} s", delta_color="inverse")
    with m2:
        if st.button("LOG CALIBRATION TRIAL"):
            st.session_state.cal_notebook.append({"L": length, "T": round(measured_period, 4)})
    
    if st.session_state.cal_notebook:
        st.dataframe(pd.DataFrame(st.session_state.cal_notebook), use_container_width=True)

with tab3:
    st.header("GRAVITY FIELD ANALYSIS")
    if measured_period > 0:
        calc_g = (4 * (np.pi**2) * length) / (measured_period**2)
        st.metric("CALCULATED g", f"{round(calc_g, 3)} m/s²")
        if st.button("COMMIT DATA TO NOTEBOOK"):
            st.session_state.lab_notebook.append({"L": length, "T": round(measured_period, 4), "calc_g": round(calc_g, 3)})
    
    if st.session_state.lab_notebook:
        st.table(pd.DataFrame(st.session_state.lab_notebook))

if st.session_state.simulation_active and not is_paused:
    time.sleep(0.05)
    st.rerun()