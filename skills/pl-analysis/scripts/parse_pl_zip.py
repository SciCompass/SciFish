#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def parse_text_member(member_name: str, text: str) -> dict:
    metadata: dict[str, object] = {}
    rows: list[tuple[float, float]] = []
    in_data = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = [part.strip() for part in line.split(",")]
        filtered = [part for part in parts if part]
        if len(filtered) < 2:
            continue

        first_value = _to_float(filtered[0])
        second_value = _to_float(filtered[1])
        if first_value is not None and second_value is not None:
            rows.append((first_value, second_value))
            in_data = True
            continue

        if in_data:
            continue

        key = filtered[0]
        value = filtered[1]
        if key in {"Start", "Stop", "Step", "Fixed/Offset", "Dwell Time", "Temp", "Repeats"}:
            metadata[key] = _to_float(value) if _to_float(value) is not None else value
        else:
            metadata[key] = value

    if not rows:
        raise ValueError(f"No numeric PL block found in {member_name}")

    rows.sort(key=lambda item: item[0])
    wavelengths = np.asarray([row[0] for row in rows], dtype=float)
    counts = np.asarray([row[1] for row in rows], dtype=float)
    median_step = round(float(np.median(np.diff(wavelengths))), 6) if len(wavelengths) > 1 else None

    return {
        "scan_name": str(metadata.get("Labels") or Path(member_name).stem),
        "measurement_type": metadata.get("Type", "unknown"),
        "member_name": member_name,
        "metadata": {
            "fixed_or_offset_nm": metadata.get("Fixed/Offset"),
            "xaxis": metadata.get("Xaxis"),
            "yaxis": metadata.get("Yaxis"),
            "repeats": metadata.get("Repeats"),
            "dwell_time_s": metadata.get("Dwell Time"),
            "lamp": metadata.get("Lamp"),
            "detector": metadata.get("Detector"),
            "comment": metadata.get("Comment"),
        },
        "summary": {
            "point_count": len(rows),
            "wavelength_range_nm": [round(float(wavelengths.min()), 6), round(float(wavelengths.max()), 6)],
            "median_step_nm": median_step,
            "intensity_range_counts": [round(float(counts.min()), 6), round(float(counts.max()), 6)],
        },
        "points": [
            {
                "emission_wavelength_nm": round(float(wavelength), 6),
                "counts": round(float(count), 8),
            }
            for wavelength, count in rows
        ],
    }


def parse_input(path: Path) -> dict:
    scans: list[dict] = []
    archive_members: list[str] = []
    unparsed_members: list[str] = []

    if path.suffix.lower() == ".zip":
        with ZipFile(path) as archive:
            archive_members = archive.namelist()
            for member_name in archive_members:
                lower_name = member_name.lower()
                if lower_name.endswith(".txt"):
                    text = archive.read(member_name).decode("utf-8", errors="ignore")
                    scans.append(parse_text_member(member_name, text))
                else:
                    unparsed_members.append(member_name)
    elif path.suffix.lower() == ".txt":
        scans.append(parse_text_member(path.name, path.read_text(encoding="utf-8", errors="ignore")))
        archive_members = [path.name]
    else:
        raise ValueError(f"Unsupported PL input: {path}")

    if not scans:
        raise ValueError(f"No readable PL text scans found in {path}")

    return {
        "source_file": str(path),
        "archive_members": archive_members,
        "unparsed_members": unparsed_members,
        "scans": scans,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_json")
    args = parser.parse_args()

    payload = parse_input(Path(args.input_file))
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
