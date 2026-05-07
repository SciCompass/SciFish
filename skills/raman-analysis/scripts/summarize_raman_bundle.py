#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from summarize_raman import load_rules, load_series, summarize_raman


MERGE_TOLERANCE_CM = 12.0
TOP_BANDS_PER_SPECTRUM = 6


def merge_band_clusters(entries: list[dict[str, float]]) -> list[dict[str, float]]:
    clusters: list[dict[str, object]] = []
    for entry in sorted(entries, key=lambda item: item["raman_shift_cm^-1"]):
        matched = None
        for cluster in clusters:
            if abs(cluster["center"] - entry["raman_shift_cm^-1"]) <= MERGE_TOLERANCE_CM:
                matched = cluster
                break
        if matched is None:
            matched = {
                "center": entry["raman_shift_cm^-1"],
                "occurrence_count": 0,
                "max_relative_intensity_pct": 0.0,
                "values": [],
            }
            clusters.append(matched)
        matched["values"].append(entry["raman_shift_cm^-1"])
        matched["occurrence_count"] += 1
        matched["max_relative_intensity_pct"] = max(
            matched["max_relative_intensity_pct"],
            entry["relative_intensity_pct"],
        )
        matched["center"] = sum(matched["values"]) / len(matched["values"])

    return [
        {
            "raman_shift_cm^-1": round(float(cluster["center"]), 3),
            "occurrence_count": int(cluster["occurrence_count"]),
            "max_relative_intensity_pct": round(float(cluster["max_relative_intensity_pct"]), 2),
        }
        for cluster in sorted(
            clusters,
            key=lambda item: (-int(item["occurrence_count"]), -float(item["max_relative_intensity_pct"])),
        )
    ]


def summarize_bundle(
    bundle_payload: dict,
    rules: dict[str, Any] | None = None,
    config_path: str | None = None,
) -> dict:
    note_text = "\n".join(note["text"] for note in bundle_payload.get("note_files", []))
    note_text_lower = note_text.lower()
    fluorescence_noted = any(
        token in note_text_lower
        for token in ("fluorescence", "荧光", "螢光", "鑽у厜")
    )
    sample_groups_summary: list[dict[str, object]] = []

    for group in bundle_payload.get("sample_groups", []):
        spectra_summary: list[dict[str, object]] = []
        recurring_input: list[dict[str, float]] = []
        fluorescence_hits = 0

        for spectrum in group.get("spectra", []):
            parsed_path = Path(spectrum["parsed_json"])
            x, y = load_series(parsed_path)
            summary = summarize_raman(x, y, rules=rules)
            if summary["fluorescence_screening"]["likely_present"]:
                fluorescence_hits += 1
            summary["parsed_json"] = str(parsed_path)
            summary["relative_path"] = spectrum["relative_path"]
            summary["preview_images"] = spectrum.get("preview_images", [])
            spectra_summary.append(summary)
            recurring_input.extend(summary["dominant_bands"][:TOP_BANDS_PER_SPECTRUM])

        sample_groups_summary.append(
            {
                "sample_name": group["sample_name"],
                "spectrum_count": len(spectra_summary),
                "fluorescence_like_spectrum_count": fluorescence_hits,
                "recurring_bands": merge_band_clusters(recurring_input),
                "spectra": spectra_summary,
            }
        )

    payload = {
        "bundle_source_file": bundle_payload["source_file"],
        "note_flags": {
            "fluorescence_noted": fluorescence_noted,
            "note_file_count": len(bundle_payload.get("note_files", [])),
        },
        "note_files": bundle_payload.get("note_files", []),
        "sample_groups": sample_groups_summary,
    }
    if config_path:
        payload["analysis_config"] = config_path
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_json")
    parser.add_argument("output_json")
    parser.add_argument("--config-json", default=None)
    args = parser.parse_args()

    bundle_payload = json.loads(Path(args.bundle_json).read_text(encoding="utf-8"))
    rules = load_rules(Path(args.config_json)) if args.config_json else None
    payload = summarize_bundle(bundle_payload, rules=rules, config_path=args.config_json)

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
