# File Format Guide

## Accepted inputs

- `.zip` packages containing PL `.txt` exports
- standalone PL `.txt` exports with the same header-plus-data layout

## Confirmed export pattern for the current archive

The uploaded archive contains two readable text members:

- `2401011361/Em-Ex808.txt`
- `2401011361/H2O-Em-Ex808.txt`

Each text file contains:

1. comma-separated metadata rows
2. one blank line
3. a numeric block with wavelength and counts

## Canonical columns

- `emission_wavelength_nm`
- `counts`

## Metadata keys worth preserving

- `Labels`
- `Type`
- `Start`
- `Stop`
- `Step`
- `Fixed/Offset`
- `Xaxis`
- `Yaxis`
- `Repeats`
- `Dwell Time`
- `Lamp`
- `Detector`

## Heuristics

- Treat the first stable two-column numeric block as the emission data block.
- Keep scan metadata even when the binary `.FS` members are not decoded.
- Sort by `emission_wavelength_nm` if needed.
- Keep raw counts unchanged in the parsed output.
- Record unsupported archive members in the parsed metadata instead of failing silently.

## Parser expectations

The parser should output:

- `source_file`
- `archive_members`
- `unparsed_members`
- `scans`

Each scan should contain:

- `scan_name`
- `measurement_type`
- `metadata`
- `summary`
- `points`
