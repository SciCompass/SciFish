#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary(payload: dict) -> dict[str, object]:
    semiquant = payload.get("semiquant", [])
    ranked = sorted(
        [row for row in semiquant if isinstance(row.get("result_mass_pct"), (int, float))],
        key=lambda row: float(row["result_mass_pct"]),
        reverse=True,
    )
    low_level = []
    for row in ranked:
        result = float(row["result_mass_pct"])
        detection_limit = row.get("detection_limit")
        near_threshold = isinstance(detection_limit, (int, float)) and result <= float(detection_limit) * 3
        if result <= 0.1 or near_threshold:
            low_level.append(
                {
                    "component": row.get("component"),
                    "result_mass_pct": result,
                    "detection_limit": detection_limit,
                    "near_threshold": near_threshold,
                }
            )

    warnings = []
    if payload.get("scan", {}).get("axis_name") == "2theta_deg":
        warnings.append("The scan trace uses a 2theta-like axis but remains an XRF line scan, not an XRD diffractogram.")
    if ranked:
        top_component = ranked[0]
        if top_component.get("component") == "SiO2" and float(top_component["result_mass_pct"]) < 90:
            warnings.append("The sample name alone does not prove high-purity quartz; the composition table shows substantial non-silica oxides.")
    if any(item.get("near_threshold") for item in low_level):
        warnings.append("Some low-level components are close to their reported detection limits and should be described cautiously.")

    return {
        "sample_name": payload.get("sample_name"),
        "major_components": [
            {"component": row.get("component"), "result_mass_pct": row.get("result_mass_pct")}
            for row in ranked[:8]
        ],
        "low_level_components": low_level,
        "scan_overview": {
            "line_label": payload.get("scan", {}).get("line_label"),
            "point_count": payload.get("scan", {}).get("summary", {}).get("point_count"),
            "axis_range_deg": payload.get("scan", {}).get("summary", {}).get("axis_range_deg"),
            "relative_intensity_range": payload.get("scan", {}).get("summary", {}).get("relative_intensity_range"),
        },
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    summary = build_summary(load_payload(Path(args.input_json)))
    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
