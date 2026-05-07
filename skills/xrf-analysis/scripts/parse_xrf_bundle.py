#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").strip()


def as_float(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def extract_source(input_path: Path) -> Path:
    if input_path.is_dir():
        return input_path
    if input_path.suffix.lower() != ".rar":
        raise ValueError(f"Unsupported input: {input_path}")
    temp_dir = Path(tempfile.mkdtemp(prefix="xrf_bundle_"))
    try:
        subprocess.run(
            ["bsdtar", "-xf", str(input_path), "-C", str(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(exc.stderr.strip() or f"Failed to extract {input_path}") from exc
    return temp_dir


def find_single(pattern: str, root: Path) -> Path:
    matches = sorted(root.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern} under {root}")
    return matches[0]


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="gb18030", newline="") as handle:
        return [row for row in csv.reader(handle)]


def parse_metadata_and_table(rows: list[list[str]]) -> tuple[dict[str, str], list[dict[str, object]]]:
    metadata: dict[str, str] = {}
    header_index = None
    for index, row in enumerate(rows):
        if row and normalize_text(row[0]) == "组分":
            header_index = index
            break
        if len(row) >= 2:
            key = normalize_text(row[0])
            value = normalize_text(row[1])
            if key:
                metadata[key] = value
    if header_index is None:
        raise ValueError("Could not find semi-quantitative table header")

    records: list[dict[str, object]] = []
    for row in rows[header_index + 1 :]:
        if len(row) < 7:
            continue
        component = normalize_text(row[0])
        if not component:
            continue
        record = {
            "component": component,
            "result_mass_pct": as_float(row[1]),
            "result_unit": normalize_text(row[2]),
            "detection_limit": as_float(row[3]),
            "element_line": normalize_text(row[4]),
            "line_intensity": as_float(row[5]),
            "normalized_weight_percent": as_float(row[6]),
        }
        records.append(record)
    return metadata, records


def parse_scan(rows: list[list[str]]) -> dict[str, object]:
    if not rows or len(rows[0]) < 5:
        raise ValueError("Unexpected scan CSV layout")
    line_label = normalize_text(rows[0][1])
    scan_window_label = normalize_text(rows[0][4])
    points = []
    for row in rows[1:]:
        if len(row) < 4:
            continue
        axis_value = as_float(row[2])
        intensity = as_float(row[3])
        if axis_value is None or intensity is None:
            continue
        points.append({"2theta_deg": axis_value, "relative_intensity": intensity})
    if not points:
        raise ValueError("No numeric scan points found")
    points.sort(key=lambda item: item["2theta_deg"])
    return {
        "line_label": line_label,
        "axis_name": "2theta_deg",
        "scan_window_label": scan_window_label,
        "summary": {
            "point_count": len(points),
            "axis_range_deg": [points[0]["2theta_deg"], points[-1]["2theta_deg"]],
            "relative_intensity_range": [
                round(min(point["relative_intensity"] for point in points), 6),
                round(max(point["relative_intensity"] for point in points), 6),
            ],
        },
        "points": points,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_json")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    extracted_root = extract_source(input_path)
    cleanup_root = extracted_root if input_path.is_file() else None
    try:
        semi_path = find_single("*半定量.csv", extracted_root)
        scan_path = find_single("*谱图.csv", extracted_root)
        metadata, semiquant = parse_metadata_and_table(read_csv_rows(semi_path))
        scan = parse_scan(read_csv_rows(scan_path))
        sample_name = metadata.get("样品名") or metadata.get("文件名") or semi_path.stem.replace("-半定量", "")
        payload = {
            "source_file": str(input_path),
            "sample_dir_name": semi_path.parent.name,
            "sample_name": sample_name.strip(),
            "metadata": metadata,
            "semiquant": semiquant,
            "scan": scan,
        }
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        if cleanup_root is not None:
            shutil.rmtree(cleanup_root, ignore_errors=True)


if __name__ == "__main__":
    main()
