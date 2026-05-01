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

# Kept the monospace font for a "Scientific" feel, no forced colors.
st.markdown("""
    <style>
    .stApp { font-family: 'Courier New', Courier, monospace; }
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
        # Disable initial conditions if they are doing the physical lab
        is_physical = st.session_state.lab_mode == "Physical"
        init_angle = st.slider("Release Angle [deg]", -90.0, 90.0, 45.0, disabled=is_physical)
        friction = st.slider("Damping Coeff (b)", 0.00, 1.00, 0.05, disabled=is_physical)

    st.markdown("---")
    
    # UI FIX: Brought back the physical connection button alongside the simulation button
    if not st.session_state.simulation_active:
        if st.button("EXECUTE SIMULATION", use_container_width=True, type="primary", key="start_sim_btn"):
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
            
        if st.button("CONNECT PHYSICAL PENDULUM", use_container_width=True, key="connect_phys_btn"):
            st.session_state.lab_mode = "Physical"
            st.session_state.simulation_active = False
            st.rerun()
            
    else:
        if st.button("TERMINATE PROCESS", use_container_width=True, key="stop_sim_btn"):
            if st.session_state.simulation_process:
                st.session_state.simulation_process.terminate()
            st.session_state.simulation_active = False
            st.session_state.lab_mode = "IDLE" # Reset to IDLE so the welcome screen comes back
            st.rerun()

# --- MAIN INTERFACE ---
st.title("PENDULUM DYNAMICS ANALYZER")

# GLOBAL MATH (Bulletproof Period Calculation)
measured_period = 0.0
if st.session_state.captured_angle:
    df_a = pd.DataFrame(st.session_state.captured_angle).sort_values("Time")
    crests = df_a[df_a["Angle"] > 5.0] 
    
    if len(crests) >= 2:
        valid_crests = [crests.iloc[0]]
        for i in range(1, len(crests)):
            if crests.iloc[i]["Time"] - valid_crests[-1]["Time"] > 0.5:
                valid_crests.append(crests.iloc[i])
                
        if len(valid_crests) >= 2:
            measured_period = (valid_crests[-1]["Time"] - valid_crests[0]["Time"]) / (len(valid_crests) - 1)

tab1, tab2, tab3 = st.tabs(["INSTRUMENTATION", "CALIBRATION", "GRAVITY EXPLORER"])

# ==========================================
# TAB 1: INSTRUMENTATION
# ==========================================
with tab1:
    if st.session_state.lab_mode == "IDLE":
        st.info("""
        **Welcome to the pendulum activity!**

        * Choose between running a simulation or conducting this experiment using the pendulum in your physics box.
        * Adjust parameters in the sidebar to begin.
        * Use the Auto-detect peaks button to probe charting points easily.
        * Use the export options to export your data for submission. You can also use plot options to save your plots.
        """)
    else:
        try:
            df = pd.read_csv("live_data.csv")
            if not df.empty:
                df = df.sort_values("Time").reset_index(drop=True)
                df_plot = df.tail(400) if st.session_state.simulation_active else df
                
                # Dynamic plots
                fig_a = px.line(df_plot, x="Time", y="Angle", color_discrete_sequence=['#00a8e8'])
                fig_v = px.line(df_plot, x="Time", y="Angular_Velocity", color_discrete_sequence=['#ff4b4b'])
                
                # Draw the points on the graphs
                for f, store, col in [(fig_a, st.session_state.captured_angle, "Angle"), 
                                      (fig_v, st.session_state.captured_velocity, "Angular_Velocity")]:
                    if store:
                        odf = pd.DataFrame(store)
                        f.add_scatter(x=odf["Time"], y=odf[col], mode='markers', marker=dict(color='#ff9900', size=12, symbol='x'), name="Peaks")
                    
                    f.update_layout(dragmode='select', clickmode='event+select', height=400, showlegend=False)
                    if st.session_state.simulation_active:
                        max_t = df_plot["Time"].max()
                        f.update_layout(xaxis_range=[max(0, max_t - 30), max_t])

                c1, c2 = st.columns(2)
                with c1: ev_a = st.plotly_chart(fig_a, use_container_width=True, on_select="rerun", key="chart_angle")
                with c2: ev_v = st.plotly_chart(fig_v, use_container_width=True, on_select="rerun", key="chart_vel")
                
                # Manual point selection
                for ev, store, col in [(ev_a, st.session_state.captured_angle, "Angle"), 
                                       (ev_v, st.session_state.captured_velocity, "Angular_Velocity")]:
                    if ev and "selection" in ev and ev["selection"]["points"]:
                        for p in ev["selection"]["points"]:
                            new_pt = {"Time": round(p["x"], 2), col: round(p["y"], 2)}
                            if not any(abs(pt['Time'] - new_pt['Time']) < 0.05 for pt in store):
                                store.append(new_pt)

                st.markdown("---")
                btn_col1, btn_col2 = st.columns([3, 1])
                with btn_col1:
                    if st.button("⚡ Auto detect peaks and Tabulate Current View", use_container_width=True, key="t1_auto_btn"):
                        st.session_state.captured_angle.clear()
                        st.session_state.captured_velocity.clear()
                        
                        pks_a, _ = signal.find_peaks(df_plot["Angle"], distance=20, prominence=0.5)
                        vly_a, _ = signal.find_peaks(-df_plot["Angle"], distance=20, prominence=0.5)
                        for i in np.concatenate([pks_a, vly_a]):
                            row = df_plot.iloc[i]
                            st.session_state.captured_angle.append({"Time": round(row["Time"], 2), "Angle": round(row["Angle"], 2)})
                            
                        pks_v, _ = signal.find_peaks(df_plot["Angular_Velocity"], distance=20, prominence=1.0)
                        vly_v, _ = signal.find_peaks(-df_plot["Angular_Velocity"], distance=20, prominence=1.0)
                        for i in np.concatenate([pks_v, vly_v]):
                            row = df_plot.iloc[i]
                            st.session_state.captured_velocity.append({"Time": round(row["Time"], 2), "Angular_Velocity": round(row["Angular_Velocity"], 2)})
                        st.rerun()
                            
                with btn_col2:
                    if st.button("🗑️ Clear All Probes", use_container_width=True, key="t1_clear_btn"):
                        st.session_state.captured_angle.clear()
                        st.session_state.captured_velocity.clear()
                        st.rerun()

                # PERMANENTLY VISIBLE TABLES
                t1, t2 = st.columns(2)
                with t1:
                    if st.session_state.captured_angle:
                        st.subheader("📋 Angle Peaks")
                        df_a = pd.DataFrame(st.session_state.captured_angle).sort_values("Time").reset_index(drop=True)
                        df_a.insert(0, "ID", [f"A{i+1}" for i in range(len(df_a))])
                        st.data_editor(df_a, use_container_width=True, disabled=["ID"], key="t1_angle_table")
                        
                        csv_a = df_a.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Angle Data", data=csv_a, file_name="angle_peaks.csv", mime="text/csv", use_container_width=True, key="t1_dl_angle")
                        
                with t2:
                    if st.session_state.captured_velocity:
                        st.subheader("📋 Velocity Peaks")
                        df_v = pd.DataFrame(st.session_state.captured_velocity).sort_values("Time").reset_index(drop=True)
                        df_v.insert(0, "ID", [f"V{i+1}" for i in range(len(df_v))])
                        st.data_editor(df_v, use_container_width=True, disabled=["ID"], key="t1_vel_table")
                        
                        csv_v = df_v.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Velocity Data", data=csv_v, file_name="velocity_peaks.csv", mime="text/csv", use_container_width=True, key="t1_dl_vel")
                            
        except Exception as e: 
            st.info("NO ACTIVE DATA STREAM")

# ==========================================
# TAB 2: CALIBRATION
# ==========================================
with tab2:
    st.header("SECONDS PENDULUM CALIBRATION")
    
    with st.expander("Show Lab Instructions", expanded=False):
        st.markdown("The time period ($T$) of a simple pendulum is governed by its length ($L$) and gravity ($g$):")
        st.latex(r"T = 2\pi \sqrt{\frac{L}{g}}")
        st.markdown("""
        A **Seconds Pendulum** is a pendulum whose period is precisely able to keep time. Meaning with each tick tock of the clock we measure seconds! A well-calibrated horological machine will tune its period to be exactly **2.0 seconds** (taking exactly 1 second for the tick and another 1 second for the tock). 
        Now it's your job to ensure proper time keeping by calibrating your pendulum to keep seconds:
                                
        * Adjust the **Length (L)** in the sidebar until your desired value is reached.
        * Repeat until the error is minimized.
        * How often does this clock need to be calibrated?
        """)
    
    col_t2_1, col_t2_2 = st.columns(2)
    with col_t2_1:
        with st.container(border=True):
            st.metric("MEASURED T", f"{round(measured_period, 4)} s")
            if measured_period > 0:
                st.caption(f"Δ Target (2.0s): {round(abs(measured_period-2.0), 4)} s")
            else:
                st.caption("Awaiting data points...")
    with col_t2_2:
        with st.container(border=True):
            st.write("Ready to record?")
            if st.button("LOG CALIBRATION TRIAL", disabled=(measured_period == 0), use_container_width=True, key="t2_log_btn"):
                st.session_state.cal_notebook.append({"L": length, "T": round(measured_period, 4)})
                st.rerun()
    
    if st.session_state.cal_notebook:
        df_cal = pd.DataFrame(st.session_state.cal_notebook)
        st.dataframe(df_cal, use_container_width=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            csv_cal = df_cal.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Calibration Data", data=csv_cal, file_name="calibration_tracker.csv", mime="text/csv", use_container_width=True, key="t2_dl_btn")
        with col_btn2:
            if st.button("🗑️ Clear Tracker", use_container_width=True, key="t2_clear_btn"):
                st.session_state.cal_notebook = []
                st.rerun()

# ==========================================
# TAB 3: GRAVITY EXPLORER
# ==========================================
with tab3:
    st.header("GRAVITY FIELD ANALYSIS")
    
    with st.expander("Show Lab Instructions", expanded=False):
        st.markdown("In this mode, assume the 'Gravity' parameter in the sidebar is unknown.")
        st.latex(r"g = \frac{4\pi^2 L}{T^2}")
    
    if measured_period > 0:
        calc_g = (4 * (np.pi**2) * length) / (measured_period**2)
        
        col_t3_1, col_t3_2 = st.columns(2)
        with col_t3_1:
            with st.container(border=True):
                st.metric("CALCULATED g", f"{round(calc_g, 3)} m/s²")
                st.caption(f"Using L={length}m, T={round(measured_period, 3)}s")
        with col_t3_2:
            with st.container(border=True):
                st.write("Save to Notebook")
                if st.button("COMMIT DATA TO NOTEBOOK", use_container_width=True, key="t3_commit_btn"):
                    st.session_state.lab_notebook.append({"L": length, "T": round(measured_period, 4), "calc_g": round(calc_g, 3)})
                    st.rerun()
    else:
        st.info("Probe peaks in the Live tab to measure a period before logging.")
        
    if st.session_state.lab_notebook:
        df_notebook = pd.DataFrame(st.session_state.lab_notebook)
        st.table(df_notebook)
        
        col_btn3, col_btn4 = st.columns(2)
        with col_btn3:
            csv_nb = df_notebook.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Notebook Data", data=csv_nb, file_name="gravity_notebook.csv", mime="text/csv", use_container_width=True, key="t3_dl_btn")
        with col_btn4:
            if st.button("🗑️ Clear Notebook", use_container_width=True, key="t3_clear_btn"):
                st.session_state.lab_notebook = []
                st.rerun()

if st.session_state.simulation_active:
    time.sleep(0.05)
    st.rerun()