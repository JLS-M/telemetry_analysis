import os
import re
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