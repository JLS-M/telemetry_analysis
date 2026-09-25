import os
import numpy as np
from my_tools.data_processing.signal_utils import (
    compute_derivative,
    extract_lap_number,
    motec_smooth,
)
from my_tools.data_processing.telemetry_loader import load_acc_telemetry


def detect_pre_braking_coasting(
    df,
    pedal_threshold=5.0,
    brake_trigger_threshold=5.0,
    max_lookahead_sec=0.5,
    min_speed_kmh=150.0,
):
    """Identifies coasting events that occur specifically before braking entries."""
    throttle = df["Throttle"].dropna().values
    brake = df["Brake"].dropna().values
    speed = df["Speed"].dropna().values
    time = df["Throttle_Time"].dropna().values

    if len(throttle) < 2 or len(brake) < 2 or len(speed) < 2:
        return []

    speed_kmh = speed * 3.6 if np.max(speed) < 120.0 else speed

    is_coasting = (throttle < pedal_threshold) & (brake < pedal_threshold)

    coasting_changes = np.diff(is_coasting.astype(int), prepend=0)
    start_indices = np.where(coasting_changes == 1)[0]
    end_indices = np.where(coasting_changes == -1)[0]

    if len(is_coasting) > 0 and is_coasting[-1]:
        end_indices = np.append(end_indices, len(is_coasting) - 1)

    pre_braking_events = []

    for start_idx, end_idx in zip(start_indices, end_indices):
        coast_start_time = time[start_idx]
        coast_end_time = time[end_idx]
        coast_duration = coast_end_time - coast_start_time

        if coast_duration < 0.02:
            continue

        lookahead_mask = (time >= coast_end_time) & (
            time <= coast_end_time + max_lookahead_sec
        )
        subsequent_brakes = brake[lookahead_mask]

        if not np.any(subsequent_brakes >= brake_trigger_threshold):
            continue

        lookback_mask = (time >= max(0.0, coast_start_time - 1.0)) & (
            time <= coast_start_time
        )
        pre_coast_speeds = speed_kmh[lookback_mask]

        if len(pre_coast_speeds) == 0:
            continue

        entry_speed = speed_kmh[start_idx]
        max_pre_speed = np.max(pre_coast_speeds)

        if (
            entry_speed >= min_speed_kmh
            and abs(entry_speed - max_pre_speed) < 5.0
        ):
            start_dist = (
                float(df["Speed_Distance"].iloc[start_idx])
                if "Speed_Distance" in df
                and start_idx < len(df["Speed_Distance"])
                else None
            )

            pre_braking_events.append(
                {
                    "start_time": float(coast_start_time),
                    "end_time": float(coast_end_time),
                    "duration": float(coast_duration),
                    "entry_speed": float(entry_speed),
                    "start_dist": start_dist,
                }
            )

    return pre_braking_events


def process_outing_throttle(
    file_paths, outing_name, smooth_samples=9, full_throttle_threshold=95.0
):
    """Processes telemetry files for an outing and extracts throttle & coasting performance metrics."""
    if not file_paths:
        print(f"No files selected for {outing_name}.")
        return None

    print(f"\n--- Processing {outing_name} ({len(file_paths)} file(s)) ---")
    lap_data = []

    for idx, path in enumerate(file_paths):
        filename = os.path.basename(path)
        df = load_acc_telemetry(path)

        throttle = df["Throttle"].dropna().values
        throttle_time = df["Throttle_Time"].dropna().values

        if len(throttle) < 2:
            print(f"Skipping {filename}: insufficient throttle data.")
            continue

        total_lap_time = throttle_time[-1] - throttle_time[0]
        dt = np.diff(throttle_time, prepend=throttle_time[0])

        full_throttle_mask = throttle >= full_throttle_threshold
        full_throttle_time = np.sum(dt[full_throttle_mask])
        full_throttle_pct = (full_throttle_time / total_lap_time) * 100.0

        throttle_smoothed = motec_smooth(throttle, num_samples=smooth_samples)
        throttle_speed = compute_derivative(throttle_smoothed, dt)

        positive_application_mask = throttle_speed > 0.0

        if np.any(positive_application_mask):
            avg_throttle_speed = float(
                np.mean(throttle_speed[positive_application_mask])
            )
        else:
            avg_throttle_speed = 0.0

        coasting_events = detect_pre_braking_coasting(df, min_speed_kmh=150.0)
        total_coast_time = sum([e["duration"] for e in coasting_events])

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
                "total_lap_time": total_lap_time,
                "coasting_events": coasting_events,
                "total_coasting_time": total_coast_time,
            }
        )

        print(
            f"{filename} (Lap {lap_num}) | Lap Time: {total_lap_time:.2f}s | "
            f"Throttle >= {full_throttle_threshold:.0f}%: {full_throttle_time:.2f}s ({full_throttle_pct:.2f}%) | "
            f"Pre-Brake Coasting (>150km/h): {total_coast_time:.2f}s ({len(coasting_events)} events)"
        )

    if not lap_data:
        return None

    lap_data.sort(key=lambda x: x["lap_num"])
    avg_pct = float(np.mean([item["pct"] for item in lap_data]))
    print(
        f"--> {outing_name} Average Full Throttle (>={full_throttle_threshold:.0f}%): {avg_pct:.2f}%"
    )

    return {"avg_pct": avg_pct, "laps": lap_data}


