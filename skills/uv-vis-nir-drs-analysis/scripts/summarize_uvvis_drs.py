#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def window_mean(x: np.ndarray, y: np.ndarray, lower: float, upper: float) -> float | None:
    mask = (x >= lower) & (x <= upper)
    if not np.any(mask):
        return None
    return round(float(np.mean(y[mask])), 6)


def summarize_sample(sample: dict) -> dict:
    x = np.asarray([point["wavelength_nm"] for point in sample["points"]], dtype=float)
    y = np.asarray([point["absorbance"] for point in sample["points"]], dtype=float)
    gradient = np.gradient(y, x)
    edge_index = int(np.argmax(np.abs(gradient)))
    peak_index = int(np.argmax(y))

    return {
        "sample_id": sample["sample_id"],
        "wavelength_range_nm": [round(float(x.min()), 3), round(float(x.max()), 3)],
        "step_nm": round(float(np.median(np.abs(np.diff(x)))), 6),
        "point_count": int(len(x)),
        "peak_wavelength_nm": round(float(x[peak_index]), 3),
        "peak_absorbance": round(float(y[peak_index]), 6),
        "mean_absorbance_200_300_nm": window_mean(x, y, 200.0, 300.0),
        "mean_absorbance_350_500_nm": window_mean(x, y, 350.0, 500.0),
        "mean_absorbance_700_800_nm": window_mean(x, y, 700.0, 800.0),
        "edge_marker_nm": round(float(x[edge_index]), 3),
        "edge_marker_derivative": round(float(gradient[edge_index]), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    samples = [summarize_sample(sample) for sample in parsed["samples"]]
    ranking = [
        {
            "sample_id": sample["sample_id"],
            "peak_absorbance": sample["peak_absorbance"],
            "peak_wavelength_nm": sample["peak_wavelength_nm"],
        }
        for sample in sorted(samples, key=lambda item: item["peak_absorbance"], reverse=True)
    ]

    payload = {
        "source_file": parsed["source_file"],
        "sample_count": len(samples),
        "batch_ranking_by_peak_absorbance": ranking,
        "samples": samples,
    }

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
