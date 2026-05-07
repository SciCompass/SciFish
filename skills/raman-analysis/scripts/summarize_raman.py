#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import find_peaks, peak_widths, savgol_filter


DEFAULT_RULES: dict[str, Any] = {
    "mid_shift_artifact_range": [1850.0, 2250.0],
    "high_shift_broad_range": [2500.0, 3200.0],
    "mid_shift_support_tolerance_cm": 35.0,
    "high_shift_support_tolerance_cm": 35.0,
    "mid_shift_max_width_cm": 80.0,
    "mid_shift_min_prominence_abs": 25.0,
    "mid_shift_min_prominence_noise_factor": 6.0,
    "high_shift_min_prominence_abs": 30.0,
    "high_shift_min_prominence_noise_factor": 8.0,
    "broad_smooth_span_cm": 45.0,
    "broad_distance_cm": 60.0,
    "broad_prominence_factor": 0.03,
    "broad_prominence_min_abs": 3.0,
    "baseline_window_cap_points": 801,
    "baseline_window_floor_points": 101,
    "baseline_window_fraction": 0.25,
}


def load_series(path: Path) -> tuple[np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    x = np.asarray([row["raman_shift_cm^-1"] for row in payload["points"]], dtype=float)
    y = np.asarray([row["intensity_au"] for row in payload["points"]], dtype=float)
    return x, y


def odd_window_length(size: int, preferred: int, minimum: int = 31) -> int:
    upper = size if size % 2 == 1 else size - 1
    if upper < 5:
        raise ValueError("Not enough points for baseline estimation")
    window = min(preferred, upper)
    if window % 2 == 0:
        window -= 1
    if window < minimum:
        window = minimum if minimum <= upper else upper
    if window % 2 == 0:
        window -= 1
    return max(window, 5)


def median_absolute_deviation(values: np.ndarray) -> float:
    median = float(np.median(values))
    return float(np.median(np.abs(values - median)))


def nearest_band_height(peaks: list[dict[str, float]], lower: float, upper: float) -> float | None:
    candidates = [band["intensity_au"] for band in peaks if lower <= band["raman_shift_cm^-1"] <= upper]
    return max(candidates) if candidates else None


def detect_broad_candidates(x: np.ndarray, y: np.ndarray, step: float, rules: dict[str, Any]) -> list[dict[str, float]]:
    smooth_points = int(round(float(rules["broad_smooth_span_cm"]) / max(step, 1e-6)))
    smooth_window = odd_window_length(len(y), preferred=min(61, max(21, smooth_points)), minimum=21)
    smooth_y = savgol_filter(y, window_length=smooth_window, polyorder=3)
    broad_distance = max(12, int(round(float(rules["broad_distance_cm"]) / max(step, 1e-6))))
    broad_prominence = max(
        (float(np.percentile(smooth_y, 99)) - float(np.percentile(smooth_y, 5))) * float(rules["broad_prominence_factor"]),
        float(rules["broad_prominence_min_abs"]),
    )
    broad_indices, broad_props = find_peaks(smooth_y, prominence=broad_prominence, distance=broad_distance)
    candidates: list[dict[str, float]] = []
    for i, idx in enumerate(broad_indices):
        candidates.append(
            {
                "raman_shift_cm^-1": float(x[idx]),
                "intensity_au": float(y[idx]),
                "prominence_au": float(broad_props["prominences"][i]),
            }
        )
    return candidates


def in_range(value: float, limits: tuple[float, float]) -> bool:
    return limits[0] <= value <= limits[1]


def load_rules(config_path: Path | None) -> dict[str, Any]:
    rules = dict(DEFAULT_RULES)
    if config_path is not None:
        overrides = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(overrides, dict):
            raise ValueError("Raman config must be a JSON object")
        rules.update(overrides)
    return rules


def summarize_raman(x: np.ndarray, y: np.ndarray, rules: dict[str, Any] | None = None) -> dict:
    active_rules = rules or DEFAULT_RULES
    if len(x) < 11:
        raise ValueError("Not enough points for Raman band detection")

    step = float(np.median(np.diff(x)))
    baseline_window_preferred = min(
        int(active_rules["baseline_window_cap_points"]),
        max(int(active_rules["baseline_window_floor_points"]), int(len(y) * float(active_rules["baseline_window_fraction"]))),
    )
    baseline = savgol_filter(y, window_length=odd_window_length(len(y), preferred=baseline_window_preferred), polyorder=3)
    corrected = y - baseline
    noise_level = max(median_absolute_deviation(corrected) * 1.4826, 1e-6)
    corrected_span = float(np.percentile(corrected, 99) - np.percentile(corrected, 10))
    max_intensity = float(np.max(y))
    prominence = max(corrected_span * 0.1, noise_level * 3.5, max_intensity * 0.015, 1e-6)
    distance = max(8, int(round(18.0 / max(step, 1e-6))))
    peak_indices, props = find_peaks(corrected, prominence=prominence, distance=distance)
    if len(peak_indices) == 0:
        relaxed_prominence = max(corrected_span * 0.06, noise_level * 2.5, max_intensity * 0.008, 1e-6)
        peak_indices, props = find_peaks(corrected, prominence=relaxed_prominence, distance=distance)
        prominence = relaxed_prominence

    baseline_span = float(np.max(baseline) - np.min(baseline))
    fluorescence_likely = baseline_span > max(max_intensity * 0.35, prominence * 3.5) and noise_level > 5.0
    ranked = np.argsort(props["prominences"])[::-1]
    min_corrected_height = max(noise_level * 2.0, corrected_span * 0.05)
    corrected_widths = (
        peak_widths(corrected, peak_indices, rel_height=0.5)[0] * step
        if len(peak_indices) > 0
        else np.asarray([], dtype=float)
    )

    dominant_bands: list[dict[str, float]] = []
    for peak_pos in ranked:
        idx = peak_indices[peak_pos]
        if float(corrected[idx]) < min_corrected_height:
            continue
        dominant_bands.append(
            {
                "raman_shift_cm^-1": round(float(x[idx]), 3),
                "intensity_au": round(float(y[idx]), 4),
                "relative_intensity_pct": round(float(y[idx]) / max_intensity * 100.0, 2),
                "corrected_height_au": round(float(corrected[idx]), 4),
                "prominence_au": round(float(props["prominences"][peak_pos]), 4),
            }
        )
    if not dominant_bands and len(peak_indices) > 0:
        best_idx = int(np.argmax(props["prominences"]))
        idx = int(peak_indices[best_idx])
        dominant_bands.append(
            {
                "raman_shift_cm^-1": round(float(x[idx]), 3),
                "intensity_au": round(float(y[idx]), 4),
                "relative_intensity_pct": round(float(y[idx]) / max_intensity * 100.0, 2),
                "corrected_height_au": round(float(corrected[idx]), 4),
                "prominence_au": round(float(props["prominences"][best_idx]), 4),
            }
        )

    broad_candidates = detect_broad_candidates(x, y, step, active_rules)
    broad_shifts = [candidate["raman_shift_cm^-1"] for candidate in broad_candidates]
    mid_shift_artifact_range = tuple(float(v) for v in active_rules["mid_shift_artifact_range"])
    high_shift_broad_range = tuple(float(v) for v in active_rules["high_shift_broad_range"])

    # Remove medium-shift artifacts unless they are very strong or stable after broad smoothing.
    refined_bands: list[dict[str, float]] = []
    for band in dominant_bands:
        shift = band["raman_shift_cm^-1"]
        keep = True
        matched_width = None
        if len(peak_indices) > 0:
            nearest_idx = int(np.argmin(np.abs(x[peak_indices] - shift)))
            if 0 <= nearest_idx < len(corrected_widths):
                matched_width = float(corrected_widths[nearest_idx])

        if in_range(shift, mid_shift_artifact_range):
            has_broad_support = any(abs(shift - ref_shift) <= float(active_rules["mid_shift_support_tolerance_cm"]) for ref_shift in broad_shifts)
            strong_enough = band["prominence_au"] >= max(
                noise_level * float(active_rules["mid_shift_min_prominence_noise_factor"]),
                float(active_rules["mid_shift_min_prominence_abs"]),
            )
            not_too_broad = matched_width is None or matched_width <= float(active_rules["mid_shift_max_width_cm"])
            keep = has_broad_support or (strong_enough and not_too_broad)

        if in_range(shift, high_shift_broad_range):
            has_broad_support = any(abs(shift - ref_shift) <= float(active_rules["high_shift_support_tolerance_cm"]) for ref_shift in broad_shifts)
            keep = has_broad_support or band["prominence_au"] >= max(
                noise_level * float(active_rules["high_shift_min_prominence_noise_factor"]),
                float(active_rules["high_shift_min_prominence_abs"]),
            )
        if keep:
            refined_bands.append(band)

    dominant_bands = refined_bands

    # Preserve broad high-shift envelopes (e.g., 2600-3100 cm^-1) for practical interpretation.
    for candidate in broad_candidates:
        shift = candidate["raman_shift_cm^-1"]
        if not in_range(shift, high_shift_broad_range):
            continue
        if any(abs(shift - band["raman_shift_cm^-1"]) <= float(active_rules["high_shift_support_tolerance_cm"]) for band in dominant_bands):
            continue
        dominant_bands.append(
            {
                "raman_shift_cm^-1": round(float(candidate["raman_shift_cm^-1"]), 3),
                "intensity_au": round(float(candidate["intensity_au"]), 4),
                "relative_intensity_pct": round(float(candidate["intensity_au"]) / max_intensity * 100.0, 2),
                "corrected_height_au": None,
                "prominence_au": round(float(candidate["prominence_au"]), 4),
            }
        )

    dominant_bands.sort(key=lambda item: item["prominence_au"], reverse=True)

    d_height = nearest_band_height(dominant_bands, 1330.0, 1360.0)
    g_height = nearest_band_height(dominant_bands, 1570.0, 1605.0)
    two_d_height = nearest_band_height(dominant_bands, 2650.0, 2720.0)

    carbon_screening = {
        "has_d_like_band": d_height is not None,
        "has_g_like_band": g_height is not None,
        "has_2d_like_band": two_d_height is not None,
        "d_to_g_height_ratio": round(d_height / g_height, 3) if d_height is not None and g_height not in (None, 0) else None,
    }

    if fluorescence_likely:
        background_character = "broad_background_or_fluorescence_influenced"
        fluorescence_reason = "baseline variation is large relative to peak prominence"
    elif len(dominant_bands) <= 2:
        background_character = "sparse_discrete_bands"
        fluorescence_reason = None
    else:
        background_character = "discrete_bands_on_low_baseline"
        fluorescence_reason = None

    return {
        "analysis_mode": "peak_screening",
        "band_count": len(dominant_bands),
        "max_intensity_au": round(max_intensity, 4),
        "background_character": background_character,
        "dominant_bands": dominant_bands,
        "fluorescence_screening": {
            "likely_present": fluorescence_likely,
            "reason": fluorescence_reason,
            "baseline_span_au": round(baseline_span, 4),
            "noise_level_au": round(noise_level, 4),
        },
        "carbon_screening": carbon_screening,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    parser.add_argument("--config-json", default=None)
    args = parser.parse_args()

    input_path = Path(args.input_json)
    x, y = load_series(input_path)
    rules = load_rules(Path(args.config_json)) if args.config_json else None
    payload = summarize_raman(x, y, rules=rules)
    payload["source_file"] = str(input_path)

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