def process_outing_brake_dynamics(
    file_paths,
    min_brake_rate=80.0,
    min_release_rate=10.0,
    smooth_samples=9,
    brake_channel="Brake",
    time_channel="Brake_Time",
):
    """Processes telemetry files in a SINGLE PASS to compute both brake application speed and release speed per lap."""
    laps_app, avg_app_speeds = [], []
    laps_rel, avg_rel_speeds = [], []

    for idx, path in enumerate(file_paths, start=1):
        filename = os.path.basename(path)
        df = load_acc_telemetry(path)

        lap_num = extract_lap_number(filename)
        if lap_num is None:
            lap_num = idx

        brake_col = next(
            (c for c in df.columns if c.lower() == brake_channel.lower()), None
        )
        time_col = next(
            (
                c
                for c in df.columns
                if c.lower() in [time_channel.lower(), "speed_time", "time"]
            ),
            None,
        )

        if brake_col and time_col:
            clean_df = df[[brake_col, time_col]].dropna().reset_index(drop=True)
            brakes = clean_df[brake_col].values
            times = clean_df[time_col].values

            if len(brakes) < 2:
                continue

            dt = np.diff(times, prepend=times[0])
            brakes_smoothed = motec_smooth(brakes, num_samples=smooth_samples)
            brake_speed = compute_derivative(brakes_smoothed, dt)

            # Application Speed (Entry)
            active_app_rates = brake_speed[brake_speed >= min_brake_rate]
            if len(active_app_rates) > 0:
                laps_app.append(lap_num)
                avg_app_speeds.append(float(np.mean(active_app_rates)))

            # Release Speed (Trail-braking)
            release_mask = (brake_speed < 0.0) & (
                np.abs(brake_speed) >= min_release_rate
            )
            active_rel_rates = np.abs(brake_speed[release_mask])
            if len(active_rel_rates) > 0:
                laps_rel.append(lap_num)
                avg_rel_speeds.append(float(np.mean(active_rel_rates)))

    # Sort deterministically
    if laps_app:
        laps_app, avg_app_speeds = zip(*sorted(zip(laps_app, avg_app_speeds)))
    if laps_rel:
        laps_rel, avg_rel_speeds = zip(*sorted(zip(laps_rel, avg_rel_speeds)))

    return (
        list(laps_app),
        list(avg_app_speeds),
        list(laps_rel),
        list(avg_rel_speeds),
    )


