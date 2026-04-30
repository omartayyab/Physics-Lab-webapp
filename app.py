import streamlit as st
import pandas as pd
import plotly.express as px
import time
import scipy.signal as signal
import numpy as np
import subprocess
import os
import sys

st.set_page_config(page_title="Pendulum Physics Lab", layout="wide")

# --- 1. INITIALIZATION ---
if "captured_angle" not in st.session_state:
    st.session_state.captured_angle = []
if "captured_velocity" not in st.session_state:
    st.session_state.captured_velocity = []
if "lab_notebook" not in st.session_state:
    st.session_state.lab_notebook = []
if "cal_notebook" not in st.session_state:
    st.session_state.cal_notebook = []
if "lab_mode" not in st.session_state:
    st.session_state.lab_mode = "Idle"
if "simulation_active" not in st.session_state:
    st.session_state.simulation_active = False
if "simulation_process" not in st.session_state:
    st.session_state.simulation_process = None

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("🎓 Learning Outcomes")
    st.info("""
    **Practical 14:** Study length effect on $T$ and calculate 'g'.  
    **Practical 15:** Prove period is independent of mass and amplitude.
    """)
    st.markdown("---")

    st.header("🧪 Simulation Settings")
    is_physical = st.session_state.lab_mode == "Physical"
    init_angle = st.slider("Initial Release Angle [°]", -90, 90, 45, disabled=is_physical)
    friction = st.slider("Friction (Damping coeff)", 0.0, 1.0, 0.1, step=0.01, disabled=is_physical)
    
    st.markdown("---")
    st.header("⚙️ Global Parameters")
    length = st.number_input("Pendulum Length (L) [m]", value=0.2, min_value=0.1)
    mass = st.number_input("Mass of Pendulum (m) [kg]", value=0.5, min_value=0.01)
    gravity = st.number_input("Gravity (g) [m/s²]", value=9.81, min_value=0.0)
    
    st.markdown("---")
    st.header("🔬 Experiment Control")
    if not st.session_state.simulation_active:
        if st.button("🟢 Start Virtual Simulation", use_container_width=True):
            if st.session_state.simulation_process is not None:
                try:
                    st.session_state.simulation_process.terminate()
                    st.session_state.simulation_process.wait()
                except:
                    pass
            
            st.session_state.captured_angle = []
            st.session_state.captured_velocity = []
            
            pd.DataFrame(columns=["Time", "Angle", "Angular_Velocity"]).to_csv("live_data.csv", index=False)
            
            env_vars = os.environ.copy()
            env_vars.update({
                "INIT_ANGLE": str(init_angle), 
                "FRICTION": str(friction), 
                "MASS": str(mass),
                "LENGTH": str(length),   
                "GRAVITY": str(gravity)  
            })
            
            st.session_state.lab_mode = "Simulation"
            st.session_state.simulation_active = True
            st.session_state.simulation_process = subprocess.Popen([sys.executable, "mock_sensor.py"], env=env_vars)
            st.rerun()
    else:
        if st.button("⏹️ Stop Simulation", use_container_width=True):
            if st.session_state.simulation_process:
                st.session_state.simulation_process.terminate()
                st.session_state.simulation_process.wait()
            st.session_state.simulation_active = False
            st.rerun()
            
    if st.button("🔵 Connect Physical Pendulum", use_container_width=True):
        st.session_state.lab_mode = "Physical"
        st.session_state.simulation_active = False
        st.rerun()

# --- GLOBALLY CALCULATE PERIOD ---
measured_period = 0.0
if st.session_state.captured_angle:
    df_a = pd.DataFrame(st.session_state.captured_angle).sort_values("Time")
    crests = df_a[df_a["Angle"] > 0]
    if len(crests) >= 2:
        total_time = crests["Time"].iloc[-1] - crests["Time"].iloc[0]
        measured_period = total_time / (len(crests) - 1)

# --- 3. MAIN DASHBOARD WITH TABS ---
st.title("Pendulum Physics Lab")
tab1, tab2, tab3 = st.tabs(["🔴 Live Experiment", "⏱️ Pendulum Calibration", "🪐 Gravity Explorer"])

