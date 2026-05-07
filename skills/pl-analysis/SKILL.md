---
name: pl-analysis
description: Analyze steady-state photoluminescence emission exports, compare scans inside a PL archive, generate publication-ready spectra, and report conservative conclusions grounded in the measured signal.
allowed-tools: Bash, Read, Write, Edit
---

# PL Analysis

Use this skill for steady-state photoluminescence result files such as `.zip` packages containing PL `.txt` exports. It should not invent transient lifetime results when the input does not include readable decay traces.

## Inputs

- Raw PL files such as `.zip` packages containing `.txt` and `.FS` members

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar PL export.
2. Run `scripts/parse_pl_zip.py` to extract metadata and canonical `emission_wavelength_nm` / `counts` series from each readable `.txt` scan in the archive.
3. Run `scripts/summarize_pl.py` on the parsed JSON to detect dominant emission maxima, integrated positive signal, and scan-to-scan intensity ratios.
4. Read `references/data-structure.md`, `references/interpretation-guide.md`, and `references/peak-notes.md` before writing conclusions.
5. Run `scripts/plot_pl_spectrum.py` to generate `.pdf` and `.png` outputs in `output/figures/`.
6. Run `scripts/render_pl_report.py` to generate a standardized Chinese comprehensive analysis report in Markdown using the parsed JSON, summary JSON, and figure paths.
7. Report:
   - available scan labels, acquisition metadata, and whether the archive contains steady-state or transient-readable data
   - wavelength range, point count, and step size for each scan
   - strongest emission maximum for each scan
   - top secondary maxima when they are separated from noise
   - relative intensity differences between scans in the same archive
   - any missing metadata that materially limits interpretation
   - a Chinese comprehensive analysis report that embeds the figure and follows a fixed section order

## Output rules

- Quote numeric values with units.
- Distinguish observed emission maxima from inferred origin assignments.
- Use conservative wording such as `consistent with`, `suggests`, or `may indicate`.
- If transient decay data are not present in a readable form, say so explicitly.
- If the file cannot be parsed, stop and explain which member or structure is unsupported.
- The Markdown report must embed the spectrum image and keep a standardized section order.
- The Markdown report should stay fact-first and keep mechanism-level language conservative.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and parsing rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation logic and wording limits: `references/interpretation-guide.md`
- PL-specific feature notes: `references/peak-notes.md`
- Figure conventions: `references/visualization-guide.md`

## Limits

- Do not claim lifetime constants, multiexponential components, or quenching mechanisms without readable transient data.
- Do not convert raw counts into absolute photoluminescence quantum yield.
- Do not assign a chemical species or defect center from peak position alone.
- Do not treat isolated noise spikes as true emission peaks.
