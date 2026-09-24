import os
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from my_tools.data_processing.telemetry_loader import load_acc_telemetry

# --- TELL PANDAS TO NEVER TRUNCATE COLUMNS ---
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
# --------------------------------------------

# Set default folder path
data_folder_path = os.path.abspath("../../telemetry_data")

# Initialize hidden tkinter root window
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

# Open multi-file selection dialog (askopenfilenames)
file_paths = filedialog.askopenfilenames(
    initialdir=data_folder_path,
    title="Select MoTeC Telemetry Files (Hold Ctrl/Cmd to select multiple)",
    filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
)

root.destroy()

# Check if the user selected any files
if not file_paths:
    print("\nNo files selected. Exiting script.")
    exit()

print(f"\n{len(file_paths)} file(s) selected.")


# ------------------------------------------------------------------
# Helper Function to switch between 'time' or 'distance'
# ------------------------------------------------------------------
def get_channel_x(df, channel_name, mode="time"):
    ch_time = df[f"{channel_name}_Time"].dropna().values

    if mode.lower() == "time":
        return ch_time
    elif mode.lower() == "distance":
        matrix = df["Time_Distance_Matrix"].iloc[0]
        return np.interp(ch_time, matrix[:, 0], matrix[:, 1])


# Set plot mode here: 'time' or 'distance'
PLOT_MODE = "time"

# Palette for multi-lap raw/filtered pairs
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

# --- SETUP PLOT ---
plt.figure(figsize=(12, 6))

# Loop over all selected telemetry files
for idx, path in enumerate(file_paths):
    filename = os.path.basename(path)
    print(f"\nLoading: {filename}")

    df = load_acc_telemetry(path)

    # Extract clean throttle position data and corresponding time vector
    throttle_data = df["Throttle"].dropna().values
    throttle_time = df["Throttle_Time"].dropna().values

    if len(throttle_data) < 2:
        print(f"Skipping {filename}: insufficient throttle data.")
        continue

    # Get X vector (Time or Distance) using the helper
    throttle_x = get_channel_x(df, "Throttle", mode=PLOT_MODE)

    # --- SAVITZKY-GOLAY FILTERING ---
    dt = np.diff(throttle_time, prepend=throttle_time[0])
    mean_dt = np.mean(dt[1:]) if len(dt) > 1 else 0.02
    fs = 1.0 / mean_dt if mean_dt > 0 else 50.0

    # Set window length to ~0.2s of data (must be an odd integer)
    window_len = int(round(0.2 * fs))
    if window_len % 2 == 0:
        window_len += 1
    window_len = max(
        5,
        min(
            window_len,
            len(throttle_data) - 1
            if len(throttle_data) % 2 != 0
            else len(throttle_data) - 2,
        ),
    )

    poly_order = 2
    throttle_filtered = savgol_filter(
        throttle_data, window_length=window_len, polyorder=poly_order
    )

    # Assign base color for the lap
    color = colors[idx % len(colors)]

    # 1. Plot Raw Throttle (dashed / semi-transparent)
    plt.plot(
        throttle_x,
        throttle_data,
        label=f"{filename} (Raw)",
        color=color,
        linestyle="--",
        linewidth=1.2,
        alpha=0.5,
    )

    # 2. Plot Filtered Throttle (solid line)
    plt.plot(
        throttle_x,
        throttle_filtered,
        label=f"{filename} (Filtered)",
        color=color,
        linewidth=1.8,
        alpha=0.9,
    )

# --- FORMAT PLOT ---
plt.title(f"Throttle Position (Raw vs. Filtered) vs {PLOT_MODE.capitalize()}")
plt.xlabel("Lap Distance (m)" if PLOT_MODE == "distance" else "Lap Time (s)")
plt.ylabel("Throttle Position (%)")
plt.ylim(-5, 105)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="best", fontsize="small")
plt.tight_layout()

fig = plt.gcf()
fig.canvas.manager.set_window_title("Throttle Filter Overlay")
plt.show()