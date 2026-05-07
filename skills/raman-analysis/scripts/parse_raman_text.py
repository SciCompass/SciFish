#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


ENCODING_CANDIDATES = (
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "gb18030",
    "gbk",
)


def read_text_with_fallback(path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ENCODING_CANDIDATES:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise ValueError(f"Unable to decode Raman file: {path}") from last_error
    return path.read_text(encoding="utf-8")


def parse_raman_text(path: Path) -> dict:
    rows = []
    for raw_line in read_text_with_fallback(path).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.replace(",", "\t").split()
        if len(parts) < 2:
            continue
        try:
            shift = float(parts[0])
            intensity = float(parts[1])
        except ValueError:
            continue
        rows.append((shift, intensity))

    if not rows:
        raise ValueError(f"No numeric Raman block found in {path}")

    rows.sort(key=lambda item: item[0])
    deduped: list[dict[str, float]] = []
    for shift, intensity in rows:
        if deduped and abs(deduped[-1]["raman_shift_cm^-1"] - shift) < 1e-9:
            deduped[-1]["intensity_au"] = (deduped[-1]["intensity_au"] + intensity) / 2.0
        else:
            deduped.append(
                {
                    "raman_shift_cm^-1": shift,
                    "intensity_au": intensity,
                }
            )

    shifts = np.asarray([row["raman_shift_cm^-1"] for row in deduped], dtype=float)
    intensities = np.asarray([row["intensity_au"] for row in deduped], dtype=float)
    median_step = round(float(np.median(np.diff(shifts))), 6) if len(shifts) > 1 else None

    return {
        "source_file": str(path),
        "metadata": {},
        "columns": {
            "raman_shift_cm^-1": "Raman shift",
            "intensity_au": "intensity",
        },
        "summary": {
            "point_count": len(deduped),
            "shift_range_cm^-1": [round(float(shifts.min()), 6), round(float(shifts.max()), 6)],
            "median_step_cm^-1": median_step,
            "intensity_range_au": [round(float(intensities.min()), 6), round(float(intensities.max()), 6)],
        },
        "points": deduped,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_json")
    args = parser.parse_args()

    payload = parse_raman_text(Path(args.input_file))
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
