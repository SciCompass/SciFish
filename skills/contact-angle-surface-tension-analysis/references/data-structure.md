# Parsed Data Structure

## Parsed JSON schema

```json
{
  "source_file": "datasets/generic-contact-angle-surface-tension-analysis/705_1704694767540_2401010773.rar",
  "extracted_root_name": "2401010773",
  "ocr_engine": "tesseract-eng",
  "image_file_count": 30,
  "unique_image_count": 30,
  "image_records": [
    {
      "relative_path": "2401010773/2-2.bmp",
      "sample_id": "2401010773",
      "group_id": "2",
      "left_ca": 80.2,
      "right_ca": 80.2,
      "average_ca": 80.2,
      "unit": "degree"
    }
  ],
  "groups": [
    {
      "sample_id": "2401010773",
      "group_id": "2",
      "image_count": 6,
      "source_images": ["2401010773/2.bmp", "2401010773/2-2.bmp"],
      "left_ca": 80.2,
      "right_ca": 80.2,
      "average_ca": 80.2,
      "unit": "degree",
      "left_contact_angle_deg": 80.2,
      "right_contact_angle_deg": 80.2,
      "mean_contact_angle_deg": 80.2,
      "left_right_difference_deg": 0.0,
      "surface_tension_mn_m": null,
      "ocr_records": []
    }
  ],
  "overall": {
    "group_count": 5,
    "groups_with_contact_angle": 5,
    "contact_angle_range_deg": [80.2, 121.9],
    "mean_contact_angle_deg": 106.9,
    "surface_tension_range_mn_m": null
  }
}
```

## Summary JSON schema

```json
{
  "measurement_mode_detected": "sessile_drop_contact_angle",
  "groups_with_contact_angle": 5,
  "groups_with_surface_tension": 0,
  "contact_angle_statistics": {
    "mean_deg": 106.9,
    "stdev_deg": 15.4,
    "min_deg": 80.2,
    "max_deg": 121.9
  },
  "data_quality_symmetry": {
    "left_right_difference_threshold_deg": 2.0,
    "groups_with_both_sides": 5,
    "groups_within_threshold": 4,
    "groups_over_threshold": 1,
    "within_threshold_ratio": 0.8,
    "overall_assessment": "mostly_symmetric_good_data_quality"
  },
  "group_summaries": [
    {
      "sample_id": "2401010773",
      "group_id": "2",
      "mean_contact_angle_deg": 80.2,
      "left_right_difference_deg": 0.2,
      "symmetry_assessment": "good_symmetry",
      "wettability_label": "hydrophilic_to_borderline"
    }
  ],
  "sample_summaries": [
    {
      "sample_id": "2401010773",
      "readable_group_count": 5,
      "mean_contact_angle_deg": 106.9,
      "wettability_label": "hydrophobic"
    }
  ],
  "cross_sample_comparison": {
    "enabled": true,
    "sample_count": 3,
    "ranking_by_mean_contact_angle_desc": [
      {
        "sample_id": "1",
        "mean_contact_angle_deg": 110.5
      },
      {
        "sample_id": "2",
        "mean_contact_angle_deg": 104.2
      }
    ],
    "highest_sample": {
      "sample_id": "1",
      "mean_contact_angle_deg": 110.5
    },
    "lowest_sample": {
      "sample_id": "3",
      "mean_contact_angle_deg": 95.1
    },
    "max_between_sample_diff_deg": 15.4,
    "assessment": "multi_sample_horizontal_comparison_completed"
  ],
  "interpretation_flags": [],
  "warnings": []
}
```

## Validation rules

- `mean_contact_angle_deg` should be the mean of visible left and right group medians.
- `left_right_difference_deg` should be flagged when the sides differ materially.
- `left_right_difference_threshold_deg` is fixed to `2.0` for routine symmetry assessment unless explicitly overridden by experts.
- Surface-tension values must remain `null` unless the OCR text contains an explicit surface-tension field.
- A group can be valid even when one side is missing, but the summary should note reduced confidence.
- Per-image extraction should always emit `left_ca`, `right_ca`, `average_ca`, and `unit`.
- `cross_sample_comparison` should be populated when sample count is 2 or more.
