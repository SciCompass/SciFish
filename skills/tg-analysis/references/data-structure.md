# Parsed Data Structure

## Parsed JSON schema

```json
{
  "source_file": "path/to/file.xls",
  "sheet_name": "Sheet1",
  "columns": {
    "temperature_c": "Temperature",
    "mass_pct": "Weight%"
  },
  "points": [
    {
      "temperature_c": 30.0,
      "time_min": 0.0,
      "mass_mg": 10.52,
      "mass_pct": 100.0,
      "dtg": -0.01
    }
  ]
}
```

## Summary JSON schema

```json
{
  "temperature_range_c": [30.0, 800.0],
  "initial_mass_pct": 100.0,
  "final_mass_pct": 21.3,
  "total_mass_loss_pct": 78.7,
  "stages": [
    {
      "start_c": 42.0,
      "peak_c": 87.0,
      "end_c": 126.0,
      "mass_loss_pct": 4.3
    }
  ],
  "warnings": []
}
```

## Validation rules

- Temperature should be monotonic non-decreasing.
- Mass percent should generally decrease or plateau.
- Final residue cannot exceed initial mass percent by more than minor numeric noise.
- Stage boundaries are approximate and should be labeled as such in prose.
- Duplicate temperature rows should be averaged before numerical derivative estimation.
