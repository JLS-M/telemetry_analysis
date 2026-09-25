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
        title=f"Select {outing_name} - MoTeC Telemetry Files",
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