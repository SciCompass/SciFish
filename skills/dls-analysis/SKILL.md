---
name: dls-analysis
description: Analyze DLS particle-size and zeta-potential exports. This production version is validated first against the confirmed Excel particle-size intensity distribution export and must explicitly report missing zeta fields instead of inferring them.
allowed-tools: Bash, Read, Write, Edit
---

# DLS Analysis

Use this skill for dynamic light scattering (DLS) and zeta-potential related exports. It supports the particle-size intensity-distribution `.xls` export format and must explicitly report missing zeta fields instead of inferring them.

## Inputs

- `.xls`, `.xlsx`, `.csv`, `.txt`
- files extracted from archives when needed

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. If the input matches the confirmed particle-size distribution `.xls` layout, run `scripts/parse_dls_xls.py` to create canonical JSON.
3. Run `scripts/summarize_dls.py` to extract the main peak, non-zero size window, long-tail behavior, and possible aggregation risk.
4. If a figure is needed, run `scripts/plot_dls_distribution.py`.
5. If a standardized Chinese report is needed, run `scripts/render_dls_report.py` with the parsed JSON, summary JSON, generated PNG path, and output Markdown path.
6. Before writing conclusions, read:
   - `references/data-structure.md`
   - `references/interpretation-guide.md`
   - `references/instrument-profile.md`
7. When generating the Chinese comprehensive report, keep the section order fixed:
   - `样品与数据概况`
   - `图谱结果`
   - `图谱图像`
   - `结构化分析`
8. If zeta-potential fields are absent from the raw export, state explicitly that:
   - the file supports particle-size intensity-distribution analysis only
   - the zeta section is blocked by missing data

## Output rules

- State the file type, worksheet, parsed columns, and units.
- Report the main peak size and its intensity value.
- State whether a large-particle tail or multi-peak behavior is present.
- Embed the generated figure with a local absolute image path so the Codex app can render it directly.
- Separate direct observations from interpretation.
- If the file only contains intensity distribution data, keep the conclusion at the intensity-distribution level and do not rewrite it as a volume or number distribution result.
- If zeta data is missing, say so clearly and stop at that boundary.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File layout and parsing rules: `references/file-format.md`
- Parsed and summary JSON schemas: `references/data-structure.md`
- Interpretation rules and language boundaries: `references/interpretation-guide.md`
- Figure conventions: `references/visualization-guide.md`

## Limits

- Do not invent Z-average, PDI, zeta potential, mobility, or conductivity values.
- Do not treat an intensity distribution as a particle-count distribution.
- Do not infer composition changes from a large-particle tail alone.
- If the file cannot be parsed, explain the blocker and the next useful step.