def process_outing_steering_and_curvature(
    file_paths,
    min_steering_rate=10.0,
    min_lat_acc_g=0.2,
    min_speed_kmh=30.0,
    smooth_samples=9,
):
    """Processes telemetry files in a SINGLE PASS to extract steering speed and trajectory curvature metrics."""
    laps_steer, avg_steer_speeds = [], []
    laps_curv, avg_curvatures = [], []

    steer_aliases = ["steering", "steer", "steerangle", "steering angle", "steer_angle", "steering_angle"]
    speed_aliases = ["speed", "v", "vehicle_speed", "car_speed"]
    lat_acc_aliases = ["g_lat", "lat_g", "acc_lat", "lat_acc", "g_lateral", "lateral_acc"]

    for idx, path in enumerate(file_paths, start=1):
        filename = os.path.basename(path)
        df = load_acc_telemetry(path)

        lap_num = extract_lap_number(filename)
        if lap_num is None:
            lap_num = idx

        steer_col = next((c for c in df.columns if c.lower() in steer_aliases), None)
        v_col = next((c for c in df.columns if c.lower() in speed_aliases), None)
        g_col = next((c for c in df.columns if c.lower() in lat_acc_aliases), None)

        # 1. Process Steering Speed
        time_col = "Steer_Angle_Time" if "Steer_Angle_Time" in df else "Speed_Time"
        if steer_col and time_col in df:
            clean_steer = df[[steer_col, time_col]].dropna().reset_index(drop=True)
            steer_val = clean_steer[steer_col].values
            steer_time = clean_steer[time_col].values

            if len(steer_val) >= 2:
                dt = np.diff(steer_time, prepend=steer_time[0])
                dt[dt <= 0] = 1e-4
                steer_smoothed = motec_smooth(steer_val, num_samples=smooth_samples)
                abs_steer_speed = np.abs(compute_derivative(steer_smoothed, dt))
                active_steer = abs_steer_speed[abs_steer_speed >= min_steering_rate]

                if len(active_steer) > 0:
                    laps_steer.append(lap_num)
                    avg_steer_speeds.append(float(np.mean(active_steer)))

        # 2. Process Trajectory Curvature
        if v_col and g_col:
            clean_curv = df[[v_col, g_col]].dropna().reset_index(drop=True)
            v_raw = clean_curv[v_col].values
            g_raw = clean_curv[g_col].values

            if len(v_raw) >= 2:
                v_ms = v_raw / 3.6 if np.max(v_raw) > 120.0 else v_raw
                is_in_g_units = np.max(np.abs(g_raw)) < 5.0
                g_ms2 = np.abs(g_raw) * 9.81 if is_in_g_units else np.abs(g_raw)
                v_kmh = v_ms * 3.6
                abs_g_units = np.abs(g_raw) if is_in_g_units else np.abs(g_raw) / 9.81

                cornering_mask = (abs_g_units >= min_lat_acc_g) & (v_kmh >= min_speed_kmh)

                if np.any(cornering_mask):
                    v_corner = v_ms[cornering_mask]
                    g_corner = g_ms2[cornering_mask]
                    curvature = g_corner / (v_corner**2)

                    laps_curv.append(lap_num)
                    avg_curvatures.append(float(np.mean(curvature)))

    # Sort deterministically
    if laps_steer:
        laps_steer, avg_steer_speeds = zip(*sorted(zip(laps_steer, avg_steer_speeds)))
    if laps_curv:
        laps_curv, avg_curvatures = zip(*sorted(zip(laps_curv, avg_curvatures)))

    return (
        list(laps_steer),
        list(avg_steer_speeds),
        list(laps_curv),
        list(avg_curvatures),
    )


# --- LEGACY WRAPPERS FOR BACKWARD COMPATIBILITY ---
def process_outing_brake_speed(file_paths, min_brake_rate=80.0, smooth_samples=9, **kwargs):
    laps_app, app_speeds, _, _ = process_outing_brake_dynamics(
        file_paths, min_brake_rate=min_brake_rate, smooth_samples=smooth_samples
    )
    return laps_app, app_speeds


def process_outing_brake_release_speed(file_paths, min_release_rate=10.0, smooth_samples=9, **kwargs):
    _, _, laps_rel, rel_speeds = process_outing_brake_dynamics(
        file_paths, min_release_rate=min_release_rate, smooth_samples=smooth_samples
    )
    return laps_rel, rel_speeds


def process_outing_steering_speed(file_paths, min_steering_rate=10.0, smooth_samples=9, **kwargs):
    laps_steer, steer_speeds, _, _ = process_outing_steering_and_curvature(
        file_paths, min_steering_rate=min_steering_rate, smooth_samples=smooth_samples
    )
    return laps_steer, steer_speeds


def process_outing_trajectory_curvature(file_paths, min_lat_acc_g=0.2, min_speed_kmh=30.0, **kwargs):
    _, _, laps_curv, curvatures = process_outing_steering_and_curvature(
        file_paths, min_lat_acc_g=min_lat_acc_g, min_speed_kmh=min_speed_kmh
    )
    return laps_curv, curvatures