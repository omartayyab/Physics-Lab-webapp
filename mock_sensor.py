import pandas as pd
import numpy as np
import time
import os

# --- 1. READ SETTINGS FROM UI ---
# The script looks for the environment variables that app.py passes to it.
# If you run this script manually (without app.py), it defaults to 45 deg and 0.1 friction.
init_angle = float(os.environ.get("INIT_ANGLE", 45.0))
friction = float(os.environ.get("FRICTION", 0.1))

# --- 2. PHYSICS SETUP ---
theta = np.radians(init_angle)
omega = 0.0
dt = 0.1  # The time step (simulates a 10Hz sensor)
g = 9.81
L = 1.0

start_time = time.time()

# --- 3. RUN LOOP ---
while True:
    # Calculate elapsed time
    t = time.time() - start_time
    
    # Simple pendulum physics math (Euler method)
    # alpha is angular acceleration
    alpha = -(g/L) * np.sin(theta) - friction * omega
    omega += alpha * dt
    theta += omega * dt
    
    # Format the new data row
    new_data = pd.DataFrame({
        "Time": [round(t, 2)], 
        "Angle": [round(np.degrees(theta), 2)], 
        "Angular_Velocity": [round(np.degrees(omega), 2)]
    })
    
    # Append to CSV. 
    # 'header=not os.path.exists()' ensures we only write column names if the file is brand new.
    new_data.to_csv("live_data.csv", mode='a', header=not os.path.exists("live_data.csv"), index=False)
    
    # Pause to simulate real-time sensor data streaming
    time.sleep(dt)