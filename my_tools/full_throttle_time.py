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


def process_outing_throttle(file_paths, outing_name):
    """Processes telemetry files for an outing and returns average full-throttle percentage."""
    if not file_paths:
        print(f"No files selected for {outing_name}.")
        return None

    print(f"\n--- Processing {outing_name} ({len(file_paths)} file(s)) ---")
    full_throttle_pcts = []

    for path in file_paths:
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
        full_throttle_pcts.append(full_throttle_pct)

        print(
            f"{filename} | Lap Time: {total_lap_time:.2f}s | "
            f"Throttle >= 95%: {full_throttle_time:.2f}s ({full_throttle_pct:.2f}%)"
        )

    if not full_throttle_pcts:
        return None

    avg_pct = float(np.mean(full_throttle_pcts))
    print(
        f"--> {outing_name} Average Full Throttle (>=95%): {avg_pct:.2f}%"
    )
    return avg_pct


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
avg_outing1 = process_outing_throttle(outing1_files, "Outing 1")
avg_outing2 = process_outing_throttle(outing2_files, "Outing 2")

if avg_outing1 is None or avg_outing2 is None:
    print("\nFailed to calculate valid averages for both outings.")
    exit()

# --- STEP 3: PLOT COMPARATIVE BAR CHART (TIGHT FRAMING) ---
labels = ["Outing 1", "Outing 2"]
averages = [avg_outing1, avg_outing2]
colors = ["#1f77b4", "#ff7f0e"]

x_positions = [0, 1]
bar_width = 1.0  # Touch adjacent edges

plt.figure(figsize=(5, 6))
bars = plt.bar(
    x_positions,
    averages,
    color=colors,
    width=bar_width,
    edgecolor="black",
    linewidth=1.2,
)

# Add numeric percentage labels above each bar
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 1.5,
        f"{yval:.2f}%",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=11,
    )

plt.xticks(x_positions, labels, fontsize=11, fontweight="bold")

# Visual styling
plt.title(
    "Full Throttle Duration Comparison (>= 95%)\nOuting 1 vs. Outing 2",
    fontsize=12,
    pad=15,
)
plt.ylabel("Full Throttle Percentage (%)", fontsize=11)
plt.ylim(0, 100)

# --- REDUCE SIDE WHITESPACE ---
plt.xlim(-0.6, 1.6)

plt.grid(axis="y", linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()
