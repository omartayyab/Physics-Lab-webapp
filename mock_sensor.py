import pandas as pd
import numpy as np
import time
import os

init_angle = float(os.environ.get("INIT_ANGLE", 45.0))
friction = float(os.environ.get("FRICTION", 0.1))
L = float(os.environ.get("LENGTH", 1.0))       
g = float(os.environ.get("GRAVITY", 9.81))     

theta_0 = np.radians(init_angle)
omega_n = np.sqrt(g / L) 

start_time = time.time()

# THE FIX: 50Hz resolution instead of 10Hz
dt = 0.02  

while True:
    t = time.time() - start_time
    
    current_theta = theta_0 * np.exp(-friction * t) * np.cos(omega_n * t)
    current_omega = -theta_0 * np.exp(-friction * t) * omega_n * np.sin(omega_n * t)
    
    new_data = pd.DataFrame({
        "Time": [round(t, 2)], 
        "Angle": [round(np.degrees(current_theta), 2)], 
        "Angular_Velocity": [round(np.degrees(current_omega), 2)]
    })
    
    new_data.to_csv("live_data.csv", mode='a', header=not os.path.exists("live_data.csv"), index=False)
    time.sleep(dt)