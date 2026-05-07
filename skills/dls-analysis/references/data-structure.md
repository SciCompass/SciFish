# Parsed Data Structure

## Parsed JSON schema

```json
{
  "source_file": "path/to/file.xls",
  "sheet_name": "Auto-detected sheet name",
  "columns": {
    "size_nm": "Size classes (nm)",
    "intensity_pct": "Intensity Distribution Data (%)"
  },
  "metadata": {
    "record_label": "1 1",
    "distribution_kind": "intensity",
    "zeta_fields_present": false
  },
  "points": [
    {
      "index": 0,
      "size_nm": 0.4,
      "intensity_pct": 0.0
    }
  ]
}
```

## Summary JSON schema

```json
{
  "distribution_kind": "intensity",
  "size_range_nm": [0.4, 8634.99],
  "nonzero_range_nm": [531.17, 1106.44],
  "main_peak": {
    "size_nm": 824.99,
    "intensity_pct": 30.83
  },
  "top_peaks": [
    {
      "size_nm": 824.99,
      "intensity_pct": 30.83,
      "prominence": 27.2,
      "width_points": 4.17
    }
  ],
  "tail_flags": {
    "large_particle_tail": true,
    "tail_end_nm": 5559.64,
    "raw_tail_end_nm": 5559.64,
    "significant_floor_pct": 0.2
  },
  "warnings": [],
  "zeta_available": false
}
```

## Validation rules

- `size_nm` must be monotonically increasing.
- `intensity_pct` should not be globally negative.
- Parser must auto-detect a valid sheet/header pair; do not assume `Sheet1` exists.
- If all intensity values are `0`, treat the file as having no valid distribution.
- `top_peaks` should keep physically meaningful peaks (minimum peak-width filtering).
- If the high-size region exceeds the significant intensity floor and persists/strengthens, emit a tail warning.
- Even when there is a single dominant peak, still check for a low-intensity long tail.
