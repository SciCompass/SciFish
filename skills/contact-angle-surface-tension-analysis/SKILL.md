---
name: contact-angle-surface-tension-analysis
description: Analyze contact-angle and surface-tension result bundles, extract visible droplet metrics from vendor screenshots, and report wettability conclusions with conservative wording.
allowed-tools: Bash, Read, Write, Edit
---

# Contact Angle / Surface Tension Analysis

Use this skill for goniometer or drop-shape analysis exports such as `.rar`, `.zip`, `.bmp`, `.png`, `.jpg`, or screenshot-heavy vendor bundles. Stay grounded in the visible evidence. Do not infer surface free energy, chemistry, or surface-tension values unless the export explicitly shows them.

## Inputs

- Raw screenshot bundles such as `.rar` or `.zip`
- Individual droplet images such as `.bmp`, `.png`, or `.jpg`
- Optional instrument notes under `instruments/generic-contact-angle-surface-tension-analysis/`
- Optional expert Q/A under `datasets/generic-contact-angle-surface-tension-analysis/`

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. Run `scripts/parse_contact_angle_bundle.py` on the raw archive or image directory to extract per-image values.
   - Per-image extraction must follow this JSON schema exactly: `{"left_ca": number|null, "right_ca": number|null, "average_ca": number|null, "unit": "degree"}`.
   - If an image shows only one angle value (for example `Angle: 31.65`), set `average_ca` to that value and keep `left_ca`/`right_ca` as `null`.
3. Run `scripts/summarize_contact_angle.py` on the parsed JSON to compute per-group/per-sample contact-angle statistics and wettability flags.
4. Run `scripts/generate_contact_angle_report_cn.py` to produce the fixed Chinese report output.
5. Read `references/data-structure.md`, `references/interpretation-guide.md`, and `references/measurement-modes.md` before writing conclusions.
6. Report:
   - what files were readable and how many distinct measurement groups were detected
   - left and right contact angle values for each group when visible
   - mean contact angle and spread across groups
   - when one order contains multiple samples, perform horizontal sample-to-sample comparison by mean contact angle
   - data quality and symmetry assessment based on `|Left CA - Right CA|`
   - threshold-based hysteresis indicator (`<= 2 deg` usually indicates better symmetry/baseline reliability)
   - whether each group is below or above the `90 deg` wettability boundary
   - whether any explicit surface-tension value is present in the export
   - limitations caused by screenshot-only or OCR-only evidence
   - fixed report output path under `output/datasets/.../*.analysis.report.cn.md`

## Output rules

- Quote numeric values with units.
- Label OCR-derived values as OCR-derived when image quality is poor.
- Separate observed values from interpretation.
- Use wording such as `suggests`, `is consistent with`, or `does not support`.
- If the bundle does not show surface-tension values explicitly, say so.
- Default report language is Chinese, using a material-chemistry-oriented structure (dataset overview, criteria/methods, results, cross-sample comparison, quality/uncertainty, and research conclusion).

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and OCR parsing rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation logic and wording limits: `references/interpretation-guide.md`
- Contact-angle versus surface-tension mode boundaries: `references/measurement-modes.md`
- Extraction schema and multimodal/OCR fallback rules: `references/extraction-spec.md`

## Limits

- Do not invent surface-tension values from sessile-drop screenshots.
- Do not infer surface free energy or adhesion work unless the export explicitly provides enough information.
- Do not claim superhydrophobicity unless the measured contact angle is clearly near or above `150 deg`.
- Do not treat one noisy OCR readout as authoritative when other screenshots in the same group disagree.
