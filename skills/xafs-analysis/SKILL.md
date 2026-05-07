---
name: xafs-analysis
description: Analyze XAFS datasets in E, k, and R spaces, extract E0 and quality indicators, report apparent shell peaks, and deliver a researcher-facing combined report with embedded figures and conservative interpretation text aligned with Athena/Larch practice.
allowed-tools: Bash, Read, Write, Edit
---

# XAFS Analysis

Use this skill for XAFS files and parsed payloads that contain E-space, k-space, and R-space arrays. Keep conclusions conservative and separate measured values from interpretation.

## Inputs

- Raw or parsed files under `datasets/generic-xafs-analysis/`
- Instrument and format references under `instruments/generic-xafs-analysis/`
- Expert-confirmed Q/A files under `datasets/generic-xafs-analysis/*.qa.md`

## Workflow

1. Read `references/file-format.md` to confirm key mapping for E/k/R spaces.
2. Run `python skills/xafs-analysis/scripts/xafs-analysis.py --data-dir datasets/generic-xafs-analysis --output-dir output/figures/generic-xafs-analysis` to process all samples in batch mode.
3. Keep default strict mode (Larch required) unless the user explicitly allows fallback with `--allow-numpy-fallback`.
4. Keep automatic E0 grouping enabled by default and only disable it when requested with `--no-auto-group`.
5. Use `--energy-threshold` only when the user asks to tune cross-sample grouping tolerance.
6. Read `references/data-structure.md` to ensure required fields are present for each sample.
7. Extract and report:
   - E-space E0 and low-to-high valence trend order
   - k-space RMS amplitude, high-k noise, and relative SNR quality label
   - R-space apparent peak positions with a maximum of three dominant peaks
8. Read `references/interpretation-guide.md` before drafting narrative text.
9. Generate analysis artifacts with explicit limitations:
   - edge-position-based valence trend is relative only
   - R-space peak positions are apparent values affected by phase shift
   - exact coordination distance requires EXAFS fitting
10. Ensure script output includes:
   - Stage 1/2/3/3b/4/5 figures in `.png`
   - text report `XAFS_Analysis_Report_{element}.txt` with auto-generated E/K/R interpretation paragraph
11. During input scan:
   - accept extensionless files when they are recognized as numeric text tables
   - print a filtered-file list with reasons for all skipped files
   - fail fast with non-zero exit when no valid sample file is detected
12. Preserve script-specific behaviors in summaries:
   - mention auto-detected element/edge and E0-based grouping result
   - mention automatic inverted-spectrum correction when triggered
   - when a reference foil exists, state that one shared energy offset was applied to the matched group
13. Apply report-delivery constraints for final handoff:
   - analyze every valid sample in the selected dataset folder
   - by default, deliver one combined report for the full batch; produce per-sample reports only when explicitly requested
   - treat the final Markdown report as the primary deliverable; script logs and intermediate files are support artifacts
14. Draft the final report in `output/reports/generic-xafs-analysis/` using `assets/report-template.md`. Write in a researcher-facing tone (suitable for materials-chemistry researchers as the primary reader); avoid developer/parser narration.
15. Embed key Stage 1/2/3/3b/4/5 figures directly in the final report body using Markdown image syntax with absolute local file paths.
16. Keep the report free of developer-facing wording (JSON dumps, parser/debug narration, script internals, file index lists).
17. Include interpretation limits and uncertainty boundaries in the conclusion section.

## Output rules

- Keep units explicit: eV, Å⁻¹, and Å.
- Use conservative wording such as `suggests`, `may indicate`, and `requires fitting confirmation`.
- If an input dimension is missing, report the missing part explicitly and avoid over-interpretation.
- Final delivery default is one combined Markdown report covering all valid samples.
- The report must include: sample/experiment context, test-result overview, E-space findings, k-space quality, R-space apparent peaks, scientific interpretation, and concise conclusion with boundaries.
- When completing the task, return the final report path, key figure paths, whether combined reporting was used, and a short Chinese finding summary unless the user requests another language.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and keys: `references/file-format.md`
- Parsed schema and fields: `references/data-structure.md`
- Interpretation boundaries: `references/interpretation-guide.md`
- Peak and quality heuristics: `references/peak-tables.md`
- Plot conventions: `references/visualization-guide.md`
