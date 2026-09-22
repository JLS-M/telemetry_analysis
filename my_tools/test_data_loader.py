import os
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from my_tools.data_loader import load_acc_telemetry

# --- TELL PANDAS TO NEVER TRUNCATE COLUMNS ---
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
# --------------------------------------------

# Set default folder path
data_folder_path = os.path.abspath("../telemetry_data")

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

# Colors palette for overlaying multiple laps cleanly
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

# --- SETUP PLOT ---
plt.figure(figsize=(12, 5))

# Loop over all selected telemetry files
for idx, path in enumerate(file_paths):
    filename = os.path.basename(path)
    print(f"\nLoading: {filename}")

    df = load_acc_telemetry(path)

    # Extract clean speed data and corresponding X vector
    speed_data = df[["Speed"]].dropna()
    speed_x = get_channel_x(df, "Speed", mode=PLOT_MODE)

    # Assign a color and plot
    color = colors[idx % len(colors)]
    plt.plot(
        speed_x,
        speed_data["Speed"] * 3.6,
        label=filename,
        color=color,
        linewidth=1.5,
        alpha=0.85,
    )

# --- FORMAT PLOT ---
plt.title(f"Speed Overlay vs {PLOT_MODE.capitalize()}")
plt.xlabel("Lap Distance (m)" if PLOT_MODE == "distance" else "Lap Time (s)")
plt.ylabel("Speed (km/h)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(loc="best", fontsize="small")
plt.tight_layout()
plt.show()