#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks


def summarize_dls(parsed_json: Path, output_json: Path) -> dict:
    payload = json.loads(parsed_json.read_text(encoding="utf-8"))
    x = np.asarray([row["size_nm"] for row in payload["points"]], dtype=float)
    y = np.asarray([row["intensity_pct"] for row in payload["points"]], dtype=float)

    if len(x) < 5:
        raise ValueError("Too few DLS points to summarize")
    if np.allclose(y, 0.0):
        raise ValueError("All intensity values are zero")

    nonzero = y > 0
    main_idx = int(np.argmax(y))

    prominence_floor = max(float(y.max()) * 0.08, 0.5)
    peak_indices, props = find_peaks(y, prominence=prominence_floor, distance=max(2, len(x) // 20))
    top_peaks = sorted(
        (
            {
                "size_nm": round(float(x[idx]), 3),
                "intensity_pct": round(float(y[idx]), 3),
                "prominence": round(float(prom), 3),
            }
            for idx, prom in zip(peak_indices, props["prominences"])
        ),
        key=lambda item: item["intensity_pct"],
        reverse=True,
    )

    tail_end = float(x[nonzero][-1]) if np.any(nonzero) else float(x[-1])
    summary = {
        "distribution_kind": payload.get("metadata", {}).get("distribution_kind", "intensity"),
        "size_range_nm": [round(float(x.min()), 3), round(float(x.max()), 3)],
        "nonzero_range_nm": [
            round(float(x[nonzero][0]), 3),
            round(float(x[nonzero][-1]), 3),
        ] if np.any(nonzero) else None,
        "main_peak": {
            "size_nm": round(float(x[main_idx]), 3),
            "intensity_pct": round(float(y[main_idx]), 3),
        },
        "top_peaks": top_peaks[:3],
        "tail_flags": {
            "large_particle_tail": bool(tail_end >= 3000.0),
            "tail_end_nm": round(tail_end, 3),
        },
        "warnings": [],
        "zeta_available": False,
    }

    if len(top_peaks) > 1:
        summary["warnings"].append("Multiple intensity peaks were detected; review for multimodal behavior.")
    if summary["tail_flags"]["large_particle_tail"]:
        summary["warnings"].append("A high-size tail extends into the micron-scale region.")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    summarize_dls(Path(args.parsed_json), Path(args.output_json))


if __name__ == "__main__":
    main()
