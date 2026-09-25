import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np

from my_tools.data_processing.telemetry_loader import load_acc_telemetry
from my_tools.data_processing.telemetry_processor import (
    detect_pre_braking_coasting,
)

DATA_FOLDER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../telemetry_data")
)


def select_telemetry_file():
    """Opens a file dialog to select a single MoTeC telemetry file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        initialdir=DATA_FOLDER_PATH,
        title="Select MoTeC Telemetry File for Coasting Test",
        filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
    )

    root.destroy()
    return file_path


# --- STEP 1: SELECT TELEMETRY FILE ---
file_path = select_telemetry_file()
if not file_path:
    print("No file selected. Exiting script.")
    exit()

filename = os.path.basename(file_path)
print(f"\n--- Loading and Analyzing: {filename} ---")

# --- STEP 2: LOAD TELEMETRY & RUN DETECTION ---
df = load_acc_telemetry(file_path)

# Extract channels
speed = df["Speed"].dropna().values
speed_time = df["Speed_Time"].dropna().values
speed_dist = df["Speed_Distance"].dropna().values

# Convert speed to km/h if recorded in m/s
speed_kmh = speed * 3.6 if np.max(speed) < 150.0 else speed

throttle = df["Throttle"].dropna().values
throttle_dist = (
    df["Speed_Distance"].iloc[: len(throttle)].values
    if "Speed_Distance" in df
    else speed_dist[: len(throttle)]
)

brake = df["Brake"].dropna().values
brake_dist = (
    df["Speed_Distance"].iloc[: len(brake)].values
    if "Speed_Distance" in df
    else speed_dist[: len(brake)]
)

# Detect pre-braking coasting events
coasting_events = detect_pre_braking_coasting(df, min_speed_kmh=150.0)
print(f"Detected {len(coasting_events)} pre-braking coasting event(s).")

# --- STEP 3: CONSTRUCT BINARY COASTING VECTOR ALIGNED WITH DISTANCE ---
coasting_signal = np.zeros_like(speed_dist)

for event in coasting_events:
    t_start = event["start_time"]
    t_end = event["end_time"]

    # Binary flag mask corresponding to speed_time vector
    mask = (speed_time >= t_start) & (speed_time <= t_end)
    coasting_signal[mask] = 1.0

# --- STEP 4: RENDER 4 STACKED SUBPLOTS ---
fig, (ax1, ax2, ax3, ax4) = plt.subplots(
    4, 1, figsize=(14, 9), sharex=True, gridspec_kw={"height_ratios": [2, 1, 1.5, 1.5]}
)

# Plot 1: Speed vs Distance
ax1.plot(speed_dist, speed_kmh, color="#1f77b4", linewidth=1.5, label="Speed")
ax1.set_ylabel("Speed (km/h)", fontsize=10, fontweight="bold")
ax1.set_title(f"Pre-Braking Coasting Analysis — {filename}", fontsize=12, pad=12)
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="upper right")

# Plot 2: Pre-Braking Coasting Flag (0 or 1)
ax2.plot(speed_dist, coasting_signal, color="#d62728", linewidth=1.8, label="Coasting Flag")
ax2.set_ylabel("Coasting\n(0 / 1)", fontsize=10, fontweight="bold")
ax2.set_ylim(-0.1, 1.1)
ax2.set_yticks([0, 1])
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="upper right")

# Highlight coasting zones visually across Plot 2
ax2.fill_between(
    speed_dist,
    0,
    coasting_signal,
    where=(coasting_signal == 1),
    color="#d62728",
    alpha=0.3,
)

# Plot 3: Throttle Pedal vs Distance
ax3.plot(throttle_dist, throttle, color="#2ca02c", linewidth=1.5, label="Throttle")
ax3.set_ylabel("Throttle (%)", fontsize=10, fontweight="bold")
ax3.set_ylim(-5, 105)
ax3.grid(True, linestyle="--", alpha=0.6)
ax3.legend(loc="upper right")

# Plot 4: Brake Pedal vs Distance
ax4.plot(brake_dist, brake, color="#ff7f0e", linewidth=1.5, label="Brake")
ax4.set_ylabel("Brake (%)", fontsize=10, fontweight="bold")
ax4.set_xlabel("Lap Distance (m)", fontsize=11, fontweight="bold")
ax4.set_ylim(-5, 105)
ax4.grid(True, linestyle="--", alpha=0.6)
ax4.legend(loc="upper right")

plt.tight_layout()
fig.canvas.manager.set_window_title("Coasting Detection Test")
plt.show()