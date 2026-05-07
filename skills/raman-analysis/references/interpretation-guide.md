# Interpretation Guide

## Minimum reporting set

- Raman-shift range and point spacing
- strongest band positions
- dominant and secondary bands with relative intensity
- spectrum-level comment on whether the signal is dominated by discrete bands or broad features
- statement of whether assignment notes are tentative or unsupported

## Pattern reading rules

- Narrow, prominent bands suggest discrete vibrational features.
- Broad envelopes without clear maxima should be described as broad-band behavior rather than sharply resolved bands.
- Do not identify a material from one band alone.
- If several dominant bands align with a known reference family, describe the match as tentative unless an explicit reference source is used.
- If operator notes or the spectral baseline indicate fluorescence, say that weak-band assignment confidence is reduced.
- For replicate bundles, prioritize bands that recur across the sample-folder replicates over one-off peaks in a single file.

## Current sample anchor

For `1-1.txt`, the current automated extraction indicates dominant bands near:

- `1343.080 cm^-1`
- `1591.780 cm^-1`
- `679.235 cm^-1`
- `2851.820 cm^-1` (broad high-shift envelope)

These positions are sample-specific anchors, not universal Raman rules.

## Bundle-specific interpretation

- Keep each spectrum as an independent observation first, then summarize recurring bands at the sample-group level.
- Preview images inside the bundle are supplementary context only; do not infer chemistry from image appearance alone.
- If a bundle note mentions fluorescence at a given excitation wavelength, explicitly connect that note to any broad rising baseline or high background in the measured spectra.
- When replicate spectra disagree materially, report the disagreement instead of averaging it away.

## Writing discipline

- Facts first, interpretations second.
- Quote band positions with `cm^-1`.
- If a tentative assignment is made, name the supporting band set.
- State missing reference spectra and missing instrument metadata explicitly.
- If the data are fluorescence-influenced, say that the result is a conservative screening readout rather than a definitive band-assignment report.
