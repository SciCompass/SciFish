# Parsed Data Structure

## Parsed JSON schema

```json
{
  "source_file": "path/to/1.XLS",
  "metadata": {
    "sample_label": "h2-tpr",
    "analysis_type": "Temperature Programmed Reduction",
    "analysis_mode": "TPR"
  },
  "trace_columns": {
    "temperature_c": "Temperature (°C)",
    "signal_au": "Signal (a.u.)"
  },
  "point_count": 4496,
  "temperature_range_c": [51.285, 798.027],
  "signal_range_au": [-0.002978, 0.004902],
  "points": [
    {
      "time_min": 0.0,
      "signal_au_vs_time": 0.0,
      "time_min_for_temperature": 0.0,
      "temperature_c_vs_time": 51.284657,
      "temperature_c": 51.284657,
      "signal_au": 0.0
    }
  ]
}
```

## Summary JSON schema

```json
{
  "analysis_mode": "TPR",
  "temperature_range_c": [51.28, 798.03],
  "dominant_event": {
    "peak_temperature_c": 440.53,
    "peak_signal_au": 0.006375,
    "prominence_au": 0.00282,
    "direction": "positive",
    "temperature_band": "mid-temperature"
  },
  "positive_events": [],
  "negative_events": [],
  "warnings": []
}
```

## Validation rules

- `temperature_c` should be non-decreasing after parsing.
- `point_count` should be in the expected thousands for a full report trace.
- Peak temperatures are approximate and depend on smoothing and prominence thresholds.
- Event direction should not be interpreted blindly when the vendor report says `Signal inverted: Yes`.
