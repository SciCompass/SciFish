---
name: tpd-tpr-tpo-analysis
description: Analyze Micromeritics AutoChem II programmed chemisorption result files for TPD, TPR, or TPO experiments, extract signal-versus-temperature traces and key run metadata, and report peak temperatures, event counts, and interpretation limits with conservative wording.
allowed-tools: Bash, Read, Write, Edit
---

# TPD TPR TPO Analysis

Use this skill for programmed chemisorption files such as Micromeritics AutoChem II `.xls` report exports, zipped experiment bundles, or paired report files. Keep the analysis grounded in the exported trace and visible metadata. Do not claim absolute uptake, stoichiometry, site density, or a mechanism unless the file explicitly supports it.

## Inputs

- Raw TPD, TPR, or TPO files such as `.xls`, `.xlsx`, `.pdf`, `.smp`, or zipped bundles

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. If the user provides a zip bundle, extract it into `output/data/` and select the `.xls` report files as the primary parse targets.
3. Run `scripts/parse_autochem_report_xls.py` on each report file to extract metadata and the canonical `temperature_c` plus `signal_au` trace.
4. Run `scripts/summarize_programmed_chemisorption.py` on the parsed JSON to estimate the baseline window, dominant positive and negative events, and reportable peak temperatures.
5. If a figure is needed, run `scripts/plot_programmed_chemisorption.py`.
6. If a standardized Chinese report is needed, run `scripts/render_tpd_tpr_tpo_report.py` with the parsed JSON, summary JSON, generated PNG path, and output Markdown path.
7. Read `references/data-structure.md`, `references/interpretation-guide.md`, and `references/measurement-modes.md` before writing conclusions.
8. Report:
   - the confirmed analysis mode visible in the file
   - sample, run times, flow rate, sample mass, and signal inversion metadata when present
- the temperature window and point count
- the dominant signal events with temperature, direction, and relative prominence
- whether the profile is mostly low-, mid-, or high-temperature
- when a Chinese comprehensive report is requested, keep the section order fixed as `样品与数据概况` / `图谱结果` / `图谱图像` / `结构化分析`
- interpretation limits and missing calibration information

## Output rules

- Quote numeric values with units.
- Distinguish file-reported metadata from your own derived peak summary.
- Treat `signal_au` as relative detector response unless the file explicitly defines a calibrated quantity.
- If the report says no peaks are available, do not interpret that as proof of a flat trace.
- If the mode is TPR, TPD, or TPO, use the correct mode label throughout the answer.
- If only TPR has been validated for the current dataset, say so explicitly before making broader family claims.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and parser rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation rules and wording limits: `references/interpretation-guide.md`
- Mode-specific guardrails: `references/measurement-modes.md`
- Figure styling if plotting is added later: `references/visualization-guide.md`

## Limits

- Do not convert a detector signal peak into absolute uptake without calibration and integration rules.
- Do not claim oxidation state sequences, desorption species identities, or reaction pathways from one profile alone.
- Do not force peak assignments when the trace is broad, overlapping, or near the noise floor.
- Flag clearly when the current skill path is validated only for the AutoChem II TPR-style report layout.
