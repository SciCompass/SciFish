#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_dls_xls(input_path: Path, output_path: Path) -> dict:
    frame = pd.read_excel(input_path, sheet_name="Sheet1", header=None)
    if len(frame) < 4 or frame.shape[1] < 2:
        raise ValueError("DLS XLS file does not match the confirmed Sheet1 layout")

    record_label = str(frame.iloc[0, 0]).strip()
    header_size = str(frame.iloc[1, 0]).strip()
    header_signal = str(frame.iloc[1, 1]).strip()
    if "size" not in header_size.lower() or "distribution" not in header_signal.lower():
        raise ValueError("Confirmed DLS particle-size headers were not found")

    data = frame.iloc[2:, :2].copy()
    data.columns = ["size_nm", "intensity_pct"]
    data["size_nm"] = pd.to_numeric(data["size_nm"], errors="coerce")
    data["intensity_pct"] = pd.to_numeric(data["intensity_pct"], errors="coerce")
    data = data.dropna().reset_index(drop=True)
    if data.empty:
        raise ValueError("No numeric DLS points found")

    diff = data["size_nm"].diff().dropna()
    if not (diff > 0).all():
        raise ValueError("Particle-size axis is not strictly increasing")

    payload = {
        "source_file": str(input_path),
        "sheet_name": "Sheet1",
        "columns": {
            "size_nm": header_size,
            "intensity_pct": header_signal,
        },
        "metadata": {
            "record_label": record_label,
            "distribution_kind": "intensity",
            "zeta_fields_present": False,
        },
        "points": [
            {
                "index": int(index),
                "size_nm": float(row.size_nm),
                "intensity_pct": float(row.intensity_pct),
            }
            for index, row in data.iterrows()
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_json")
    args = parser.parse_args()

    parse_dls_xls(Path(args.input_file), Path(args.output_json))


if __name__ == "__main__":
    main()
