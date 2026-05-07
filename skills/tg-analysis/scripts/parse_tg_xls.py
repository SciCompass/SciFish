#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ALIASES = {
    "temperature_c": ["temperature", "temp", "sample temp", "furnace temp"],
    "time_min": ["time", "minute", "min", "elapsed time"],
    "mass_mg": ["mass mg", "weight mg", "sample mass mg", "tg mg", "weight"],
    "mass_pct": ["mass %", "weight %", "%weight", "tg%", "weight percent"],
    "dtg": ["dtg", "dw/dt", "dm/dt", "dm/dt%", "dm/dt %", "dm/dt(mg/min)", "dm/dt(mg/degc)", "dm/dt", "dm/dt ", "dm/dt(mg/c)", "dm/dt(mg/°c)", "dm/dt(mg/℃)", "dm/dt(mg/celsius)", "deriv. weight", "deriv. weight % / °c", "dm/dt(mg/minute)", "dm/dt(mg per min)", "dm/dt(mg per c)", "dm/dt(mg/deg)"],
}


def normalize_name(name: object) -> str:
    text = "" if name is None else str(name)
    return " ".join(text.strip().lower().replace("_", " ").split())


def score_headers(columns: list[str]) -> int:
    normalized = [normalize_name(col) for col in columns]
    score = 0
    for group in ALIASES.values():
        if any(any(alias in col for alias in group) for col in normalized):
            score += 1
    return score


def build_candidate(frame: pd.DataFrame, header_row: int) -> pd.DataFrame:
    candidate = frame.iloc[header_row:].copy()
    header_values = candidate.iloc[0].tolist()
    if header_row + 1 < len(frame):
        unit_values = frame.iloc[header_row + 1].tolist()
    else:
        unit_values = [None] * len(header_values)
    columns: list[str] = []
    seen: dict[str, int] = {}
    for raw_header, raw_unit in zip(header_values, unit_values):
        header = normalize_name(raw_header)
        unit = normalize_name(raw_unit)
        combined = " ".join(part for part in [header, unit] if part and part != "nan").strip()
        name = combined or header or unit or "unnamed"
        seen[name] = seen.get(name, 0) + 1
        if seen[name] > 1:
            name = f"{name} #{seen[name]}"
        columns.append(name)
    start_row = header_row + 2 if header_row + 1 < len(frame) else header_row + 1
    candidate = frame.iloc[start_row:].copy().reset_index(drop=True)
    candidate.columns = columns
    return candidate


def find_best_sheet(path: Path) -> tuple[str, pd.DataFrame]:
    sheets = pd.read_excel(path, sheet_name=None, header=None, engine="xlrd")
    best_name = None
    best_frame = None
    best_score = -1
    for name, frame in sheets.items():
        for header_row in range(min(12, len(frame))):
            candidate = build_candidate(frame, header_row)
            if candidate.empty:
                continue
            score = score_headers([str(c) for c in candidate.columns])
            if score > best_score:
                best_score = score
                best_name = name
                best_frame = candidate
    if best_frame is None or best_name is None:
        raise ValueError("No numeric TG-like sheet found")
    return best_name, best_frame


def map_columns(columns: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for original in columns:
        normalized = normalize_name(original)
        if "deriv." in normalized or "deriv weight" in normalized:
            result.setdefault("dtg", original)
            continue
        if "weight" in normalized and "%" in normalized:
            result.setdefault("mass_pct", original)
            continue
        if "weight" in normalized and "mg" in normalized:
            result.setdefault("mass_mg", original)
            continue
        for canonical, aliases in ALIASES.items():
            if canonical in result:
                continue
            if any(alias in normalized for alias in aliases):
                result[canonical] = original
    return result


def coerce_numeric(frame: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    data = pd.DataFrame()
    for canonical, original in columns.items():
        data[canonical] = pd.to_numeric(frame[original], errors="coerce")
    data = data.dropna(how="all")
    if "mass_pct" not in data.columns and "mass_mg" in data.columns:
        first_valid = data["mass_mg"].dropna().iloc[0]
        data["mass_pct"] = data["mass_mg"] / first_valid * 100.0
    if "temperature_c" in data.columns:
        data = data[data["temperature_c"].notna()]
        data = data.sort_values("temperature_c").reset_index(drop=True)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_json")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_json)
    sheet_name, frame = find_best_sheet(input_path)
    columns = map_columns([str(c) for c in frame.columns])
    parsed = coerce_numeric(frame, columns)
    if "temperature_c" not in parsed.columns:
        raise ValueError("Temperature column not found")
    if "mass_mg" not in parsed.columns and "mass_pct" not in parsed.columns:
        raise ValueError("Mass or mass percent column not found")

    payload = {
        "source_file": str(input_path),
        "sheet_name": sheet_name,
        "columns": columns,
        "points": parsed.where(pd.notna(parsed), None).to_dict(orient="records"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
