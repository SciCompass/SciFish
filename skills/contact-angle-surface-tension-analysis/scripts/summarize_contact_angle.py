#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def wettability_label(angle: float) -> str:
    if angle < 10:
        return "superhydrophilic"
    if angle < 90:
        return "hydrophilic_to_borderline"
    if angle < 150:
        return "hydrophobic"
    return "superhydrophobic"


def symmetry_label(left: float | None, right: float | None, threshold_deg: float) -> str:
    if left is None or right is None:
        return "insufficient_side_data"
    if abs(left - right) <= threshold_deg:
        return "good_symmetry"
    return "possible_hysteresis_or_surface_heterogeneity"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    groups = payload.get("groups", [])
    angle_groups = [group for group in groups if group.get("average_ca") is not None or group.get("mean_contact_angle_deg") is not None]
    tension_groups = [group for group in groups if group.get("surface_tension_mn_m") is not None]
    symmetry_threshold_deg = 2.0

    def group_angle(group: dict[str, object]) -> float | None:
        value = group.get("average_ca")
        if value is None:
            value = group.get("mean_contact_angle_deg")
        return float(value) if value is not None else None

    def group_side_value(group: dict[str, object], key: str) -> float | None:
        value = group.get(key)
        return float(value) if value is not None else None

    def side_pair(group: dict[str, object]) -> tuple[float | None, float | None]:
        left = group_side_value(group, "left_ca")
        if left is None:
            left = group_side_value(group, "left_contact_angle_deg")
        right = group_side_value(group, "right_ca")
        if right is None:
            right = group_side_value(group, "right_contact_angle_deg")
        return left, right

    mean_angles = [value for value in (group_angle(group) for group in angle_groups) if value is not None]
    asymmetry = [
        abs(left - right)
        for group in angle_groups
        for left, right in [side_pair(group)]
        if left is not None and right is not None
    ]

    warnings: list[str] = []
    if not angle_groups:
        warnings.append("No contact-angle values were extracted from the bundle.")
    if not tension_groups:
        warnings.append("No explicit surface-tension value was visible in the parsed screenshots.")
    if payload.get("duplicate_relative_paths"):
        warnings.append("Duplicate screenshots were detected and excluded from the summary.")

    summary = {
        "source_file": payload.get("source_file"),
        "measurement_mode_detected": "sessile_drop_contact_angle" if angle_groups else "unknown",
        "supported_metrics_visible": [
            "contact_angle_deg" if angle_groups else None,
            "surface_tension_mn_m" if tension_groups else None,
        ],
        "group_count": len(groups),
        "groups_with_contact_angle": len(angle_groups),
        "groups_with_surface_tension": len(tension_groups),
        "contact_angle_statistics": {
            "mean_deg": round(statistics.mean(mean_angles), 3) if mean_angles else None,
            "stdev_deg": round(statistics.pstdev(mean_angles), 3) if len(mean_angles) > 1 else 0.0 if mean_angles else None,
            "min_deg": round(min(mean_angles), 3) if mean_angles else None,
            "max_deg": round(max(mean_angles), 3) if mean_angles else None,
            "mean_left_right_difference_deg": round(statistics.mean(asymmetry), 3) if asymmetry else None,
        },
        "group_summaries": [
            {
                "sample_id": group.get("sample_id", "root"),
                "group_id": group["group_id"],
                "left_contact_angle_deg": group.get("left_ca", group.get("left_contact_angle_deg")),
                "right_contact_angle_deg": group.get("right_ca", group.get("right_contact_angle_deg")),
                "mean_contact_angle_deg": group.get("average_ca", group.get("mean_contact_angle_deg")),
                "left_right_difference_deg": (
                    round(
                        abs(left - right),
                        3,
                    )
                    if left is not None and right is not None
                    else None
                ),
                "symmetry_assessment": symmetry_label(
                    left,
                    right,
                    symmetry_threshold_deg,
                ),
                "wettability_label": wettability_label(group_angle(group))
                if group_angle(group) is not None
                else None,
                "surface_tension_mn_m": group.get("surface_tension_mn_m"),
            }
            for group in angle_groups or groups
            for left, right in [side_pair(group)]
        ],
        "sample_summaries": [],
        "cross_sample_comparison": {
            "enabled": False,
            "sample_count": 0,
            "ranking_by_mean_contact_angle_desc": [],
            "highest_sample": None,
            "lowest_sample": None,
            "max_between_sample_diff_deg": None,
            "assessment": "single_sample_no_horizontal_comparison",
        },
        "data_quality_symmetry": {
            "left_right_difference_threshold_deg": symmetry_threshold_deg,
            "groups_with_both_sides": 0,
            "groups_within_threshold": 0,
            "groups_over_threshold": 0,
            "within_threshold_ratio": None,
            "overall_assessment": "insufficient_side_data",
        },
        "interpretation_flags": [],
        "limitations": [
            "The current sample is a screenshot bundle, not a structured numeric report.",
            "Liquid identity, droplet volume, and acquisition method are not visible in the supplied images.",
            "OCR-derived values should be treated as approximate until checked against the original vendor export or multimodal cross-check.",
        ],
        "warnings": warnings,
    }

    sample_to_angles: dict[str, list[float]] = {}
    sample_to_asymmetry: dict[str, list[float]] = {}
    for group in angle_groups:
        value = group_angle(group)
        if value is None:
            continue
        sample = str(group.get("sample_id", "root"))
        sample_to_angles.setdefault(sample, []).append(value)
        left_value, right_value = side_pair(group)
        if left_value is not None and right_value is not None:
            sample_to_asymmetry.setdefault(sample, []).append(abs(left_value - right_value))
    for sample in sorted(sample_to_angles):
        values = sample_to_angles[sample]
        avg = float(statistics.mean(values))
        sample_asymmetry = sample_to_asymmetry.get(sample, [])
        within_count = sum(1 for val in sample_asymmetry if val <= symmetry_threshold_deg)
        summary["sample_summaries"].append(
            {
                "sample_id": sample,
                "readable_group_count": len(values),
                "mean_contact_angle_deg": round(avg, 3),
                "min_contact_angle_deg": round(min(values), 3),
                "max_contact_angle_deg": round(max(values), 3),
                "mean_left_right_difference_deg": round(statistics.mean(sample_asymmetry), 3) if sample_asymmetry else None,
                "groups_with_both_sides": len(sample_asymmetry),
                "groups_within_symmetry_threshold": within_count,
                "wettability_label": wettability_label(avg),
            }
        )

    sample_rank = sorted(
        summary["sample_summaries"],
        key=lambda item: item["mean_contact_angle_deg"],
        reverse=True,
    )
    summary["cross_sample_comparison"]["sample_count"] = len(sample_rank)
    if len(sample_rank) >= 2:
        highest = sample_rank[0]
        lowest = sample_rank[-1]
        max_diff = highest["mean_contact_angle_deg"] - lowest["mean_contact_angle_deg"]
        summary["cross_sample_comparison"].update(
            {
                "enabled": True,
                "ranking_by_mean_contact_angle_desc": [
                    {
                        "sample_id": item["sample_id"],
                        "mean_contact_angle_deg": item["mean_contact_angle_deg"],
                        "wettability_label": item["wettability_label"],
                    }
                    for item in sample_rank
                ],
                "highest_sample": {
                    "sample_id": highest["sample_id"],
                    "mean_contact_angle_deg": highest["mean_contact_angle_deg"],
                    "wettability_label": highest["wettability_label"],
                },
                "lowest_sample": {
                    "sample_id": lowest["sample_id"],
                    "mean_contact_angle_deg": lowest["mean_contact_angle_deg"],
                    "wettability_label": lowest["wettability_label"],
                },
                "max_between_sample_diff_deg": round(max_diff, 3),
                "assessment": "multi_sample_horizontal_comparison_completed",
            }
        )
    elif len(sample_rank) == 1:
        only = sample_rank[0]
        summary["cross_sample_comparison"].update(
            {
                "ranking_by_mean_contact_angle_desc": [
                    {
                        "sample_id": only["sample_id"],
                        "mean_contact_angle_deg": only["mean_contact_angle_deg"],
                        "wettability_label": only["wettability_label"],
                    }
                ],
                "highest_sample": {
                    "sample_id": only["sample_id"],
                    "mean_contact_angle_deg": only["mean_contact_angle_deg"],
                    "wettability_label": only["wettability_label"],
                },
                "lowest_sample": {
                    "sample_id": only["sample_id"],
                    "mean_contact_angle_deg": only["mean_contact_angle_deg"],
                    "wettability_label": only["wettability_label"],
                },
            }
        )

    groups_with_both_sides = len(asymmetry)
    groups_within_threshold = sum(1 for value in asymmetry if value <= symmetry_threshold_deg)
    groups_over_threshold = groups_with_both_sides - groups_within_threshold
    summary["data_quality_symmetry"]["groups_with_both_sides"] = groups_with_both_sides
    summary["data_quality_symmetry"]["groups_within_threshold"] = groups_within_threshold
    summary["data_quality_symmetry"]["groups_over_threshold"] = groups_over_threshold
    if groups_with_both_sides > 0:
        ratio = groups_within_threshold / groups_with_both_sides
        summary["data_quality_symmetry"]["within_threshold_ratio"] = round(ratio, 3)
        if ratio >= 0.8:
            summary["data_quality_symmetry"]["overall_assessment"] = "mostly_symmetric_good_data_quality"
        elif ratio >= 0.5:
            summary["data_quality_symmetry"]["overall_assessment"] = "mixed_symmetry_needs_spot_check"
        else:
            summary["data_quality_symmetry"]["overall_assessment"] = "frequent_asymmetry_possible_hysteresis_or_nonuniform_surface"

    if mean_angles:
        overall_mean = statistics.mean(mean_angles)
        summary["interpretation_flags"].append(
            f"Overall mean contact angle is about {overall_mean:.1f} deg, which is consistent with {wettability_label(overall_mean).replace('_', ' ')} behavior."
        )
        if min(mean_angles) < 90 < max(mean_angles):
            summary["interpretation_flags"].append(
                "The bundle spans both below-90 deg and above-90 deg groups, so wettability is not uniform across the visible measurements."
            )
        elif overall_mean >= 90:
            summary["interpretation_flags"].append(
                "Most visible groups fall on the hydrophobic side of the 90 deg boundary."
            )
        else:
            summary["interpretation_flags"].append(
                "Most visible groups stay below the 90 deg boundary and are more consistent with hydrophilic or borderline wetting."
            )
    if groups_with_both_sides > 0:
        summary["interpretation_flags"].append(
            f"Left-right difference <= {symmetry_threshold_deg:.1f} deg appears in {groups_within_threshold}/{groups_with_both_sides} groups."
        )

    Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
