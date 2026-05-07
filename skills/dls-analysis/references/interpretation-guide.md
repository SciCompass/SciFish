# Interpretation Guide

## Minimum reporting set

- File type and whether parsing succeeded
- Distribution kind: intensity distribution
- Main peak particle size
- Main peak intensity percentage
- Non-zero size range
- Whether a large-particle tail is present
- Whether multi-peak or broad-peak behavior is present
- Whether zeta data is available

## Interpretation rules

- When the dominant intensity peak is large, describe it as the size range that dominates the intensity response.
- If the non-zero range extends into the multi-micron region, describe it as a large-particle tail or possible aggregate fraction.
- Do not rewrite an intensity distribution as if it were the most common particle count size.
- If the export lacks zeta fields, say explicitly that zeta potential cannot be determined from the current file.

## Current sample anchors

Based on the automated extraction from the current `15` `.xls` files:

- Main peak particle sizes are roughly between `396` and `825 nm`.
- Groups `1` and `2` tend to have larger main peaks.
- Group `5` includes smaller main peaks, but several files also show long tails.
- Multiple files extend their non-zero range to `5559.64 nm`.

These values are anchors for this archive only and must not be generalized as global DLS rules.

## Writing discipline

- Facts first, interpretation second.
- Use conservative wording such as `suggests`, `may indicate`, or `is consistent with`.
- If data is missing, say exactly what is missing.
