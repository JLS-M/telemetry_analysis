import os
import re
import tkinter as tk
from tkinter import filedialog
import numpy as np


def motec_smooth(data, num_samples=9):
    """Smooths data using a moving average over 'num_samples',
    matching MoTeC i2's default channel smoothing behavior.
    """
    if num_samples <= 1:
        return data
    window = np.ones(num_samples) / num_samples
    return np.convolve(data, window, mode="same")


def compute_derivative(signal, dt):
    """Calculates the rate of change (derivative) over a time step vector dt.
    Applies a threshold floor (1e-6) to prevent zero-division errors.
    """
    d_signal = np.diff(signal, prepend=signal[0])
    safe_dt = np.where(dt == 0, 1e-6, dt)
    return d_signal / safe_dt


def extract_lap_number(filename):
    """Extracts the lap number integer from filenames formatted like '...Lap.xxxxx.ld'."""
    base_name = os.path.splitext(filename)[0]
    match = re.search(r"Lap\.(\d+)$", base_name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def get_outing_files(outing_name, initial_dir=None):
    """Opens a file dialog to select multiple MoTeC telemetry files for a specific outing."""
    if initial_dir is None:
        initial_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../telemetry_data")
        )

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_paths = filedialog.askopenfilenames(
        initialdir=initial_dir,
        title=f"Select {outing_name} MoTeC Telemetry Files",
        filetypes=[("MoTeC Log Files", "*.ld"), ("All Files", "*.*")],
    )

    root.destroy()
    return list(file_paths)


def apply_shared_y_limits(ax, *data_lists):
    """Sets Y-axis bounds: 70% of min value and 130% (+30%) of max value across input series."""
    combined = []
    for d in data_lists:
        if d:
            combined.extend(d)

    if combined:
        min_val = min(combined)
        max_val = max(combined)

        # Handle edge cases where values are zero or negative
        y_min = min_val * 0.7 if min_val > 0 else min_val * 1.3
        y_max = max_val * 1.3 if max_val > 0 else max_val * 0.7

        # Handle flat signals where min and max are equal
        if y_min == y_max:
            y_min = y_min * 0.7 if y_min != 0 else -1.0
            y_max = y_max * 1.3 if y_max != 0 else 1.0

        ax.set_ylim(bottom=y_min, top=y_max)


# --- GLOBAL LAP NUMBERING CONFIGURATION ---
# Options:
#   - "straight": Uses the original lap numbers from the files (e.g., Lap 2, 6, 7...).
#   - "sequential": Remaps consecutively: Outing 1 gets 1..N, Outing 2 gets N+1..N+M.
LAP_NUMBERING_MODE = "sequential"


def remap_outing_laps(data_o1, data_o2):
    """
    Sorts laps chronologically and returns remapped x-values (lap numbers)
    for Outing 1 and Outing 2 based on the global LAP_NUMBERING_MODE toggle.
    """
    laps_1 = sorted(data_o1["laps"], key=lambda x: x["lap_num"])
    laps_2 = sorted(data_o2["laps"], key=lambda x: x["lap_num"])

    original_laps_o1 = [item["lap_num"] for item in laps_1]
    original_laps_o2 = [item["lap_num"] for item in laps_2]

    if LAP_NUMBERING_MODE == "sequential":
        count_o1 = len(laps_1)
        seq_laps_o1 = list(range(1, count_o1 + 1))
        seq_laps_o2 = list(range(count_o1 + 1, count_o1 + len(laps_2) + 1))
        return seq_laps_o1, seq_laps_o2, laps_1, laps_2
    else:
        return original_laps_o1, original_laps_o2, laps_1, laps_2


def remap_lap_lists(laps_steer_1, laps_curv_1, laps_steer_2, laps_curv_2):
    """
    For processors returning separate lap lists (like steering),
    applies chronological sequential or straight mapping based on global LAP_NUMBERING_MODE.
    """
    u1 = sorted(list(set((laps_steer_1 or []) + (laps_curv_1 or []))))
    u2 = sorted(list(set((laps_steer_2 or []) + (laps_curv_2 or []))))

    if LAP_NUMBERING_MODE == "sequential":
        map_1 = {lap: idx + 1 for idx, lap in enumerate(u1)}
        offset = len(u1)
        map_2 = {lap: offset + idx + 1 for idx, lap in enumerate(u2)}
    else:
        map_1 = {lap: lap for lap in u1}
        map_2 = {lap: lap for lap in u2}

    mapped_steer_1 = [map_1[l] for l in laps_steer_1] if laps_steer_1 else []
    mapped_curv_1 = [map_1[l] for l in laps_curv_1] if laps_curv_1 else []
    mapped_steer_2 = [map_2[l] for l in laps_steer_2] if laps_steer_2 else []
    mapped_curv_2 = [map_2[l] for l in laps_curv_2] if laps_curv_2 else []

    return mapped_steer_1, mapped_curv_1, mapped_steer_2, mapped_curv_2


# --- CENTRALIZED PLOTTING STYLES ---
PLOT_COLORS = {"Outing 1": "#1f77b4", "Outing 2": "#ff7f0e"}
SCATTER_STYLE = {"s": 70, "alpha": 0.85, "edgecolor": "black", "linewidth": 0.8}

def apply_global_plot_style():
    """Applies centralized typography and layout defaults across all telemetry figures."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 10,
        'axes.titlepad': 12,
    })