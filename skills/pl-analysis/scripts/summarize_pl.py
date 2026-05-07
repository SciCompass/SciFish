#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks


def summarize_scan(scan: dict) -> dict:
    x = np.asarray([row["emission_wavelength_nm"] for row in scan["points"]], dtype=float)
    y = np.asarray([row["counts"] for row in scan["points"]], dtype=float)
    if len(x) < 11:
        raise ValueError(f"Not enough points for PL peak detection in {scan['scan_name']}")

    step = float(np.median(np.diff(x)))
    dynamic_range = float(np.max(y) - np.min(y))
    prominence = max(dynamic_range * 0.08, 20.0)
    distance = max(5, int(round(10.0 / max(step, 1e-6))))
    peak_indices, props = find_peaks(y, prominence=prominence, distance=distance)
    baseline = float(np.percentile(y, 5))
    min_peak_height = max(0.0, baseline + dynamic_range * 0.08)

    ranked_positions = np.argsort(props["prominences"])[::-1] if len(peak_indices) else []
    dominant_peaks: list[dict[str, float]] = []
    max_counts = float(np.max(y))
    for pos in ranked_positions[:8]:
        idx = int(peak_indices[pos])
        if float(y[idx]) <= min_peak_height:
            continue
        dominant_peaks.append(
            {
                "emission_wavelength_nm": round(float(x[idx]), 3),
                "counts": round(float(y[idx]), 4),
                "relative_intensity_pct": round(float(y[idx]) / max_counts * 100.0, 2) if max_counts else 0.0,
                "prominence_counts": round(float(props["prominences"][pos]), 4),
            }
        )

    strongest_idx = int(np.argmax(y))
    above_baseline_y = np.clip(y - baseline, 0.0, None)
    positive_sum = float(np.sum(above_baseline_y))
    centroid = float(np.sum(x * above_baseline_y) / positive_sum) if positive_sum > 0 else None

    return {
        "scan_name": scan["scan_name"],
        "measurement_type": scan["measurement_type"],
        "strongest_peak_nm": round(float(x[strongest_idx]), 3),
        "max_counts": round(float(max_counts), 4),
        "min_counts": round(float(np.min(y)), 4),
        "baseline_estimate_counts": round(float(baseline), 4),
        "integrated_above_baseline_counts_nm": round(float(np.trapezoid(above_baseline_y, x)), 4),
        "centroid_above_baseline_nm": round(float(centroid), 3) if centroid is not None else None,
        "negative_fraction": round(float(np.mean(y < 0.0)), 4),
        "dominant_peaks": dominant_peaks,
    }


def compare_scans(scan_summaries: list[dict]) -> list[dict]:
    if len(scan_summaries) < 2:
        return []

    reference = scan_summaries[0]
    comparisons = []
    for scan in scan_summaries[1:]:
        comparisons.append(
            {
                "scan_name": scan["scan_name"],
                "reference_scan_name": reference["scan_name"],
                "max_count_ratio_vs_reference": round(scan["max_counts"] / reference["max_counts"], 4)
                if reference["max_counts"]
                else None,
                "integrated_above_baseline_ratio_vs_reference": round(
                    scan["integrated_above_baseline_counts_nm"] / reference["integrated_above_baseline_counts_nm"], 4
                )
                if reference["integrated_above_baseline_counts_nm"]
                else None,
                "strongest_peak_shift_nm_vs_reference": round(
                    scan["strongest_peak_nm"] - reference["strongest_peak_nm"], 3
                ),
            }
        )
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    parsed_path = Path(args.parsed_json)
    payload = json.loads(parsed_path.read_text(encoding="utf-8"))
    scan_summaries = [summarize_scan(scan) for scan in payload["scans"]]
    summary = {
        "source_file": str(parsed_path),
        "scan_count": len(scan_summaries),
        "steady_state_detected": any(scan["measurement_type"] == "Emission Scan" for scan in payload["scans"]),
        "transient_decay_detected": any("decay" in str(scan["measurement_type"]).lower() for scan in payload["scans"]),
        "scans": scan_summaries,
        "comparisons": compare_scans(scan_summaries),
    }

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
