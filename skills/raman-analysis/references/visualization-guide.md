# Visualization Guide - Generic Raman Analysis

## 1. Figure Specifications

- Dimensions: single-column figure, default `3.5 x 2.6 inch`
- Font: Arial, Helvetica, or DejaVu Sans, minimum `8 pt`
- Data line: dark charcoal or deep blue, `1.0-1.2 pt`
- Band markers: muted red annotations for the top bands

## 2. Axis Conventions

- X-axis: `Raman shift (cm^-1)`
- Y-axis: `Intensity (a.u.)`
- X range: use the measured range from the parsed file
- Y range: start slightly below the measured minimum unless the baseline would be clipped

## 3. Required Annotations

- Annotate the strongest `3-5` bands with their `cm^-1` values
- Use thin dashed guide lines for annotated bands
- Keep labels offset so they do not overlap the data line

## 4. Output Files

- Primary: `output/figures/generic-raman-analysis/{sample}-spectrum-v1.pdf`
- Preview: `output/figures/generic-raman-analysis/{sample}-spectrum-v1.png`

## 5. Script Reference

- Plot script: `scripts/plot_raman_spectrum.py`
- Key function: `plot_raman_spectrum(parsed_path, summary_path, output_stem)`
