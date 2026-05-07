---
name: uv-vis-nir-drs-analysis
description: Analyze UV-Vis/UV-Vis-NIR/DRS spectra from zip/xlsx/xls/csv/txt, run mode-aware Eg screening with Tauc candidates (direct and indirect), and produce publication-ready spectra plus Tauc figures with conservative interpretation boundaries.
allowed-tools: Bash, Read, Write, Edit
---

# UV-Vis-NIR DRS Analysis

Use this skill for UV-Vis / UV-Vis-NIR / DRS spectra exports (Shimadzu and generic tabular formats). The parser supports `.zip`, `.xlsx`, `.xls`, `.csv`, `.txt`, or a directory path. Keep conclusions in the original signal domain and run Eg only through the implemented rule thresholds.

## Inputs

- Raw result input as `.zip`, `.xlsx`, `.xls`, `.csv`, `.txt`, or a directory path containing these formats
- Optional instrument notes under `instruments/shimadzu-uv-3600-plus-drs/`
- Optional expert Q/A under `datasets/shimadzu-uv-3600-plus-drs/`

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. Run `scripts/parse_uvvis_drs_zip.py` with a single input path (zip/file/folder) to extract batch metadata and canonical `wavelength_nm` / `absorbance` series into a parsed JSON file.
3. Run `scripts/summarize_uvvis_drs.py` to generate per-sample summary metrics and `eg_assessment`.
   - Eg logic lives in `scripts/bloom_draw.py`; read `references/eg-algorithm-flow.md` before reporting any Eg number.
   - Signal mode is inferred from metadata (`吸收/abs` -> absorbance, `透过/trans/%T` -> transmittance, `反射/reflect/%R` -> reflectance).
   - Mode-aware energy conversion is strict: absorbance/transmittance use `1240/lambda`, reflectance uses `1024/lambda`.
   - Eg screening entry checks: point count, signal dynamic range, wavelength overlap, and valid transformed-point count.
   - Linear-region extraction uses Savitzky-Golay smoothing + recursive segmentation (`R_tol=0.995`, `min_segment_points=2`) with rolling-window fallback.
   - Candidate ranking uses decile scores from `delta_y` and slope `k`, then left-bound priority, and returns at most 2 candidates.
   - If Eg is skipped, preserve the rule-based skip reason and switch to `peak_position_and_shape_comparison`.
4. Read `references/data-structure.md`, `references/interpretation-guide.md`, `references/eg-algorithm-flow.md`, `references/band-tables.md`, and `references/visualization-guide.md` before writing conclusions.
5. Run `scripts/plot_uvvis_drs.py` to generate `.pdf` and `.png` spectra outputs in `output/figures/shimadzu-uv-3600-plus-drs/` using Nature/Science-style publication settings (single-column sizing, editable vector text, clean axis/tick styling, color-blind-safe palette).
   - Default plotting mode has **no inset**.
   - For manuscript highlight panels, optionally add an inset zoom window with:
     `--inset-range xmin,xmax --inset-anchor x0,y0,width,height`
6. Run `scripts/plot_tauc_uvvis_drs.py` to generate Tauc plots (`.pdf` + `.png`) for samples that pass Eg screening.
   - This step also writes a fixed Markdown conclusion file for each run:
     `output/reports/{dataset-folder}/{source-stem}.report.md`
   - Required section order in the generated report: `Results` -> `Discussion`.
   - Default delivery is one **combined** batch report covering all valid samples; only generate per-sample report when the user explicitly asks.
7. Use researcher-facing report delivery standard:
   - write evidence-first scientific narrative (not script/pipeline narration)
   - avoid developer artifacts (raw JSON dumps, parser/debug notes, internal implementation wording)
   - embed key figures directly in the report with absolute local image paths
   - include concise interpretation boundaries without overclaiming

## Output rules

- Quote numeric values with units.
- Separate observed spectral facts from tentative interpretation.
- Use conservative wording such as `consistent with`, `suggests`, `may reflect`, or `requires confirmation`.
- If the export is absorbance-domain rather than reflectance-domain, say that explicitly before discussing Kubelka-Munk or Tauc workflows.
- Always report whether Eg screening passed or failed before quoting any Eg value.
- If the file cannot be parsed, stop and explain what is missing or malformed.
- The final report must follow this mandatory section order:
  1) `Results`
  2) `Discussion`
- `Results` must include:
  - batch scope (`sample_count`, wavelength range, step, signal type)
  - ranked peak summary and at least one grouped comparison statement
  - primary optical parameters (peak/edge/Eg when available)
- `Discussion` must include:
  - what can be concluded from the current spectral domain
  - what cannot be concluded and why (metadata/calibration/thickness/transform limits)
- Do not add a separate `Data-Figure References` section in the report body.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and parsing rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation logic and wording limits: `references/interpretation-guide.md`
- Eg algorithm and thresholds from current scripts: `references/eg-algorithm-flow.md`
- Region anchors and band-gap caution: `references/band-tables.md`
- Figure conventions: `references/visualization-guide.md`

## Limits

- Do not convert absorbance-domain exports into reflectance claims without explicit evidence.
- Do not report a numerical band gap when `eg_assessment.meaningful_for_eg` is false.
- Do not identify a material or mechanism from one broad visible maximum alone.
- Do not overinterpret small slope changes at the scan boundaries.
