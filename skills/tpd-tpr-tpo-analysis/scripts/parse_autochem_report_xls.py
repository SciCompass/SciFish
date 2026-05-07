#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


METADATA_LABELS = {
    "sample_label": "Sample:",
    "operator": "Operator:",
    "submitter": "Submitter:",
    "source_run_file": "File:",
    "started_at": "Started:",
    "completed_at": "Completed:",
    "analysis_type": "Analysis type:",
    "measured_flow_rate": "Measured flow rate:",
    "signal_offset": "Signal offset:",
    "signal_inverted": "Signal inverted:",
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if text.lower() == "nan":
        return ""
    return text


def find_first_value_to_right(frame: pd.DataFrame, label: str) -> str | None:
    for row_idx in range(frame.shape[0]):
        for col_idx in range(frame.shape[1]):
            cell = clean_text(frame.iat[row_idx, col_idx])
            if cell != label:
                continue
            for next_col in range(col_idx + 1, frame.shape[1]):
                candidate = clean_text(frame.iat[row_idx, next_col])
                if candidate and candidate != "|":
                    return candidate
    return None


def parse_metadata(frame: pd.DataFrame) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for key, label in METADATA_LABELS.items():
        value = find_first_value_to_right(frame, label)
        if value is not None:
            metadata[key] = value
    if "analysis_type" in metadata:
        text = str(metadata["analysis_type"]).lower()
        if "reduction" in text:
            metadata["analysis_mode"] = "TPR"
        elif "oxidation" in text:
            metadata["analysis_mode"] = "TPO"
        elif "desorption" in text:
            metadata["analysis_mode"] = "TPD"
        else:
            metadata["analysis_mode"] = "unknown"
    return metadata


def find_trace_header_row(frame: pd.DataFrame) -> int:
    for row_idx in range(frame.shape[0]):
        row = [clean_text(v) for v in frame.iloc[row_idx].tolist()]
        if "Time (minutes)" in row and "Temperature (°C)" in row and "Signal (a.u.)" in row:
            return row_idx
    raise ValueError("Could not find the report trace header row")


def parse_trace(frame: pd.DataFrame) -> pd.DataFrame:
    header_row = find_trace_header_row(frame)
    data = frame.iloc[header_row + 1 :, [5, 6, 10, 11, 15, 16]].copy()
    data.columns = [
        "time_min",
        "signal_au_vs_time",
        "time_min_for_temperature",
        "temperature_c_vs_time",
        "temperature_c",
        "signal_au",
    ]
    parsed = data.apply(pd.to_numeric, errors="coerce")
    parsed = parsed.dropna(subset=["temperature_c", "signal_au"])
    parsed = parsed[parsed["temperature_c"].between(0, 1200)]
    parsed = parsed.reset_index(drop=True)
    if parsed.empty:
        raise ValueError("No usable temperature-signal trace points found")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_json")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_json)
    frame = pd.read_excel(input_path, sheet_name="Sheet1", header=None, engine="xlrd")

    trace = parse_trace(frame)
    payload = {
        "source_file": str(input_path),
        "metadata": parse_metadata(frame),
        "trace_columns": {
            "time_min": "Time (minutes)",
            "signal_au_vs_time": "Signal (a.u.)",
            "time_min_for_temperature": "Time (minutes)",
            "temperature_c_vs_time": "Temperature (°C)",
            "temperature_c": "Temperature (°C)",
            "signal_au": "Signal (a.u.)",
        },
        "point_count": int(len(trace)),
        "temperature_range_c": [
            round(float(trace["temperature_c"].iloc[0]), 3),
            round(float(trace["temperature_c"].iloc[-1]), 3),
        ],
        "signal_range_au": [
            round(float(trace["signal_au"].min()), 6),
            round(float(trace["signal_au"].max()), 6),
        ],
        "points": trace.round(
            {
                "time_min": 6,
                "signal_au_vs_time": 9,
                "time_min_for_temperature": 6,
                "temperature_c_vs_time": 6,
                "temperature_c": 6,
                "signal_au": 9,
            }
        ).to_dict(orient="records"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
