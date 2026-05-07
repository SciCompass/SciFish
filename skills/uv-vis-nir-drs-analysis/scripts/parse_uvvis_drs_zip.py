#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SUPPORTED_SUFFIXES = {".txt", ".csv", ".xls", ".xlsx"}


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        text = str(value).strip()
        if text == "":
            return None
        number = float(text)
        if not np.isfinite(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def _build_sample_from_xy(
    source_entry: str,
    wavelengths: list[float],
    signals: list[float],
    metadata: dict[str, str] | None = None,
) -> dict:
    points = [
        {
            "index": idx,
            "wavelength_nm": float(x),
            "absorbance": float(y),
        }
        for idx, (x, y) in enumerate(zip(wavelengths, signals))
    ]
    if len(points) < 50:
        raise ValueError(f"Too few numeric rows parsed from {source_entry}")

    x = np.asarray([point["wavelength_nm"] for point in points], dtype=float)
    diff = np.diff(x)
    if not ((diff > 0).all() or (diff < 0).all()):
        raise ValueError(f"Wavelength axis is not monotonic in {source_entry}")

    summary = {
        "point_count": int(len(points)),
        "wavelength_range_nm": [float(x.min()), float(x.max())],
        "axis_direction": "ascending" if float(diff[0]) > 0 else "descending",
        "step_nm": round(float(np.median(np.abs(diff))), 6),
    }
    return {
        "sample_id": Path(source_entry).stem,
        "source_entry": source_entry,
        "metadata": metadata or {},
        "summary": summary,
        "points": points,
    }


def _extract_xy_from_dataframe(df: pd.DataFrame, source_entry: str) -> tuple[list[float], list[float], dict[str, str]]:
    if df.shape[1] < 2:
        raise ValueError(f"Expected at least 2 columns in {source_entry}")

    normalized = [str(col).strip().lower().replace(" ", "") for col in df.columns]
    wave_idx = None
    signal_idx = None

    for idx, name in enumerate(normalized):
        if wave_idx is None and ("波长" in name or "wavelength" in name or "nm" in name):
            wave_idx = idx
        if signal_idx is None and any(token in name for token in ("吸收", "absorb", "反射", "reflect", "透过", "trans", "%r", "%t")):
            signal_idx = idx

    if wave_idx is None:
        wave_idx = 0
    if signal_idx is None:
        signal_idx = 1 if wave_idx == 0 else 0

    wave_col = df.iloc[:, wave_idx]
    signal_col = df.iloc[:, signal_idx]
    pairs: list[tuple[float, float]] = []
    for x_raw, y_raw in zip(wave_col, signal_col):
        x = _safe_float(x_raw)
        y = _safe_float(y_raw)
        if x is None or y is None:
            continue
        pairs.append((x, y))

    if len(pairs) < 50:
        raise ValueError(f"Too few valid XY rows in {source_entry}")

    metadata = {
        "source_format": "tabular",
        "x_column": str(df.columns[wave_idx]),
        "y_column": str(df.columns[signal_idx]),
    }
    y_label = str(df.columns[signal_idx]).strip().lower()
    if "reflect" in y_label or "反射" in y_label or "%r" in y_label:
        metadata["光度值类型"] = "反射率"
    elif "trans" in y_label or "透过" in y_label or "%t" in y_label:
        metadata["光度值类型"] = "透过率"
    elif "abs" in y_label or "吸收" in y_label:
        metadata["光度值类型"] = "吸收值"
    return [pair[0] for pair in pairs], [pair[1] for pair in pairs], metadata


def parse_txt_payload(text: str, source_entry: str) -> dict:
    lines = text.splitlines()
    header_index = next((idx for idx, line in enumerate(lines) if line.startswith("波长(nm),")), None)
    if header_index is None:
        raise ValueError(f"No numeric table header found in {source_entry}")

    metadata: dict[str, str] = {}
    for line in lines[:header_index]:
        if ":," not in line:
            continue
        key, value = line.split(":,", 1)
        metadata[key.strip()] = value.strip()

    points = []
    for line in lines[header_index + 1:]:
        parts = line.split(",")
        if len(parts) < 2:
            continue
        try:
            wavelength = float(parts[0])
            absorbance = float(parts[1])
        except ValueError:
            continue
        points.append(
            {
                "index": len(points),
                "wavelength_nm": wavelength,
                "absorbance": absorbance,
            }
        )

    wavelengths = [point["wavelength_nm"] for point in points]
    signals = [point["absorbance"] for point in points]
    return _build_sample_from_xy(source_entry, wavelengths, signals, metadata)


def parse_csv_or_txt_file(path: Path) -> dict:
    def _extract_header_metadata(lines: list[str], limit: int = 120) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for raw in lines[:limit]:
            cleaned = raw.replace('"', "").strip()
            if ":" not in cleaned:
                continue
            key, value = cleaned.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                metadata[key] = value
        return metadata

    def _read_table_with_fallback(target: Path, sep: str) -> pd.DataFrame:
        last_error: Exception | None = None
        for enc in ("utf-8", "gb18030"):
            try:
                return pd.read_csv(target, sep=sep, engine="python", encoding=enc)
            except Exception as exc:  # fallback on encoding/parsing errors
                last_error = exc
        raise ValueError(f"Failed to parse tabular file {target}: {last_error}") from last_error

    if path.suffix.lower() == ".csv":
        try:
            df = _read_table_with_fallback(path, sep=",")
            x, y, metadata = _extract_xy_from_dataframe(df, str(path))
            return _build_sample_from_xy(path.name, x, y, metadata)
        except ValueError:
            pass

    text = path.read_text(encoding="gb18030", errors="replace")
    if "波长(nm)," in text:
        return parse_txt_payload(text, path.name)

    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=",\t;")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    try:
        df = _read_table_with_fallback(path, sep=delimiter)
        x, y, metadata = _extract_xy_from_dataframe(df, str(path))
        return _build_sample_from_xy(path.name, x, y, metadata)
    except ValueError:
        pass

    # Fallback for plain two-column exports with title lines such as:
    # "1 - RawData"
    # "Wavelength(nm)","R%"
    wavelengths: list[float] = []
    signals: list[float] = []
    lines = text.splitlines()
    for raw in lines:
        cleaned = raw.replace('"', "").strip()
        if not cleaned:
            continue
        parts = [token.strip() for token in cleaned.split(delimiter)]
        if len(parts) < 2:
            continue
        x = _safe_float(parts[0])
        y = _safe_float(parts[1])
        if x is None or y is None:
            continue
        wavelengths.append(x)
        signals.append(y)

    metadata = {"source_format": "tabular-fallback"}
    if lines:
        metadata.update(_extract_header_metadata(lines))
        header_scan = "\n".join(line.replace('"', "") for line in lines[:120])
        lower_scan = header_scan.lower()
        if (
            "反射" in header_scan
            or "r%" in lower_scan
            or "reflect" in lower_scan
            or "������" in header_scan
            or re.search(r"\bnm\b[\t,; ]+\br%?\b", lower_scan) is not None
        ):
            metadata["光度值类型"] = "反射率"
        elif (
            "透过" in header_scan
            or "t%" in lower_scan
            or "trans" in lower_scan
            or "͸����" in header_scan
            or re.search(r"\bnm\b[\t,; ]+\bt%?\b", lower_scan) is not None
        ):
            metadata["光度值类型"] = "透过率"
        elif (
            "吸收" in header_scan
            or "absorb" in lower_scan
            or re.search(r"\bnm\b[\t,; ]+\babs\b", lower_scan) is not None
            or re.search(r"\babs\b", lower_scan) is not None
            or "a%" in lower_scan
            or "����ֵ" in header_scan
        ):
            metadata["光度值类型"] = "吸收值"
    return _build_sample_from_xy(path.name, wavelengths, signals, metadata)


