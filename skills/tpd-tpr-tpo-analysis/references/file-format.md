# File Format Guide

## Accepted inputs

- `.xls` report exports from AutoChem II 2920
- zipped bundles that contain `.xls` plus optional `.pdf` and `.smp`
- `.pdf` and `.smp` may be archived, but `.xls` is the primary parse target

## Confirmed layout for the current dataset

- The workbook has a single sheet named `Sheet1`.
- The sheet is page-oriented rather than table-oriented.
- Metadata appears in the top-left area.
- The numeric region is split into three blocks:
  - columns `5-6`: `Signal (a.u.) vs. Time`
  - columns `10-11`: `Temperature vs. Time`
  - columns `15-16`: `Signal (a.u.) vs. Temperature`
- The trace header row contains:
  - `Time (minutes)`
  - `Signal (a.u.)`
  - `Temperature (°C)`

## Canonical columns

- `time_min`
- `signal_au_vs_time`
- `time_min_for_temperature`
- `temperature_c_vs_time`
- `temperature_c`
- `signal_au`

## Parsing rules

- Read the workbook with `header=None`.
- Find the header row by searching for the panel labels, not by assuming a fixed row number.
- Extract metadata by scanning for key-value labels such as `Analysis type:` and `Measured flow rate:`.
- Use `temperature_c` and `signal_au` as the canonical curve for peak analysis.
- Preserve the signal inversion flag as metadata.

## Practical warning

The current real dataset verifies the TPR layout only. If a future TPD or TPO file changes the panel order or labels, update the parser before trusting the result.
