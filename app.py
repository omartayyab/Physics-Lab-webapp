import streamlit as st
import pandas as pd
import plotly.express as px
import time
import scipy.signal as signal
import numpy as np
import subprocess
import os

st.set_page_config(page_title="Pendulum Physics Lab", layout="wide")

# --- 1. INITIALIZATION ---
if "captured_angle" not in st.session_state:
    st.session_state.captured_angle = []
if "captured_velocity" not in st.session_state:
    st.session_state.captured_velocity = []
if "lab_mode" not in st.session_state:
    st.session_state.lab_mode = "Idle"
if "simulation_active" not in st.session_state:
    st.session_state.simulation_active = False
if "simulation_process" not in st.session_state:
    st.session_state.simulation_process = None

# --- 2. SIDEBAR (Properly Organized) ---
with st.sidebar:
    # 1. PARAMETERS (Defined first so the buttons can read them)
    st.header("🧪 Simulation Settings")
    is_physical = st.session_state.lab_mode == "Physical"
    init_angle = st.slider("Initial Release Angle [°]", -90, 90, 45, disabled=is_physical)
    friction = st.slider("Friction (Damping coeff)", 0.0, 1.0, 0.1, step=0.01, disabled=is_physical)
    
    st.markdown("---")
    st.header("⚙️ Global Parameters")
    length = st.number_input("Pendulum Length (L) [m]", value=1.0, min_value=0.1)
    gravity = st.number_input("Gravity (g) [m/s²]", value=9.81, min_value=0.0)
    
    st.markdown("---")
    
    # 2. EXPERIMENT CONTROLS (Action buttons at the bottom)
    st.header("🔬 Experiment Control")
    if not st.session_state.simulation_active:
        if st.button("🟢 Start Virtual Simulation", use_container_width=True):
            # Zombie Killer
            try:
                os.system("pkill -f mock_sensor.py")
            except:
                pass
            time.sleep(0.1)
            
            # Reset CSV
            pd.DataFrame(columns=["Time", "Angle", "Angular_Velocity"]).to_csv("live_data.csv", index=False)
            
            # PASS UI VARIABLES TO THE SENSOR
            env_vars = os.environ.copy()
            env_vars["INIT_ANGLE"] = str(init_angle)
            env_vars["FRICTION"] = str(friction)
            
            st.session_state.lab_mode = "Simulation"
            st.session_state.simulation_active = True
            st.session_state.simulation_process = subprocess.Popen(["python", "mock_sensor.py"], env=env_vars)
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

# --- 3. MAIN UI ---
status_icon = "🟢" if st.session_state.lab_mode == "Simulation" else "🔵" if st.session_state.lab_mode == "Physical" else "⚪"
st.title(f"Pendulum Lab - {status_icon} {st.session_state.lab_mode}")

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    if st.session_state.simulation_active:
        st.success(f"LIVE: Simulating from T=0s | θ₀={init_angle}° | Friction={friction}")
    elif st.session_state.lab_mode == "Simulation":
        st.info("📊 Data Frozen: Use Crosshairs to Probe Peaks")
    else:
        st.info("Adjust parameters and select a mode to begin.")

with col_h2:
    is_paused = st.toggle("⏸️ Pause/Probe", value=not st.session_state.simulation_active, disabled=(st.session_state.lab_mode == "Idle"))

# --- 4. DATA & PLOTTING ---
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

            # --- 5. PEAK CAPTURE & ACTION BUTTONS ---
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
                    if st.button("⚡ Auto-Tabulate Current View", use_container_width=True):
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

            # --- 6. CLEAN DATA TABLES ---
            t1, t2 = st.columns(2)
            with t1:
                if st.session_state.captured_angle:
                    st.subheader("📋 Angle Peaks")
                    df_a = pd.DataFrame(st.session_state.captured_angle).sort_values("Time").reset_index(drop=True)
                    df_a.insert(0, "ID", [f"A{i+1}" for i in range(len(df_a))])
                    st.data_editor(df_a, use_container_width=True, disabled=["ID"], key="ta")
            with t2:
                if st.session_state.captured_velocity:
                    st.subheader("📋 Velocity Peaks")
                    df_v = pd.DataFrame(st.session_state.captured_velocity).sort_values("Time").reset_index(drop=True)
                    df_v.insert(0, "ID", [f"V{i+1}" for i in range(len(df_v))])
                    st.data_editor(df_v, use_container_width=True, disabled=["ID"], key="tv")

    except Exception as e:
        st.info("Fresh Start: Waiting for T=0 sensor data...")

# --- 7. RERUN LOOP ---
if st.session_state.simulation_active and not is_paused:
    time.sleep(0.1)
    st.rerun()