# ==========================================
# TAB 1: LIVE EXPERIMENT
# ==========================================
with tab1:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        if st.session_state.simulation_active:
            st.success(f"LIVE: $L={length}m$, $m={mass}kg$, $\\theta_0={init_angle}^\\circ$")
        elif st.session_state.lab_mode == "Simulation":
            st.info("📊 Data Frozen: Analyze peaks to verify Practical 14 & 15.")
        else:
           st.info("""
            **Welcome to the pendulum activity!**

            * Choose between running a simulation or conducting this experiment using the pendulum in your physics box.
            * Adjust parameters in the sidebar to begin.
            *  Use the Auto-detect peaks button to probe charting points easily.
            * Use the export options to export your data for submission. You can also use plot options to save your plots.
            """)
            
    with col_h2:
        is_paused = st.toggle("⏸️ Pause/Probe", value=not st.session_state.simulation_active, disabled=(st.session_state.lab_mode == "Idle"))

    if st.session_state.lab_mode != "Idle":
        try:
            df = pd.read_csv("live_data.csv")
            if not df.empty:
                df = df.sort_values("Time").reset_index(drop=True)
                df_plot = df.tail(400) if st.session_state.simulation_active else df
                
                fig_a = px.line(df_plot, x="Time", y="Angle", title="Angle (θ) vs Time")
                fig_v = px.line(df_plot, x="Time", y="Angular_Velocity", title="Velocity (ω) vs Time")
                
                for f, store, col, color in [(fig_a, st.session_state.captured_angle, "Angle", "#1f77b4"), 
                                             (fig_v, st.session_state.captured_velocity, "Angular_Velocity", "#ff7f0e")]:
                    f.update_traces(line_color=color)
                    if store:
                        odf = pd.DataFrame(store)
                        f.add_scatter(x=odf["Time"], y=odf[col], mode='markers', marker=dict(color='red', size=12, symbol='x'))
                    
                    f.update_layout(dragmode='select', clickmode='event+select', height=400, showlegend=False)
                    if st.session_state.simulation_active and not is_paused:
                        max_t = df_plot["Time"].max()
                        f.update_layout(xaxis_range=[max(0, max_t - 30), max_t])

                c1, c2 = st.columns(2)
                with c1: ev_a = st.plotly_chart(fig_a, use_container_width=True, on_select="rerun", key="a_plt")
                with c2: ev_v = st.plotly_chart(fig_v, use_container_width=True, on_select="rerun", key="v_plt")

                if is_paused:
                    for ev, store, col in [(ev_a, st.session_state.captured_angle, "Angle"), 
                                           (ev_v, st.session_state.captured_velocity, "Angular_Velocity")]:
                        if ev and "selection" in ev and ev["selection"]["points"]:
                            for p in ev["selection"]["points"]:
                                new_pt = {"Time": round(p["x"], 2), col: round(p["y"], 2)}
                                if not any(abs(pt['Time'] - new_pt['Time']) < 0.05 for pt in store):
                                    store.append(new_pt)
                            st.rerun()

                    st.markdown("---")
                    btn_col1, btn_col2 = st.columns([3, 1])
                    with btn_col1:
                        if st.button("⚡ Auto detect peaks and Tabulate Current View", use_container_width=True):
                            for col, store, prom in [("Angle", st.session_state.captured_angle, 0.5), 
                                                     ("Angular_Velocity", st.session_state.captured_velocity, 1.0)]:
                                pks, _ = signal.find_peaks(df_plot[col], distance=10, prominence=prom, plateau_size=(1, 5))
                                vly, _ = signal.find_peaks(-df_plot[col], distance=10, prominence=prom, plateau_size=(1, 5))
                                for i in np.concatenate([pks, vly]):
                                    row = df_plot.iloc[i]
                                    new_pt = {"Time": round(row["Time"], 2), col: round(row[col], 2)}
                                    if not any(abs(pt['Time'] - new_pt['Time']) < 0.05 for pt in store):
                                        store.append(new_pt)
                            st.rerun()
                    
                    with btn_col2:
                        if st.button("🗑️ Clear All Probes", use_container_width=True):
                            st.session_state.captured_angle = []
                            st.session_state.captured_velocity = []
                            st.rerun()

                t1, t2 = st.columns(2)
                with t1:
                    if st.session_state.captured_angle:
                        st.subheader("📋 Angle Peaks")
                        df_a = pd.DataFrame(st.session_state.captured_angle).sort_values("Time").reset_index(drop=True)
                        df_a.insert(0, "ID", [f"A{i+1}" for i in range(len(df_a))])
                        st.data_editor(df_a, use_container_width=True, disabled=["ID"], key="ta")
                        
                        csv_a = df_a.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Angle Data", data=csv_a, file_name="angle_peaks.csv", mime="text/csv", use_container_width=True)
                        
                with t2:
                    if st.session_state.captured_velocity:
                        st.subheader("📋 Velocity Peaks")
                        df_v = pd.DataFrame(st.session_state.captured_velocity).sort_values("Time").reset_index(drop=True)
                        df_v.insert(0, "ID", [f"V{i+1}" for i in range(len(df_v))])
                        st.data_editor(df_v, use_container_width=True, disabled=["ID"], key="tv")
                        
                        csv_v = df_v.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Velocity Data", data=csv_v, file_name="velocity_peaks.csv", mime="text/csv", use_container_width=True)

        except Exception as e:
            st.info("Waiting for data stream...")

