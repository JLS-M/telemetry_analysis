import os
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# Open multi-file selection dialog
file_paths = filedialog.askopenfilenames(
    initialdir=data_folder_path,
    title="Select MoTeC Telemetry Files (Hold Ctrl/Cmd to select multiple)",
    filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
)

root.destroy()

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


# ------------------------------------------------------------------
# MoTeC-style Moving Average Filter
# ------------------------------------------------------------------
def motec_smooth(data, num_samples=5):
    """
    Smooths data using a moving average over 'num_samples',
    matching MoTeC i2's default channel smoothing behavior.
    """
    if num_samples <= 1:
        return data
    # Use mode='same' to keep output vector length equal to input vector
    window = np.ones(num_samples) / num_samples
    return np.convolve(data, window, mode="same")


# --- SETTINGS ---
PLOT_MODE = "time"  # 'time' or 'distance'
SMOOTH_SAMPLES = 9  # Number of samples for MoTeC-style smoothing (e.g. 5 to 10 samples)

# Palette for multi-lap raw/filtered pairs
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

# --- SETUP PLOT ---
plt.figure(figsize=(12, 6))

for idx, path in enumerate(file_paths):
    filename = os.path.basename(path)
    print(f"\nLoading: {filename}")

    df = load_acc_telemetry(path)

    throttle_data = df["Throttle"].dropna().values
    throttle_time = df["Throttle_Time"].dropna().values

    if len(throttle_data) < 2:
        print(f"Skipping {filename}: insufficient throttle data.")
        continue

    throttle_x = get_channel_x(df, "Throttle", mode=PLOT_MODE)

    # Apply MoTeC-style moving average
    throttle_filtered = motec_smooth(throttle_data, num_samples=SMOOTH_SAMPLES)

    color = colors[idx % len(colors)]

    # 1. Plot Raw Throttle
    plt.plot(
        throttle_x,
        throttle_data,
        label=f"{filename} (Raw)",
        color=color,
        linestyle="--",
        linewidth=1.2,
        alpha=0.5,
    )

    # 2. Plot Filtered Throttle
    plt.plot(
        throttle_x,
        throttle_filtered,
        label=f"{filename} (MoTeC Smooth {SMOOTH_SAMPLES} samples)",
        color=color,
        linewidth=1.8,
        alpha=0.9,
    )

# --- FORMAT PLOT ---
plt.title(
    f"Throttle Position (Raw vs. MoTeC Smooth) vs {PLOT_MODE.capitalize()}"
)
plt.xlabel("Lap Distance (m)" if PLOT_MODE == "distance" else "Lap Time (s)")
plt.ylabel("Throttle Position (%)")
plt.ylim(-5, 105)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="best", fontsize="small")
plt.tight_layout()

fig = plt.gcf()
fig.canvas.manager.set_window_title("MoTeC Throttle Smoothing Overlay")
plt.show()