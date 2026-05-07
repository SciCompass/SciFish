#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from parse_raman_text import parse_raman_text, read_text_with_fallback


SUPPORTED_DATA_SUFFIXES = {".txt", ".csv", ".tsv"}
SUPPORTED_ARCHIVE_SUFFIXES = {".rar", ".zip"}
TEXT_NOTE_LIMIT = 1200


def safe_stem(path: Path) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in path.stem)


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def extract_archive(archive_path: Path, extract_dir: Path) -> None:
    ensure_clean_dir(extract_dir)
    try:
        subprocess.run(
            ["bsdtar", "-xf", str(archive_path), "-C", str(extract_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        return
    except FileNotFoundError as exc:
        # Fallback to patool when bsdtar is unavailable on Windows environments.
        try:
            import patoolib

            patoolib.extract_archive(str(archive_path), outdir=str(extract_dir), verbosity=-1)
            return
        except Exception as fallback_exc:
            raise RuntimeError("Failed to extract Raman archive bundle: bsdtar/patool unavailable") from fallback_exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise RuntimeError(f"Failed to extract archive {archive_path}: {message}") from exc


def collect_text(path: Path) -> str:
    return read_text_with_fallback(path).strip()


def iter_candidate_files(root: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_DATA_SUFFIXES
        ]
    )


def parse_bundle(input_path: Path, output_path: Path) -> dict:
    bundle_name = safe_stem(input_path)
    bundle_root = output_path.parent / bundle_name
    extract_dir = bundle_root / "extracted"
    parsed_dir = bundle_root / "parsed"
    ensure_clean_dir(parsed_dir)

    if input_path.is_file() and input_path.suffix.lower() in SUPPORTED_ARCHIVE_SUFFIXES:
        extract_archive(input_path, extract_dir)
        search_root = extract_dir
    elif input_path.is_dir():
        search_root = input_path
        extract_dir = input_path
    else:
        raise ValueError(f"Unsupported Raman bundle input: {input_path}")

    note_files: list[dict[str, str]] = []
    sample_groups: dict[str, list[dict[str, object]]] = {}

    for candidate in iter_candidate_files(search_root):
        relative_path = candidate.relative_to(search_root)
        try:
            payload = parse_raman_text(candidate)
        except ValueError:
            text = collect_text(candidate)
            if text:
                note_files.append(
                    {
                        "relative_path": str(relative_path),
                        "text": text[:TEXT_NOTE_LIMIT],
                    }
                )
            continue

        sanitized_rel = "__".join(relative_path.with_suffix("").parts)
        parsed_path = parsed_dir / f"{sanitized_rel}.parsed.json"
        parsed_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        sample_name = relative_path.parts[-2] if len(relative_path.parts) >= 2 else "root"
        sibling_images = sorted(
            [
                str(path.name)
                for path in candidate.parent.glob(f"{candidate.stem}*.jpg")
            ]
        )
        sample_groups.setdefault(sample_name, []).append(
            {
                "relative_path": str(relative_path),
                "source_file": str(candidate),
                "parsed_json": str(parsed_path),
                "preview_images": sibling_images,
            }
        )

    payload = {
        "source_file": str(input_path),
        "bundle_name": bundle_name,
        "extracted_dir": str(extract_dir),
        "note_files": note_files,
        "sample_groups": [
            {
                "sample_name": sample_name,
                "spectrum_count": len(entries),
                "spectra": entries,
            }
            for sample_name, entries in sorted(sample_groups.items())
        ],
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_json")
    args = parser.parse_args()

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = parse_bundle(Path(args.input_path), output_path)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