def parse_excel_file(path: Path) -> list[dict]:
    def _first_token(value: object) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        return text.split()[0].lower()

    def _infer_signal_type_from_raw_sheet(raw_df: pd.DataFrame) -> str | None:
        first_col = [_first_token(cell) for cell in raw_df.iloc[:200, 0].tolist()]
        for idx in range(1, len(first_col)):
            prev_token = first_col[idx - 1]
            token = first_col[idx]
            if prev_token in ("nm", "wavelength", "波长"):
                if token in ("a", "abs", "absorbance", "吸收值"):
                    return "吸收值"
                if token in ("r", "r%", "reflectance", "反射率"):
                    return "反射率"
                if token in ("t", "t%", "transmittance", "透过率"):
                    return "透过率"
        return None

    workbook = pd.ExcelFile(path)
    samples: list[dict] = []
    for sheet_name in workbook.sheet_names:
        df = workbook.parse(sheet_name=sheet_name)
        raw_df = workbook.parse(sheet_name=sheet_name, header=None)
        if df.dropna(how="all").empty:
            continue
        try:
            x, y, metadata = _extract_xy_from_dataframe(df, f"{path.name}::{sheet_name}")
        except ValueError:
            continue
        if "光度值类型" not in metadata:
            inferred_signal_type = _infer_signal_type_from_raw_sheet(raw_df)
            if inferred_signal_type is not None:
                metadata["光度值类型"] = inferred_signal_type
        metadata["sheet_name"] = str(sheet_name)
        sample = _build_sample_from_xy(f"{path.stem}-{sheet_name}", x, y, metadata)
        sample["source_entry"] = f"{path.name}::{sheet_name}"
        samples.append(sample)
    if not samples:
        raise ValueError(f"No valid spectrum sheet found in {path}")
    return samples


