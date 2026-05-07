# Interpretation Guide

## Minimum reporting set

- instrument and software context, if present in the export
- wavelength range, step size, and signal label
- strongest visible-region maximum for each sample
- ranking of samples by peak absorbance
- comment on whether maxima are clustered or shifted across the batch
- long-wavelength baseline comment for `700-800 nm`
- explicit statement of interpretation limits

## Pattern reading rules

- A broad maximum in the visible region can support comparative statements such as stronger or weaker visible absorption.
- A shift in the maximum toward longer wavelength may be described as a red shift in the observed absorption maximum, but not as a mechanistic explanation.
- Long-wavelength residual absorbance can support conservative comments about whether absorption tails extend into the red end of the measured window.
- Derivative-based edge markers are only screening aids. Report them as edge-like markers, not definitive optical band edges.

## Eg decision rules

- First read per-sample `eg_assessment` from `summarize_uvvis_drs.py`.
- For algorithm details (mode transform, thresholds, candidate ranking), follow `references/eg-algorithm-flow.md`.
- Default threshold profile is: `R2 >= 0.995`, Eg in `1.5-4.5 eV`, segment y-span >= 10%, and top-2 candidate output.
- Eg in this workflow is only valid for absorbance/reflectance context and powder/bulk-like samples.
- Tauc linear regions are extracted with the recursive segmentation rule in `scripts/line_fit.py` (`R_tol` aligned with current `R2_THRESHOLD`), with rolling-window fallback for robustness.
- Only quote Eg when `meaningful_for_eg = true` and at least one valid Tauc linear candidate is present.
- Preferred reported values are `selected_direct_eg_ev` and `selected_indirect_eg_ev` with candidate quality (`r2`, segment bounds).
- If `decision = peak_only`, do not force Eg interpretation. Use peak position, shift trend, and baseline-tail comparison instead.
- Always preserve the skip reason (`eg_assessment.reason`) when Eg is not reported.

## Writing discipline

- Facts first, interpretation second.
- Quote wavelength values in `nm`.
- If the export is absorbance-domain, say so before discussing any reflectance-domain methods.
- State clearly when a stronger claim would require reflectance data, sample identity, thickness information, or calibration.
- Use mandatory report structure: `Results` -> `Discussion`.
- In `Discussion`, explicitly separate supported conclusions from non-supported claims.

## Forbidden shortcuts

- Do not claim a numerical band gap when Eg screening fails.
- Do not identify a pigment, semiconductor, or dopant solely from one broad maximum.
- Do not describe the current `200-800 nm` export as a full NIR result set.
