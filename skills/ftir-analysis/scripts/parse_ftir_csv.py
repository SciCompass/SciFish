#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_json")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_json)

    frame = pd.read_csv(input_path, header=None, names=["wavenumber_cm1", "signal"])
    frame = frame.apply(pd.to_numeric, errors="coerce").dropna().reset_index(drop=True)
    if len(frame) < 100:
        raise ValueError("FTIR file has too few numeric rows")

    diff = frame["wavenumber_cm1"].diff().dropna()
    if not ((diff > 0).all() or (diff < 0).all()):
        raise ValueError("Wavenumber axis is not monotonic")

    axis_direction = "ascending" if diff.iloc[0] > 0 else "descending"
    payload = {
        "source_file": str(input_path),
        "metadata": {
            "row_count": int(len(frame)),
            "axis_direction": axis_direction,
            "signal_label": "unknown",
        },
        "columns": {
            "wavenumber_cm1": "column_0",
            "signal": "column_1",
        },
        "points": [
            {
                "index": int(index),
                "wavenumber_cm1": float(row.wavenumber_cm1),
                "signal": float(row.signal),
            }
            for index, row in frame.iterrows()
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
