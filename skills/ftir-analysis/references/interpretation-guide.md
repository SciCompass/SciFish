# Interpretation Guide

## Minimum reporting set

- available metadata and missing metadata
- spectral range and axis direction
- strongest absorption-like band
- main bands in the `4000-2500 cm^-1`, `2500-1500 cm^-1`, and `1500-400 cm^-1` regions
- whether broad hydroxyl/water-like features are present
- whether a strong carbonyl-like band near `1700-1750 cm^-1` is clearly present
- limitations caused by unlabeled signal type

## Interpretation rules

- Peak picking is adaptive to signal scale; compare peaks by relative prominence, not absolute raw value.
- Boundary-region peaks (near spectral start/end) can be valid but should be marked as lower confidence.
- A broad band around `3200-3600 cm^-1` can be consistent with O-H or N-H stretching, but assignment should remain conservative.
- A band near `1600-1650 cm^-1` may be consistent with adsorbed water bending, aromatic C=C, or other vibrations depending on context.
- Strong bands near `1000-1150 cm^-1` often indicate fingerprint-region skeletal vibrations; in oxide-rich systems they can be consistent with Si-O or related bonds.
- Absence of a dominant band near `1700-1750 cm^-1` should be described as absence of a clear strong carbonyl-like feature, not proof that all carbonyl species are absent.
- Fingerprint bands support screening and comparison, not definitive compound identification.

## Writing discipline

- Facts first, then tentative interpretation.
- Use conservative verbs.
- Explicitly call out missing instrument model, resolution, scan count, background condition, and signal labeling when absent.
- If endpoint values look clipped or processed, say that boundary features may be unreliable.
