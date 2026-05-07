# Visualization Guide - Generic PL Analysis

## 1. Figure specifications

- Dimensions: single-column figure, default `3.5 x 2.6 inch`
- Font: Arial, Helvetica, or DejaVu Sans, minimum `8 pt`
- Data lines: dark charcoal plus one contrast color for multi-scan overlays
- Peak markers: muted red annotations for the top maxima

## 2. Axis conventions

- X-axis: `Emission wavelength (nm)`
- Y-axis: `Counts`
- X range: use the measured range from the parsed file
- Y range: extend slightly beyond the measured minimum and maximum

## 3. Required annotations

- Annotate the strongest `2-3` maxima for each main scan
- Use thin dashed guide lines for annotated peaks
- Keep labels offset to avoid overlap

## 4. Output files

- Primary: `output/figures/generic-pl-analysis/{sample}-emission-v1.pdf`
- Preview: `output/figures/generic-pl-analysis/{sample}-emission-v1.png`
- Report companion: `output/data/generic-pl-analysis/{sample}.report.zh.md`, with the PNG figure embedded in the Markdown body

## 5. Script reference

- Plot script: `scripts/plot_pl_spectrum.py`
- Key function: `plot_pl_spectrum(parsed_path, summary_path, output_stem)`
