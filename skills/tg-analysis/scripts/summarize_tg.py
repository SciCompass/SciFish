#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks


def load_points(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    temps = []
    mass_pct = []
    dtg = []
    for row in payload["points"]:
        t = row.get("temperature_c")
        m = row.get("mass_pct")
        d = row.get("dtg")
        if t is None or m is None:
            continue
        temps.append(float(t))
        mass_pct.append(float(m))
        dtg.append(np.nan if d is None else float(d))
    temp_arr = np.asarray(temps)
    mass_arr = np.asarray(mass_pct)
    dtg_arr = np.asarray(dtg)
    # Duplicate temperatures are common in exported TG tables and destabilize gradients.
    unique_temps, inverse = np.unique(temp_arr, return_inverse=True)
    if len(unique_temps) != len(temp_arr):
        summed_mass = np.zeros_like(unique_temps, dtype=float)
        summed_dtg = np.zeros_like(unique_temps, dtype=float)
        counts_mass = np.zeros_like(unique_temps, dtype=float)
        counts_dtg = np.zeros_like(unique_temps, dtype=float)
        for idx, group in enumerate(inverse):
            if not np.isnan(mass_arr[idx]):
                summed_mass[group] += mass_arr[idx]
                counts_mass[group] += 1
            if not np.isnan(dtg_arr[idx]):
                summed_dtg[group] += dtg_arr[idx]
                counts_dtg[group] += 1
        mass_arr = summed_mass / np.where(counts_mass == 0, 1, counts_mass)
        dtg_arr = summed_dtg / np.where(counts_dtg == 0, 1, counts_dtg)
        dtg_arr[counts_dtg == 0] = np.nan
        temp_arr = unique_temps
    if np.isnan(dtg_arr).all():
        dtg_arr = np.gradient(mass_arr, temp_arr)
    return temp_arr, mass_arr, dtg_arr


def estimate_stages(temps: np.ndarray, mass_pct: np.ndarray, dtg: np.ndarray) -> list[dict[str, float]]:
    if len(dtg) < 5:
        return []
    # Smooth small numerical noise so a broad decomposition event is not split into many peaks.
    kernel = np.ones(5) / 5.0
    smoothed = np.convolve(dtg, kernel, mode="same")
    prominence = max(abs(np.nanmin(smoothed)) * 0.15, 0.03)
    distance = max(5, len(smoothed) // 12)
    peak_indices, _ = find_peaks(-smoothed, prominence=prominence, distance=distance)
    stages = []
    for idx in peak_indices:
        peak_temp = temps[idx]
        left = idx
        right = idx
        threshold = smoothed[idx] * 0.25
        while left > 0 and smoothed[left] < threshold:
            left -= 1
        while right < len(smoothed) - 1 and smoothed[right] < threshold:
            right += 1
        loss = mass_pct[left] - mass_pct[right]
        if loss <= 0.2:
            continue
        stage = (
            round(float(temps[left]), 2),
            round(float(peak_temp), 2),
            round(float(temps[right]), 2),
            round(float(loss), 3),
        )
        if stages and abs(stages[-1]["peak_c"] - stage[1]) < max((temps[-1] - temps[0]) * 0.08, 20):
            continue
        stages.append(
            {
                "start_c": stage[0],
                "peak_c": stage[1],
                "end_c": stage[2],
                "mass_loss_pct": stage[3],
            }
        )
    return stages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    temps, mass_pct, dtg = load_points(Path(args.input_json))
    stages = estimate_stages(temps, mass_pct, dtg)
    summary = {
        "temperature_range_c": [round(float(temps[0]), 2), round(float(temps[-1]), 2)],
        "initial_mass_pct": round(float(mass_pct[0]), 3),
        "final_mass_pct": round(float(mass_pct[-1]), 3),
        "total_mass_loss_pct": round(float(mass_pct[0] - mass_pct[-1]), 3),
        "stages": stages,
        "warnings": [] if stages else ["No clear main decomposition stage detected automatically."],
    }
    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
