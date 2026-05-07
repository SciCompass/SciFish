---
name: raman-analysis
description: Analyze Raman spectrum files, extract dominant bands, generate publication-ready spectra, and provide conservative band-assignment notes grounded in the measured signal.
allowed-tools: Bash, Read, Write, Edit
---

# Raman Analysis

Use this skill for Raman result files such as `.txt`, `.csv`, tabular text exports, and Raman bundles packaged as `.rar` or `.zip`. Keep conclusions grounded in the measured spectrum. Do not overclaim material identity, defect density, crystallinity, or chemistry when the file only supports peak-level evidence.

## Inputs

- Raw Raman files such as `.txt`, `.csv`, or tabular text exports
- Raman archive bundles such as `.rar` / `.zip` that contain multiple spectra, replicate folders, note files, or preview images

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. If the input is a single spectrum file, run `scripts/parse_raman_text.py` to extract the canonical `raman_shift_cm^-1` / `intensity_au` series.
3. If the input is a `.rar` or `.zip` bundle, run `scripts/parse_raman_bundle.py` first. This extracts the archive into `output/data/`, parses every numeric Raman text export, preserves non-numeric note files, and records sample-group membership.
4. Run `scripts/summarize_raman.py` on each parsed spectrum JSON to detect dominant bands, relative intensity, broad-background behavior, and simple carbon-screening anchors. If needed, pass `--config-json <path>` to tune artifact filtering and broad-band retention thresholds for a specific instrument/export style.
5. For archive bundles, run `scripts/summarize_raman_bundle.py` to aggregate per-spectrum summaries, compare replicates inside each sample folder, and surface shared bands plus note-file warnings such as fluorescence. Use `--config-json <path>` to force the same threshold profile across all spectra in the bundle.
6. Read `references/data-structure.md`, `references/interpretation-guide.md`, and `references/band-tables.md` before writing conclusions.
7. Run `scripts/plot_raman_spectrum.py` to generate `.pdf` and `.png` outputs in `output/figures/` for representative spectra or any file explicitly requested by the user.
8. Run `scripts/render_raman_report.py` to generate a standardized Chinese comprehensive analysis report in Markdown using the parsed JSON, summary JSON, and figure paths.
9. Report:
   - Raman-shift range, point spacing, and available metadata
   - strongest observed band positions and intensities
   - dominant and secondary bands with relative intensity
   - whether the spectrum suggests discrete bands on a low baseline or broad-band / fluorescence-influenced behavior
   - for bundles: which spectra belong to each sample group, which bands recur across replicates, and whether the bundle contains operator notes that constrain interpretation
   - any tentative band-assignment notes with explicit uncertainty
   - limitations and missing reference information
   - a Chinese comprehensive analysis report that embeds the figure and follows a fixed section order

## Output rules

- Quote numeric values with units.
- Distinguish observed bands from inferred assignments.
- Use wording such as `consistent with`, `may suggest`, or `tentatively corresponds to`.
- If no reference spectrum is available, say that the output is a peak-based screening result only.
- If note files or spectral shape suggest fluorescence background, say so explicitly and downgrade confidence in weak-band interpretation.
- For bundles, keep per-spectrum facts separate from across-replicate observations.
- If the file cannot be parsed, stop and explain what is missing or malformed.
- The Markdown report must embed the spectrum image and stay fact-first.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and parsing rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation logic and wording rules: `references/interpretation-guide.md`
- Common Raman band anchors and matching cautions: `references/band-tables.md`
- Figure conventions: `references/visualization-guide.md`

## Limits

- Do not claim definitive material identity without reference support.
- Do not infer defect density, layer number, or composition from a single uncalibrated spectrum.
- Do not treat noise spikes as true Raman bands.
- Do not flatten a Raman bundle into one synthetic spectrum; preserve per-file observations.
- Do not report quantitative band-area ratios unless the workflow explicitly computes them.
