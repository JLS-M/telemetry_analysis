# This tool takes two sets of laps and for each of them it calculates:
# 1. Average full-throttle percentage (>= 95%).
# 2. Per-lap full-throttle percentages.
# 3. Average positive throttle application speed (% throttle / second) using
#    a MoTeC-style moving average filter to remove noise prior to taking the derivative.
#
# Plots rendered:
# - Plot 1: Bar chart comparing average full-throttle % per outing.
# - Plot 2: Scatter plot of full-throttle % per individual lap number.
# - Plot 3: Scatter plot of average throttle application speed per individual lap number.

import os
import re
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from my_tools.data_loader import load_acc_telemetry


# Set default folder path
data_folder_path = os.path.abspath("../telemetry_data")


def motec_smooth(data, num_samples=9):
    """Smooths data using a moving average over 'num_samples',

    matching MoTeC i2's default channel smoothing behavior.
    """
    if num_samples <= 1:
        return data
    window = np.ones(num_samples) / num_samples
    return np.convolve(data, window, mode="same")


def extract_lap_number(filename):
    """Extracts the lap number integer from filenames formatted like '...Lap.xxxxx.ld'."""
    base_name = os.path.splitext(filename)[0]
    match = re.search(r"Lap\.(\d+)$", base_name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def get_outing_files(outing_name):
    """Opens a file dialog to select files for a specific outing."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_paths = filedialog.askopenfilenames(
        initialdir=data_folder_path,
        title=f"Select {outing_name} - MoTeC Telemetry Files (Hold Ctrl/Cmd for multiple)",
        filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
    )

    root.destroy()
    return list(file_paths)


def process_outing_throttle(file_paths, outing_name, smooth_samples=9):
    """Processes telemetry files for an outing.

    Returns a dict with:
      - 'avg_pct': float
      - 'laps': list of dicts with 'lap_num', 'filename', 'pct', 'avg_throttle_speed'
    """
    if not file_paths:
        print(f"No files selected for {outing_name}.")
        return None

    print(f"\n--- Processing {outing_name} ({len(file_paths)} file(s)) ---")
    lap_data = []

    for idx, path in enumerate(file_paths):
        filename = os.path.basename(path)
        df = load_acc_telemetry(path)

        # Clean throttle data and corresponding time vector
        throttle = df["Throttle"].dropna().values
        throttle_time = df["Throttle_Time"].dropna().values

        if len(throttle) < 2:
            print(f"Skipping {filename}: insufficient throttle data.")
            continue

        # Total lap time (in seconds) based on Throttle channel duration
        total_lap_time = throttle_time[-1] - throttle_time[0]

        # Calculate precise time deltas (dt) between consecutive samples
        dt = np.diff(throttle_time, prepend=throttle_time[0])

        # Mask for samples where throttle is >= 95%
        full_throttle_mask = throttle >= 95.0

        # Total full-throttle time in seconds
        full_throttle_time = np.sum(dt[full_throttle_mask])

        # Percentage of lap spent at full throttle
        full_throttle_pct = (full_throttle_time / total_lap_time) * 100.0

        # --- MOTEC-STYLE SMOOTHING & THROTTLE SPEED ---
        throttle_smoothed = motec_smooth(throttle, num_samples=smooth_samples)

        # Derivative calculation on smoothed signal
        d_throttle = np.diff(throttle_smoothed, prepend=throttle_smoothed[0])
        safe_dt = np.where(dt == 0, 1e-6, dt)
        throttle_speed = d_throttle / safe_dt  # Unit: % / s

        # Filter for positive application rate (pedal press)
        positive_application_mask = throttle_speed > 0.0

        if np.any(positive_application_mask):
            avg_throttle_speed = float(
                np.mean(throttle_speed[positive_application_mask])
            )
        else:
            avg_throttle_speed = 0.0

        # Extract lap number from filename, fallback to sequential order if missing
        lap_num = extract_lap_number(filename)
        if lap_num is None:
            lap_num = idx + 1
            print(
                f"Warning: Could not extract lap number from '{filename}'. Using index {lap_num}."
            )

        lap_data.append(
            {
                "filename": filename,
                "lap_num": lap_num,
                "pct": full_throttle_pct,
                "avg_throttle_speed": avg_throttle_speed,
            }
        )

        print(
            f"{filename} (Lap {lap_num}) | Lap Time: {total_lap_time:.2f}s | "
            f"Throttle >= 95%: {full_throttle_time:.2f}s ({full_throttle_pct:.2f}%) | "
            f"MoTeC Smooth Speed: {avg_throttle_speed:.2f}%/s"
        )

    if not lap_data:
        return None

    avg_pct = float(np.mean([item["pct"] for item in lap_data]))
    print(f"--> {outing_name} Average Full Throttle (>=95%): {avg_pct:.2f}%")

    return {"avg_pct": avg_pct, "laps": lap_data}


# --- STEP 1: SELECT FILES FOR BOTH OUTINGS ---
outing1_files = get_outing_files("Outing 1")
if not outing1_files:
    print("\nNo files selected for Outing 1. Exiting script.")
    exit()

outing2_files = get_outing_files("Outing 2")
if not outing2_files:
    print("\nNo files selected for Outing 2. Exiting script.")
    exit()

# --- STEP 2: PROCESS TELEMETRY DATA ---
SMOOTH_SAMPLES = 9

data_outing1 = process_outing_throttle(
    outing1_files, "Outing 1", smooth_samples=SMOOTH_SAMPLES
)
data_outing2 = process_outing_throttle(
    outing2_files, "Outing 2", smooth_samples=SMOOTH_SAMPLES
)

if data_outing1 is None or data_outing2 is None:
    print("\nFailed to calculate valid averages for both outings.")
    exit()

# --- STEP 3: PLOT CHARTS (3-PANEL LAYOUT) ---
colors = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 5))

outings_data = [("Outing 1", data_outing1), ("Outing 2", data_outing2)]
all_lap_nums = []
for name, data in outings_data:
    all_lap_nums.extend([item["lap_num"] for item in data["laps"]])

min_lap = min(all_lap_nums) if all_lap_nums else 1
max_lap = max(all_lap_nums) if all_lap_nums else 1


# --- PLOT 1: AVERAGE BAR CHART ---
labels = ["Outing 1", "Outing 2"]
averages = [data_outing1["avg_pct"], data_outing2["avg_pct"]]
x_positions = [0, 1]
bar_width = 1.0

bars = ax1.bar(
    x_positions,
    averages,
    color=[colors["Outing 1"], colors["Outing 2"]],
    width=bar_width,
    edgecolor="black",
    linewidth=1.2,
)

for bar in bars:
    yval = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 1.5,
        f"{yval:.2f}%",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=11,
    )

ax1.set_xticks(x_positions)
ax1.set_xticklabels(labels, fontsize=11, fontweight="bold")
ax1.set_title(
    "Average Full Throttle (>= 95%)\nOuting 1 vs. Outing 2",
    fontsize=11,
    pad=15,
)
ax1.set_ylabel("Full Throttle Percentage (%)", fontsize=10)
ax1.set_ylim(0, 100)
ax1.set_xlim(-0.6, 1.6)
ax1.grid(axis="y", linestyle="--", alpha=0.6)


# --- PLOT 2: PER-LAP FULL THROTTLE % SCATTER ---
for name, data in outings_data:
    x_laps = [item["lap_num"] for item in data["laps"]]
    y_pcts = [item["pct"] for item in data["laps"]]

    ax2.scatter(
        x_laps,
        y_pcts,
        color=colors[name],
        label=name,
        s=70,
        alpha=0.85,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )

ax2.set_title("Full Throttle % per Lap\nby Lap Number", fontsize=11, pad=15)
ax2.set_xlabel("Lap Number", fontsize=10)
ax2.set_ylabel("Full Throttle Percentage (%)", fontsize=10)
ax2.set_ylim(0, 100)
ax2.set_xticks(range(min_lap, max_lap + 1))
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="best")


# --- PLOT 3: PER-LAP THROTTLE APPLICATION SPEED SCATTER ---
for name, data in outings_data:
    x_laps = [item["lap_num"] for item in data["laps"]]
    y_speeds = [item["avg_throttle_speed"] for item in data["laps"]]

    ax3.scatter(
        x_laps,
        y_speeds,
        color=colors[name],
        label=name,
        s=70,
        alpha=0.85,
        edgecolor="black",
        linewidth=0.8,
        zorder=3,
    )

ax3.set_title(
    f"Avg Throttle Speed per Lap (MoTeC Smooth {SMOOTH_SAMPLES}smp)\nby Lap Number",
    fontsize=11,
    pad=15,
)
ax3.set_xlabel("Lap Number", fontsize=10)
ax3.set_ylabel("Throttle Speed (% / s)", fontsize=10)

# Scaled Y-axis bounds from 20 to 90 %/s
ax3.set_ylim(20, 90)

ax3.set_xticks(range(min_lap, max_lap + 1))
ax3.grid(True, linestyle="--", alpha=0.6)
ax3.legend(loc="best")


plt.tight_layout()
fig.canvas.manager.set_window_title("Throttle analysis")
plt.show()