def parse_archive(input_path: Path) -> dict:
    archive_entries = []
    samples = []
    with zipfile.ZipFile(input_path) as archive:
        for name in archive.namelist():
            archive_entries.append(name)
            if not name.endswith(".txt"):
                continue
            text = archive.read(name).decode("gb18030")
            samples.append(parse_txt_payload(text, name))

    if not samples:
        raise ValueError(f"No .txt spectra found in {input_path}")

    shared_keys = set(samples[0]["metadata"].keys())
    for sample in samples[1:]:
        shared_keys &= set(sample["metadata"].keys())
    batch_metadata = {key: samples[0]["metadata"][key] for key in sorted(shared_keys)}

    return {
        "source_file": str(input_path),
        "archive_entries": archive_entries,
        "batch_metadata": batch_metadata,
        "samples": samples,
    }


def parse_directory(input_dir: Path) -> dict:
    archive_entries: list[str] = []
    samples: list[dict] = []
    for file in sorted(input_dir.rglob("*")):
        if not file.is_file():
            continue
        suffix = file.suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            continue
        archive_entries.append(str(file.relative_to(input_dir)))
        if suffix in {".txt", ".csv"}:
            samples.append(parse_csv_or_txt_file(file))
        else:
            samples.extend(parse_excel_file(file))
    if not samples:
        raise ValueError(f"No supported spectra files found in {input_dir}")
    shared_keys = set(samples[0]["metadata"].keys())
    for sample in samples[1:]:
        shared_keys &= set(sample["metadata"].keys())
    batch_metadata = {key: samples[0]["metadata"][key] for key in sorted(shared_keys)}
    return {
        "source_file": str(input_dir),
        "archive_entries": archive_entries,
        "batch_metadata": batch_metadata,
        "samples": samples,
    }


def parse_input(input_path: Path) -> dict:
    if input_path.is_dir():
        return parse_directory(input_path)
    suffix = input_path.suffix.lower()
    if suffix == ".zip":
        return parse_archive(input_path)
    if suffix in {".txt", ".csv"}:
        sample = parse_csv_or_txt_file(input_path)
        return {
            "source_file": str(input_path),
            "archive_entries": [input_path.name],
            "batch_metadata": dict(sample.get("metadata", {})),
            "samples": [sample],
        }
    if suffix in {".xls", ".xlsx"}:
        samples = parse_excel_file(input_path)
        shared_keys = set(samples[0]["metadata"].keys())
        for sample in samples[1:]:
            shared_keys &= set(sample["metadata"].keys())
        batch_metadata = {key: samples[0]["metadata"][key] for key in sorted(shared_keys)}
        return {
            "source_file": str(input_path),
            "archive_entries": [input_path.name],
            "batch_metadata": batch_metadata,
            "samples": samples,
        }
    raise ValueError(f"Unsupported input type: {input_path.suffix} ({input_path})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_json")
    args = parser.parse_args()

    payload = parse_input(Path(args.input_path))
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
