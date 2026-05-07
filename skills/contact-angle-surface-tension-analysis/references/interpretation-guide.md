# Interpretation Guide

## Minimum reporting set

- number of distinct measurement groups
- left and right contact angle for each readable group
- mean contact angle and spread across groups
- whether each group is below or above the `90 deg` wettability boundary
- whether explicit surface-tension values are present
- confidence limits and missing metadata

## Interpretation rules

- Treat visible numeric overlays as the primary evidence.
- A contact angle below `90 deg` is more consistent with hydrophilic or borderline wetting.
- A contact angle above `90 deg` is more consistent with hydrophobic wetting.
- Do not describe a surface as superhydrophobic unless the angle is clearly near or above `150 deg`.
- If left and right angles differ noticeably, report the asymmetry instead of silently averaging it away.
- Use `|Left CA - Right CA|` as the hysteresis indicator for data-quality and symmetry checks.
- In routine contact-angle screenshots, left-right difference within `2 deg` usually supports good droplet symmetry and a reasonable baseline pick.
- Repeated differences above `2 deg` suggest possible contact-angle hysteresis, local roughness, chemical heterogeneity, or baseline-selection issues.
- If the same order includes multiple samples, include horizontal comparison by sample-level mean contact angle in the conclusion.

## Writing discipline

- Facts first, then interpretation.
- Distinguish OCR-derived values from manually verified values.
- Prefer `suggests`, `is consistent with`, or `does not support`.
- State explicitly when the current export lacks a visible surface-tension metric.
- Default deliverable is a Chinese report with both per-image extraction and per-sample wettability conclusions.
- For research audiences, include method criteria, horizontal sample comparison (when available), data quality/uncertainty, and material-chemistry-facing conclusions.
