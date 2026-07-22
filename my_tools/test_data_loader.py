import matplotlib.pyplot as plt
import numpy as np  # <-- ADDED
import pandas as pd
from my_tools.data_loader import load_acc_telemetry

# --- TELL PANDAS TO NEVER TRUNCATE COLUMNS ---
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
# --------------------------------------------

file_path = (
    "../telemetry_data/test_2_Silverstone-ford_mustang_gt3-25-2026.07.19-13.23.25.ld"
)

print("\nLoading telemetry data...")
df = load_acc_telemetry(file_path)

print("\n--- Telemetry Loaded Successfully! ---")
print("Data Shape (Rows, Columns):", df.shape)
print("\nFirst 5 rows:")
print(df.head())


# ------------------------------------------------------------------
# ADDED: Helper Function to switch between 'time' or 'distance'
# ------------------------------------------------------------------
def get_channel_x(df, channel_name, mode="time"):
    ch_time = df[f"{channel_name}_Time"].dropna().values

    if mode.lower() == "time":
        return ch_time
    elif mode.lower() == "distance":
        matrix = df["Time_Distance_Matrix"].iloc[0]
        return np.interp(ch_time, matrix[:, 0], matrix[:, 1])


# Set plot mode here: 'time' or 'distance'
PLOT_MODE = "time"  # <-- ADDED

# Drop NaN rows caused by length padding for plotting
speed_data = df[["Speed"]].dropna()
speed_x = get_channel_x(df, "Speed", mode=PLOT_MODE)  # <-- ADDED

# --- SPEED PLOT ---
plt.figure(figsize=(12, 5))

plt.plot(speed_x, speed_data["Speed"] * 3.6, color="#1f77b4", linewidth=1.5)
plt.title(f"Speed vs {PLOT_MODE.capitalize()} - Silverstone Mustang GT3")
plt.xlabel("Lap Distance (m)" if PLOT_MODE == "distance" else "Lap Time (s)")
plt.ylabel("Speed (km/h)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()