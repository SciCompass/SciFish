# Visualization Guide - Generic FTIR Style

## Figure Specifications

- Dimensions: single-column figure, default `3.6 x 2.7 inch`
- Font: Arial, Helvetica, or DejaVu Sans, minimum `8 pt`
- Data line: dark navy, `1.0-1.2 pt`
- Band markers: muted red annotations for the top bands

## Axis Conventions

- X-axis: `Wavenumber (cm^-1)`
- Y-axis: `Signal (a.u. or %)`
- Preferred display direction: descending wavenumber from left to right
- Y range: use the measured range with slight padding

## Required Annotations

- Annotate the strongest `3-5` absorption-like bands
- Keep labels offset so they do not overlap the spectrum
- If the response label is unknown, use a generic Y-axis title

## Output Files

- Primary: `output/figures/generic-ftir-analysis/{sample}-ftir-v1.pdf`
- Preview: `output/figures/generic-ftir-analysis/{sample}-ftir-v1.png`
