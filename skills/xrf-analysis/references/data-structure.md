# Data Structure

## Parsed JSON schema

```json
{
  "source_file": "datasets/generic-xrf-analysis/2266_1704452948947_2401010177.rar",
  "sample_name": "1-1石英",
  "metadata": {
    "文件名": "1-1石英",
    "样品名": "1-1石英",
    "分析日期": "2024-01-05 09:34",
    "样品类型": "氧化物粉末",
    "组分类型": "氧化物"
  },
  "semiquant": [
    {
      "component": "SiO2",
      "result_mass_pct": 49.2477,
      "result_unit": "mass%",
      "detection_limit": 0.04167,
      "element_line": "Si-KA",
      "line_intensity": 31.079,
      "normalized_weight_percent": 24.1897
    }
  ],
  "scan": {
    "line_label": "Ca-KA",
    "axis_name": "2theta_deg",
    "scan_window_label": "100- 300",
    "summary": {
      "point_count": 5600,
      "axis_range_deg": [5.0, 148.01],
      "relative_intensity_range": [0.0, 31.2499]
    },
    "points": [
      {
        "2theta_deg": 110.0,
        "relative_intensity": 0.05916
      }
    ]
  }
}
```

## Summary JSON schema

```json
{
  "sample_name": "1-1石英",
  "major_components": [
    {
      "component": "SiO2",
      "result_mass_pct": 49.2477
    }
  ],
  "low_level_components": [
    {
      "component": "Y2O3",
      "result_mass_pct": 0.0018,
      "detection_limit": 0.00521
    }
  ],
  "scan_overview": {
    "line_label": "Ca-KA",
    "point_count": 5600,
    "axis_range_deg": [5.0, 148.01]
  },
  "warnings": []
}
```

## Normalization rules

- Store numeric values as floats.
- Preserve original metadata keys from the source file.
- Keep semi-quantitative rows sorted by descending `result_mass_pct` in the summary layer.
- Keep scan points sorted by increasing scan axis value.
- Put caveats about interpretation into `warnings`.
