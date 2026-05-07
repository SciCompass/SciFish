---
name: tg-analysis
description: Analyze TG/TGA thermogravimetric data files, explain mass-loss stages, DTG peaks, onset temperatures, residue, and likely thermal events, and generate publication-ready TG/DTG figures. Use this when the user provides TG, TGA, thermogravimetric, or thermal decomposition result files such as .xls, .xlsx, .csv, or .txt, including NETZSCH CSV exports, or asks for a scientific-quality TG/DTG plot.
allowed-tools: Bash, Read, Write, Edit
---

# TG Analysis

Use this skill for thermogravimetric result files. Keep the analysis grounded in the measured curve. Do not infer composition, reaction mechanism, or phase identity unless the data directly supports it.

## Inputs

- Raw data files such as `.xls`, `.xlsx`, `.csv`, `.txt`
- Optional instrument notes under `instruments/generic-tg-analysis/`
- Optional expert Q/A under `datasets/generic-tg-analysis/`

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. Run `scripts/parse_tg_xls.py` as the default parser for `.xls`, `.xlsx`, `.csv`, and `.txt` TG exports. Despite the filename, it now handles Excel-like exports, NETZSCH-style text exports, and NETZSCH `.xlsx` sheets with long `#KEY:` metadata preambles before the numeric table.
3. Run `scripts/summarize_tg.py` on the parsed table to estimate TG step regions, DTG peaks, onset temperatures, mass loss, and residue. This script now uses a Savitzky-Golay step-analysis method with DDTG-based start/end detection, low-temperature initial-loss peak injection, overlap splitting, and adjacent-step merging for partially resolved events.
4. If the user asks for a detailed engineering-style TG step plot, run `scripts/plot_tg_steps.py` on the parsed JSON.
5. If the user asks for a publication-grade figure, read `references/visualization-guide.md` and run `scripts/plot_tg_publication.py` with the parsed JSON, summary JSON, and an output base path.
6. Run `scripts/generate_tg_report.py` after analysis. Pass the parsed JSON, summary JSON, final report output path, and the matching figure directory or prefix so every generated TG image is embedded structurally into the report body.
7. Read `references/data-structure.md` and `references/interpretation-guide.md` before writing conclusions.
8. Report:
   - sample and experiment information needed by materials-chemistry researchers
   - temperature range and initial/final mass or mass percent
   - each main stage with onset, peak, end, start mass, end mass, and percent loss
   - final residue
   - embedded figure sections covering all generated TG result images
   - confidence limits and any missing signals

## Output rules

- Quote numeric values with units.
- If only approximate onset or end points can be determined, state that they are approximate.
- Separate observed facts from interpretations.
- Prefer "suggests", "consistent with", or "may indicate" over definitive claims.
- If DTG is missing and was numerically estimated, say so.
- Treat automatically detected TG step boundaries as algorithmic estimates, especially for overlapping or truncated high-temperature events.
- For publication-style figures, prefer vector outputs (`.pdf`, `.svg`) plus high-resolution raster outputs (`.png`, `.tiff`).
- Keep scientific figures minimal: no decorative title, no legend unless needed, and only the smallest set of annotations required to explain the main event.
- Final TG reports should embed generated raster or vector-displayable images directly in the Markdown body, not only list file paths.
- Final TG reports should avoid engineering-only wording such as parsed JSON, summary JSON, file index, or internal processing artifacts. Write for materials chemistry researchers, not for tool developers.

## Reference map

- Instrument context: `references/instrument-profile.md`
- Column mapping and parsing rules: `references/file-format.md`
- Canonical parsed schema: `references/data-structure.md`
- Interpretation rules and wording: `references/interpretation-guide.md`
- Publication figure rules: `references/visualization-guide.md`

## Limits

- Do not claim chemical identity from TG alone.
- Do not claim kinetics, activation energy, or component percentages unless directly computed and supported.
- Flag blocked cases clearly when the raw file cannot be read.
