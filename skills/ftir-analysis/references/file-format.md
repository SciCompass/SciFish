# File Format Guide

## Accepted inputs

- `.csv`
- `.txt`
- `.xls`
- `.xlsx`

## Generic export assumptions

- Two-column numeric table is preferred.
- Column 1 is wavenumber in `cm^-1`.
- Column 2 is a measured spectral response channel (label may be missing).
- Header rows are optional; parser should coerce numeric rows and drop non-numeric lines.

## Canonical columns

- `wavenumber_cm1`
- `signal`

## Parsing and interpretation heuristics

- Preserve acquisition order and record axis direction (`ascending` or `descending`).
- Keep `signal_label` as `unknown` when metadata does not explicitly identify absorbance/transmittance.
- Use adaptive signal-mode inference:
  - treat as absorbance-like when value distribution matches absorbance behavior;
  - otherwise transform as transmittance-like (`1 - signal`) for peak picking.
- Apply scale-adaptive peak thresholds; avoid fixed assumptions such as `0-100`.
- Flag zero or clipped endpoints as potential preprocessing artifacts.
