#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


NUMBER_FRAGMENT = r"([0-9]{1,3}(?:\s*\.\s*[0-9]{1,3})?)"
LEFT_PATTERNS = [
    re.compile(r"(?:I?CA|CA)\s*left\D{0,20}" + NUMBER_FRAGMENT, re.IGNORECASE),
    re.compile(r"left\s*angle\D{0,20}" + NUMBER_FRAGMENT, re.IGNORECASE),
]
RIGHT_PATTERNS = [
    re.compile(r"(?:I?CA|CA)\s*right\D{0,20}" + NUMBER_FRAGMENT, re.IGNORECASE),
    re.compile(r"right\s*angle\D{0,20}" + NUMBER_FRAGMENT, re.IGNORECASE),
]
AVERAGE_PATTERNS = [
    re.compile(r"(?:avg|ave|average)\s*(?:CA|angle)?\D{0,20}" + NUMBER_FRAGMENT, re.IGNORECASE),
    re.compile(r"(?:I?CA|CA)\s*(?:avg|ave|average)\D{0,20}" + NUMBER_FRAGMENT, re.IGNORECASE),
]
SINGLE_ANGLE_PATTERN = re.compile(r"(?:^|\b)(?:angle|angel)\s*[:=]?\s*" + NUMBER_FRAGMENT, re.IGNORECASE)
SURFACE_TENSION_PATTERN = re.compile(
    r"(?:surface\s*tension|interfacial\s*tension|IFT|SFT|gamma)\D{0,12}([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_source(input_path: Path) -> tuple[Path, Path | None]:
    if input_path.is_dir():
        return input_path, None
    suffix = input_path.suffix.lower()
    if suffix not in {".rar", ".zip"}:
        raise ValueError(f"Unsupported input: {input_path}")
    temp_dir = Path(tempfile.mkdtemp(prefix="contact_angle_bundle_"))
    try:
        if suffix == ".zip":
            shutil.unpack_archive(str(input_path), str(temp_dir))
        else:
            subprocess.run(
                ["bsdtar", "-xf", str(input_path), "-C", str(temp_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    except (subprocess.CalledProcessError, shutil.ReadError) as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if isinstance(exc, subprocess.CalledProcessError):
            stderr = decode_subprocess_output(exc.stderr)
            message = stderr.strip() or f"Failed to extract {input_path}"
        else:
            message = f"Failed to extract {input_path}: {exc}"
        raise RuntimeError(message) from exc
    children = [child for child in temp_dir.iterdir()]
    if len(children) == 1 and children[0].is_dir():
        return children[0], temp_dir
    return temp_dir, temp_dir


def find_images(root: Path) -> list[Path]:
    suffixes = {".bmp", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes)


def prepare_for_ocr(path: Path, temp_dir: Path) -> Path:
    image = Image.open(path)
    image.load()
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    # OCR is more stable after contrast normalization and moderate upscaling.
    image = ImageOps.autocontrast(image)
    image = image.resize((image.width * 2, image.height * 2))
    out_path = temp_dir / f"{path.stem}.png"
    image.save(out_path)
    return out_path


def decode_subprocess_output(raw: bytes | None) -> str:
    if not raw:
        return ""
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def run_tesseract(path: Path) -> str:
    try:
        result = subprocess.run(
            ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "6"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("tesseract is required to parse screenshot bundles") from exc
    except subprocess.CalledProcessError as exc:
        stderr = decode_subprocess_output(exc.stderr).strip()
        raise RuntimeError(stderr or f"tesseract failed for {path}") from exc
    stdout = decode_subprocess_output(result.stdout)
    return " ".join(stdout.split())


def parse_numeric(raw: str | None) -> float | None:
    if raw is None:
        return None
    normalized = raw.replace(" ", "")
    try:
        return round(float(normalized), 3)
    except ValueError:
        return None


def extract_first(patterns: list[re.Pattern[str]], text: str) -> float | None:
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        value = parse_numeric(match.group(1))
        if value is not None:
            return value
    return None


def parse_metrics(text: str) -> dict[str, object]:
    left_value = extract_first(LEFT_PATTERNS, text)
    right_value = extract_first(RIGHT_PATTERNS, text)
    average_value = extract_first(AVERAGE_PATTERNS, text)

    if average_value is None and left_value is None and right_value is None:
        single_match = SINGLE_ANGLE_PATTERN.search(text)
        if single_match:
            average_value = parse_numeric(single_match.group(1))

    if average_value is None:
        visible_sides = [value for value in (left_value, right_value) if value is not None]
        if visible_sides:
            average_value = round(float(statistics.mean(visible_sides)), 3)

    tension_match = SURFACE_TENSION_PATTERN.search(text)
    surface_tension = parse_numeric(tension_match.group(1)) if tension_match else None

    return {
        "left_ca": left_value,
        "right_ca": right_value,
        "average_ca": average_value,
        "unit": "degree",
        "surface_tension_mn_m": surface_tension,
        # Backward-compatible aliases.
        "left_contact_angle_deg": left_value,
        "right_contact_angle_deg": right_value,
        "mean_contact_angle_deg": average_value,
    }


def base_group_id(path: Path) -> str:
    return path.stem.split("-", 1)[0]


def sample_id(path: Path, root: Path) -> str:
    parent = path.parent.relative_to(root).as_posix()
    return parent if parent != "." else "root"


def group_key(path: Path, root: Path) -> str:
    return f"{sample_id(path, root)}::{base_group_id(path)}"


def median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.median(values)), 3)


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(statistics.mean(values)), 3)


def summarize_group(key: str, records: list[dict[str, object]]) -> dict[str, object]:
    left_values = [record["left_ca"] for record in records if record["left_ca"] is not None]
    right_values = [record["right_ca"] for record in records if record["right_ca"] is not None]
    average_values = [record["average_ca"] for record in records if record["average_ca"] is not None]
    tension_values = [record["surface_tension_mn_m"] for record in records if record["surface_tension_mn_m"] is not None]

    left = median_or_none(left_values)
    right = median_or_none(right_values)
    mean_angle = median_or_none(average_values)
    if mean_angle is None:
        mean_candidates = [value for value in (left, right) if value is not None]
        mean_angle = mean_or_none(mean_candidates)
    asymmetry = round(abs(left - right), 3) if left is not None and right is not None else None

    first = records[0]
    return {
        "sample_id": first["sample_id"],
        "group_id": first["group_id"],
        "group_key": key,
        "image_count": len(records),
        "source_images": [record["relative_path"] for record in records],
        "left_ca": left,
        "right_ca": right,
        "average_ca": mean_angle,
        "unit": "degree",
        "left_contact_angle_deg": left,
        "right_contact_angle_deg": right,
        "mean_contact_angle_deg": mean_angle,
        "left_right_difference_deg": asymmetry,
        "surface_tension_mn_m": median_or_none(tension_values),
        "ocr_records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_json")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    extracted_root, cleanup_root = extract_source(input_path)
    temp_ocr_dir = Path(tempfile.mkdtemp(prefix="contact_angle_ocr_"))
    try:
        images = find_images(extracted_root)
        if not images:
            raise FileNotFoundError(f"No supported images found under {extracted_root}")

        seen_hashes: dict[str, str] = {}
        grouped_records: dict[str, list[dict[str, object]]] = {}
        image_records: list[dict[str, object]] = []
        duplicate_paths: list[str] = []

        for image_path in images:
            relative_path = image_path.relative_to(extracted_root).as_posix()
            digest = sha256sum(image_path)
            if digest in seen_hashes:
                duplicate_paths.append(relative_path)
                continue

            seen_hashes[digest] = relative_path
            ocr_ready = prepare_for_ocr(image_path, temp_ocr_dir)
            ocr_text = run_tesseract(ocr_ready)
            metrics = parse_metrics(ocr_text)
            record = {
                "relative_path": relative_path,
                "sample_id": sample_id(image_path, extracted_root),
                "group_id": base_group_id(image_path),
                "group_key": group_key(image_path, extracted_root),
                "ocr_text": ocr_text,
                **metrics,
            }
            image_records.append(record)
            grouped_records.setdefault(record["group_key"], []).append(record)

        groups = [summarize_group(key, records) for key, records in sorted(grouped_records.items(), key=lambda item: item[0])]
        mean_values = [group["average_ca"] for group in groups if group["average_ca"] is not None]
        tension_values = [group["surface_tension_mn_m"] for group in groups if group["surface_tension_mn_m"] is not None]

        payload = {
            "source_file": str(input_path),
            "extracted_root_name": extracted_root.name,
            "ocr_engine": "tesseract-eng",
            "image_file_count": len(find_images(extracted_root)),
            "unique_image_count": len(seen_hashes),
            "duplicate_relative_paths": duplicate_paths,
            "image_records": image_records,
            "groups": groups,
            "overall": {
                "group_count": len(groups),
                "groups_with_contact_angle": sum(1 for value in mean_values if value is not None),
                "contact_angle_range_deg": [
                    round(min(mean_values), 3),
                    round(max(mean_values), 3),
                ]
                if mean_values
                else None,
                "mean_contact_angle_deg": mean_or_none(mean_values),
                "surface_tension_range_mn_m": [
                    round(min(tension_values), 3),
                    round(max(tension_values), 3),
                ]
                if tension_values
                else None,
            },
        }

        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        shutil.rmtree(temp_ocr_dir, ignore_errors=True)
        if cleanup_root is not None:
            shutil.rmtree(cleanup_root, ignore_errors=True)


if __name__ == "__main__":
    main()
