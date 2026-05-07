# File Format Guide

## Accepted inputs

- `.xls` and `.xlsx`
- `.csv` and `.txt`

## Confirmed export pattern for sample-001

- Row 0 contains a run title such as `Ramp 10.00 °C/min to 820.00 °C`
- Row 1 contains text headers
- Row 2 contains units
- Numeric data starts on row 3
- Duplicate header names can occur, especially `Weight`

## Canonical columns

- `temperature_c`
- `time_min`
- `mass_mg`
- `mass_pct`
- `dtg`

At minimum, the parser should recover temperature plus either mass or mass percent.

## Alias mapping

- Temperature aliases: `Temperature`, `Temp`, `Sample Temp`, `Furnace Temp`
- Time aliases: `Time`, `min`, `Minute`, `Elapsed Time`
- Mass aliases: `Mass`, `Weight`, `TG`, `Sample Mass`
- Mass percent aliases: `Mass %`, `Weight %`, `%Weight`, `TG%`
- DTG aliases: `DTG`, `dW/dt`, `dm/dT`, `Deriv. Weight`

## Heuristics

- Skip rows that are mostly empty.
- Prefer the first contiguous numeric block with at least 20 rows.
- Trim rows after the numeric series terminates.
- Merge the header and unit rows before alias matching.
- If only raw mass exists, normalize against the first valid mass point.
- If temperature decreases overall, flag the file as suspicious.
