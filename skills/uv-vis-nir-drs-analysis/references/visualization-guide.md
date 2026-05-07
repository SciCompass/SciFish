# Visualization Guide - Shimadzu UV-Vis DRS Style

## Figure specifications

- Dimensions: single-column figure, default `3.8 x 2.8 inch`
- Font: Arial, Helvetica, or DejaVu Sans, minimum `8 pt`
- Line width: `1.0-1.2 pt`
- Use distinct, color-blind-safe colors for each sample
- Annotate one main maximum per sample

## Axis conventions

- X-axis: `Wavelength (nm)`
- Y-axis: `Absorbance (a.u.)`
- X range: the measured range, normally `200-800 nm` for the current batch
- Y range: start slightly below the minimum measured absorbance

## Required annotations

- Label each sample in a legend
- Mark the main maximum for each sample with a point and wavelength label
- Keep labels offset to avoid overlapping traces

## Output files

- Primary: `output/figures/shimadzu-uv-3600-plus-drs/{archive-stem}-overlay-v1.pdf`
- Preview: `output/figures/shimadzu-uv-3600-plus-drs/{archive-stem}-overlay-v1.png`

## Script reference

- Plot script: `scripts/plot_uvvis_drs.py`
