# Parsed Data Structure

## Parsed JSON schema

```json
{
  "source_file": "datasets/generic-ftir-analysis/sample.csv",
  "metadata": {
    "row_count": 7469,
    "axis_direction": "ascending",
    "signal_label": "unknown"
  },
  "columns": {
    "wavenumber_cm1": "column_0",
    "signal": "column_1"
  },
  "points": [
    {
      "index": 0,
      "wavenumber_cm1": 399.6747,
      "signal": 0.0
    }
  ]
}
```

## Summary JSON schema

```json
{
  "wavenumber_range_cm1": [399.6747, 4000.1230],
  "signal_range": [0.0, 0.0965],
  "main_bands": [
    {
      "wavenumber_cm1": 1047.8,
      "signal": 0.0814,
      "prominence": 0.0456,
      "region": "fingerprint"
    }
  ],
  "detection_mode": "absorbance | transmittance_to_absorbance",
  "peak_pick_params": {
    "prominence": 0.0020,
    "distance_points": 14,
    "savgol_window": 25,
    "width_min_points": 12,
    "min_height": 0.0316
  },
  "broad_band_flags": {
    "oh_nh_like": false,
    "water_bending_like": false,
    "strong_carbonyl_like": false
  },
  "warnings": []
}
```

## Validation rules

- The spectrum must contain at least 100 numeric points.
- Wavenumber values should be strictly monotonic after parsing.
- Peak detection must be adaptive to signal scale; do not assume a fixed `0-100` signal range.
- Summary bands are derived from absorption-like peaks after automatic signal-mode normalization.
- Reported `wavenumber_cm1` may be refined to sub-grid precision.
- Reported `signal` is interpolated from original measured points at the refined coordinate.
- Broad-band flags are screening aids and must not be treated as definitive assignments.
