# Interpretation Guide

## Minimum reporting set

- confirmed analysis mode visible in the file
- temperature range and point count
- measured flow rate and sample mass when present
- dominant event temperature and direction
- any secondary low-, mid-, or high-temperature events worth noting
- confidence limits and missing calibration information

## Interpretation rules

- Use the vendor metadata to label the run as TPD, TPR, or TPO. Do not infer the mode from chemistry language alone.
- Treat peak temperature as the most defensible summary metric from this export.
- Relative signal height and prominence can support comparison within the same dataset, but they are not absolute uptake values.
- When the profile shows broad or overlapping structure, describe it as broad or overlapping instead of forcing separate event assignments.
- If a software report says no peaks are available, continue analyzing the trace itself.

## Writing discipline

- Facts first, then interpretation.
- Separate file-reported values from derived values.
- Prefer `suggests`, `is consistent with`, or `does not by itself prove`.
- State clearly when the current evidence only validates the TPR path of the family skill.
