# Interpretation Guide

## Minimum reporting set

- whether readable steady-state and/or transient data are present
- scan labels and key acquisition metadata
- wavelength range and step size for each scan
- strongest emission maximum for each scan
- secondary maxima when they are separated from noise
- scan-to-scan relative intensity differences
- a strict statement of interpretation limits

## Pattern reading rules

- Report observed emission maxima first, then any tentative interpretation.
- A stronger signal in one scan than another can be reported descriptively, but the cause should not be inferred without sample context.
- If counts cross below zero, treat the baseline as offset or noise affected; do not overinterpret weak low-count maxima.
- If multiple maxima cluster tightly, describe them as a broad high-intensity region with local maxima unless clear separation is evident.
- If transient-readable data are absent, explicitly state that no lifetime fitting or decay analysis was performed.

## Current archive anchors

For the current archive, automated extraction shows:

- `Em-Ex808` strongest point near `1549.0 nm`
- `H2O-Em-Ex808` strongest point near `1548.0 nm`
- `H2O-Em-Ex808` is weaker than `Em-Ex808` by raw maximum-count comparison

These are archive-specific anchors, not universal PL rules.

## Writing discipline

- Facts first, interpretation second.
- Quote wavelengths with `nm`.
- If a mechanism is unknown, say it is unknown.
- State clearly when only steady-state emission data are available.