# ==========================================
# TAB 2: CALIBRATION
# ==========================================
with tab2:
    st.subheader("Challenge: The Seconds Pendulum")
    st.markdown("The time period ($T$) of a simple pendulum is governed by its length ($L$) and gravity ($g$):")
    st.latex(r"T = 2\pi \sqrt{\frac{L}{g}}")
    st.markdown("""
    A **Seconds Pendulum** is a pendulum whose period is precisely able to keep time. Meaning with each tick tock of the clock we measure seocnds! A well calibrated hororoligcal machine will tune 
    its period to be exactly, **2.0 seconds**. (taking exactly 1 second for the tick and another 1 second for the tock). 
    Now its your job to ensure proper time keeping by calibrating your pendulum to keep seconds,
                            
    * Adjust the **Length (L)** in the sidebar until your desired value is reached.
    * Repeat until the error is minimized.
    * How often does this clock need to calibrated?
                
    """)
    
    if measured_period > 0:
        st.metric("Measured Time Period (T)", f"{round(measured_period, 3)} s")
        if abs(measured_period - 2.0) < 0.05:
            st.balloons()
            st.success("Perfectly Calibrated!")
        else:
            st.warning(f"Off by {round(abs(2.0 - measured_period), 3)}s. Adjust Length!")
    else:
        st.info("Probe at least two peaks on the SAME side (e.g., top peaks) in the Live tab to calculate a full period.")

    st.markdown("### 📝 Calibration Tracker")
    st.write("Click below to log your current Length and Measured Period directly from the app.")
    
    if measured_period > 0:
        error_val = abs(2.0 - measured_period)
        if st.button(f"➕ Log Attempt: L = {length}m | T = {round(measured_period, 3)}s"):
            st.session_state.cal_notebook.append({
                "Length (m)": length,
                "Period (s)": round(measured_period, 3),
                "Error (s)": round(error_val, 3)
            })
            st.rerun()
    else:
        st.button("➕ Log Attempt", disabled=True)

    if st.session_state.cal_notebook:
        df_cal = pd.DataFrame(st.session_state.cal_notebook)
        st.table(df_cal)
        
        # --- NEW: CSV Export & Clear Side-by-Side ---
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            csv_cal = df_cal.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Calibration Data", data=csv_cal, file_name="calibration_tracker.csv", mime="text/csv", use_container_width=True)
        with col_btn2:
            if st.button("🗑️ Clear Tracker", use_container_width=True):
                st.session_state.cal_notebook = []
                st.rerun()

# ==========================================
# TAB 3: GRAVITY EXPLORER 
# ==========================================
with tab3:
    st.subheader("Mission: Hypothetical Planet Exploration")
    st.write("In this mode, assume the 'Gravity' parameter in the sidebar is unknown.")
    st.latex(r"g = \frac{4\pi^2 L}{T^2}")
    
    with st.expander("Step-by-Step Instructions"):
        st.write("1. Set a Length ($L$) in the sidebar and run the simulation.")
        st.write("2. In the Live Tab, probe two consecutive peaks on the same side to find the Period ($T$).")
        st.write("3. Click the button below to instantly calculate and save 'g' to your notebook.")
        st.write("4. Repeat with different lengths to find an average value for 'g'.")

    st.markdown("### 📝 Digital Lab Notebook")
    
    if measured_period > 0:
        calc_g = (4 * (np.pi**2) * length) / (measured_period**2)
        st.metric("Currently Calculated 'g'", f"{round(calc_g, 2)} m/s²")
        
        if st.button(f"➕ Add to Notebook: L = {length}m | T = {round(measured_period, 3)}s"):
            st.session_state.lab_notebook.append({
                "Length (m)": length,
                "Period (s)": round(measured_period, 3),
                "Calculated g (m/s²)": round(calc_g, 2)
            })
            st.rerun()
    else:
        st.info("Probe peaks in the Live tab to measure a period before logging.")
        st.button("➕ Add to Notebook", disabled=True)

    if st.session_state.lab_notebook:
        st.markdown("#### Saved Data")
        df_notebook = pd.DataFrame(st.session_state.lab_notebook)
        st.table(df_notebook)
        
        avg_g = df_notebook["Calculated g (m/s²)"].mean()
        st.info(f"**Average Calculated 'g': {round(avg_g, 2)} m/s²**")
        
        error = abs(gravity - avg_g) / gravity * 100
        if error < 2:
            st.success(f"Excellent! Your average calculation is {round(100-error, 2)}% accurate.")
        else:
            st.error(f"Your average value is off by {round(error, 1)}%. Run more trials!")
            
        # --- NEW: CSV Export & Clear Side-by-Side ---
        col_btn3, col_btn4 = st.columns(2)
        with col_btn3:
            csv_nb = df_notebook.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Notebook Data", data=csv_nb, file_name="gravity_notebook.csv", mime="text/csv", use_container_width=True)
        with col_btn4:
            if st.button("🗑️ Clear Notebook", use_container_width=True):
                st.session_state.lab_notebook = []
                st.rerun()

# --- 4. RERUN LOOP ---
if st.session_state.simulation_active and not is_paused:
    time.sleep(0.1)
    st.rerun()