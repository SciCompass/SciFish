#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks, peak_prominences, savgol_filter


def classify_region(wavenumber_cm1: float) -> str:
    if wavenumber_cm1 >= 2500:
        return "functional-group"
    if wavenumber_cm1 >= 1500:
        return "mid-region"
    return "fingerprint"


def infer_is_absorbance(values: np.ndarray) -> bool:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return False
    max_val = float(np.max(finite))
    median_val = float(np.median(finite))
    p90 = float(np.percentile(finite, 90))
    if max_val <= 1.05:
        return p90 < 0.45 and median_val < 0.25
    if max_val <= 10.0:
        return True
    return False


def normalize_transmittance(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.clip(values, 0.0, 1.0)
    max_val = float(np.max(finite))
    if max_val > 1.5:
        return np.clip(values / 100.0, 0.0, 1.0)
    return np.clip(values, 0.0, 1.0)


def recommend_peak_params(wavenumbers: np.ndarray, signal: np.ndarray) -> tuple[float, int, tuple[int | None, int | None], float]:
    signal_range = float(np.max(signal) - np.min(signal))
    wn_step = abs(float(wavenumbers[0] - wavenumbers[-1])) / max(1, len(wavenumbers) - 1)
    gradient = np.abs(np.diff(signal))
    noise_estimate = float(np.percentile(gradient, 10)) if gradient.size else 0.0
    # Scale floor with signal range so low-amplitude spectra are not over-suppressed.
    min_prom_floor = max(signal_range * 0.015, 0.002)
    prominence = max(noise_estimate * 3.0, signal_range * 0.03, min_prom_floor)
    width_min = max(3, int(6 / wn_step)) if wn_step > 0 else 3
    min_height = float(max(np.min(signal) + signal_range * 0.03, noise_estimate * 2.0))
    return prominence, width_min, (width_min, None), min_height


def refine_peak_with_parabola(x: np.ndarray, y: np.ndarray, index: int) -> tuple[float, float]:
    idx = int(index)
    if idx <= 0 or idx >= len(y) - 1:
        return float(x[idx]), float(y[idx])
    local_x = np.asarray(x[idx - 1:idx + 2], dtype=float)
    local_y = np.asarray(y[idx - 1:idx + 2], dtype=float)
    try:
        a, b, c = np.polyfit(local_x, local_y, 2)
    except Exception:
        return float(x[idx]), float(y[idx])
    if not np.isfinite(a) or abs(a) < 1e-12 or a >= 0.0:
        return float(x[idx]), float(y[idx])
    vertex_x = -b / (2.0 * a)
    if vertex_x < float(np.min(local_x)) or vertex_x > float(np.max(local_x)):
        return float(x[idx]), float(y[idx])
    vertex_y = a * vertex_x * vertex_x + b * vertex_x + c
    if not np.isfinite(vertex_y):
        return float(x[idx]), float(y[idx])
    return float(vertex_x), float(vertex_y)


def recover_boundary_peaks(
    x: np.ndarray,
    y_signal: np.ndarray,
    existing_indices: list[int],
    prominence: float,
    min_height: float,
    edge_search_cm1: float = 40.0,
) -> list[int]:
    accepted = set(int(i) for i in existing_indices)
    x_min = float(np.min(x))
    x_max = float(np.max(x))
    edge_mask = (x <= x_min + edge_search_cm1) | (x >= x_max - edge_search_cm1)
    candidates = np.where(edge_mask)[0]
    if candidates.size == 0:
        return sorted(accepted)

    relax_prom = max(prominence * 0.8, float(np.std(np.diff(y_signal))) * 2.0, 1e-6)
    for idx in candidates:
        idx = int(idx)
        if idx <= 1 or idx >= len(y_signal) - 2:
            continue
        if any(abs(idx - p) <= 2 for p in accepted):
            continue
        if not (y_signal[idx] >= y_signal[idx - 1] and y_signal[idx] >= y_signal[idx + 1]):
            continue
        if y_signal[idx] < (min_height * 0.9):
            continue
        prom = float(peak_prominences(y_signal, [idx])[0][0])
        if prom < relax_prom:
            continue
        accepted.add(idx)
    return sorted(accepted)


def detect_bands(
    x: np.ndarray, y_signal: np.ndarray, y_original: np.ndarray, prominence: float, distance: int, min_height: float
) -> list[dict[str, float | str]]:
    peak_indices, _ = find_peaks(
        y_signal,
        prominence=prominence,
        distance=distance,
        height=min_height,
    )
    indices = sorted(int(i) for i in peak_indices.tolist())

    # If the first pass is too strict, relax prominence once to recover chemically useful bands.
    if len(indices) < 5:
        relaxed_indices, _ = find_peaks(
            y_signal,
            prominence=max(prominence * 0.65, 1e-6),
            distance=max(6, distance // 2),
            height=min_height * 0.9,
        )
        indices = sorted(set(indices) | set(int(i) for i in relaxed_indices.tolist()))

    indices = recover_boundary_peaks(x, y_signal, indices, prominence, min_height)
    prom_values = peak_prominences(y_signal, indices)[0] if indices else []
    bands: list[dict[str, float | str]] = []
    for idx, prom in zip(indices, prom_values):
        refined_x, _ = refine_peak_with_parabola(x, y_signal, idx)
        bands.append(
            {
                "wavenumber_cm1": refined_x,
                "signal": float(np.interp(refined_x, x, y_original)),
                "prominence": float(prom),
                "region": classify_region(refined_x),
            }
        )
    return sorted(bands, key=lambda item: item["prominence"], reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    parsed_path = Path(args.parsed_json)
    output_path = Path(args.output_json)
    payload = json.loads(parsed_path.read_text(encoding="utf-8"))
    points = payload["points"]
    x = np.asarray([row["wavenumber_cm1"] for row in points], dtype=float)
    y = np.asarray([row["signal"] for row in points], dtype=float)

    # Smooth before peak picking to suppress digitization noise while preserving band shapes.
    window = max(9, min(25, (len(y) // 200) | 1))
    if window >= len(y):
        window = len(y) - 1 if len(y) % 2 == 0 else len(y)
    smooth_y = savgol_filter(y, window_length=window, polyorder=2, mode="interp")

    is_absorbance = infer_is_absorbance(smooth_y)
    if is_absorbance:
        absorbance_like = smooth_y
    else:
        transmittance_like = normalize_transmittance(smooth_y)
        absorbance_like = 1.0 - transmittance_like
    prominence, width_min, _, min_height = recommend_peak_params(x, absorbance_like)
    distance = max(8, len(x) // 500)
    ranked = detect_bands(x, absorbance_like, y, prominence, distance, min_height)
    signal_range = float(np.max(absorbance_like) - np.min(absorbance_like))
    carbonyl_prominence_cutoff = max(prominence * 2.0, signal_range * 0.08)

    summary = {
        "wavenumber_range_cm1": [float(x.min()), float(x.max())],
        "signal_range": [float(y.min()), float(y.max())],
        "main_bands": ranked[:10],
        "detection_mode": "absorbance" if is_absorbance else "transmittance_to_absorbance",
        "peak_pick_params": {
            "prominence": float(prominence),
            "distance_points": int(distance),
            "savgol_window": int(window),
            "width_min_points": int(width_min),
            "min_height": float(min_height),
        },
        "broad_band_flags": {
            "oh_nh_like": any(3200.0 <= band["wavenumber_cm1"] <= 3600.0 for band in ranked[:10]),
            "water_bending_like": any(1580.0 <= band["wavenumber_cm1"] <= 1660.0 for band in ranked[:10]),
            "strong_carbonyl_like": any(
                1700.0 <= band["wavenumber_cm1"] <= 1750.0
                and band["prominence"] >= carbonyl_prominence_cutoff
                for band in ranked[:10]
            ),
        },
        "warnings": [],
    }

    if np.isclose(y[0], 0.0) or np.isclose(y[-1], 0.0):
        summary["warnings"].append("Zero-valued endpoints are present; boundary bands may be unreliable.")
    if not ranked:
        summary["warnings"].append("No robust bands were detected under adaptive thresholds.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
