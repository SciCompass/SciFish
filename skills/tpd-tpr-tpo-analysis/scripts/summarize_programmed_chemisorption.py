#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def load_trace(path: Path) -> tuple[dict[str, object], np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    temps = []
    signal = []
    for row in payload["points"]:
        temp = row.get("temperature_c")
        sig = row.get("signal_au")
        if temp is None or sig is None:
            continue
        temps.append(float(temp))
        signal.append(float(sig))
    return payload, np.asarray(temps), np.asarray(signal)


def find_events(temps: np.ndarray, signal: np.ndarray) -> tuple[np.ndarray, list[dict[str, float]], list[dict[str, float]]]:
    window = min(len(signal) if len(signal) % 2 == 1 else len(signal) - 1, 61)
    if window < 5:
        window = 5
    smooth = pd.Series(signal).rolling(window, center=True, min_periods=1).mean().to_numpy()
    signal_span = float(np.nanmax(smooth) - np.nanmin(smooth))
    prominence = max(signal_span * 0.08, 0.0005)
    distance = max(40, len(smooth) // 30)

    positive_idx, positive_props = find_peaks(smooth, prominence=prominence, distance=distance)
    negative_idx, negative_props = find_peaks(-smooth, prominence=prominence, distance=distance)

    positives = [
        {
            "peak_temperature_c": round(float(temps[idx]), 2),
            "peak_signal_au": round(float(smooth[idx]), 6),
            "prominence_au": round(float(positive_props["prominences"][i]), 6),
            "direction": "positive",
        }
        for i, idx in enumerate(positive_idx)
    ]
    negatives = [
        {
            "peak_temperature_c": round(float(temps[idx]), 2),
            "peak_signal_au": round(float(smooth[idx]), 6),
            "prominence_au": round(float(negative_props["prominences"][i]), 6),
            "direction": "negative",
        }
        for i, idx in enumerate(negative_idx)
    ]
    positives.sort(key=lambda item: item["prominence_au"], reverse=True)
    negatives.sort(key=lambda item: item["prominence_au"], reverse=True)
    return smooth, positives[:5], negatives[:5]


def temperature_band(temp: float) -> str:
    if temp < 200:
        return "low-temperature"
    if temp < 500:
        return "mid-temperature"
    return "high-temperature"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    payload, temps, signal = load_trace(Path(args.input_json))
    smooth, positives, negatives = find_events(temps, signal)
    dominant = None
    candidates = positives + negatives
    if candidates:
        dominant = max(candidates, key=lambda item: item["prominence_au"])

    summary = {
        "source_file": payload["source_file"],
        "analysis_mode": payload.get("metadata", {}).get("analysis_mode", "unknown"),
        "point_count": int(len(temps)),
        "temperature_range_c": [round(float(temps.min()), 2), round(float(temps.max()), 2)],
        "raw_signal_range_au": [round(float(signal.min()), 6), round(float(signal.max()), 6)],
        "smoothed_signal_range_au": [round(float(smooth.min()), 6), round(float(smooth.max()), 6)],
        "dominant_event": {
            **dominant,
            "temperature_band": temperature_band(float(dominant["peak_temperature_c"])),
        }
        if dominant
        else None,
        "positive_events": positives,
        "negative_events": negatives,
        "warnings": [],
    }

    if not candidates:
        summary["warnings"].append("No clear peak above the current prominence threshold.")
    if payload.get("metadata", {}).get("signal_inverted", "").lower() == "yes":
        summary["warnings"].append("Signal inverted flag is set in the vendor report; inspect event direction before assigning physical meaning.")
    if payload.get("metadata", {}).get("analysis_mode") != "TPR":
        summary["warnings"].append("Current parser was validated on AutoChem II TPR report layout; other modes need confirmation on real files.")

    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
