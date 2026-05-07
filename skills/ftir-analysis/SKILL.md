---
name: ftir-analysis
description: Analyze FTIR spectra, extract dominant absorption bands, generate publication-ready spectra plots, and provide conservative functional-group screening grounded in the measured data.
allowed-tools: Bash, Read, Write, Edit
---

# FTIR Analysis

Use this skill for FTIR result files such as `.csv`, `.txt`, `.xls`, or `.xlsx`. Stay grounded in the measured spectrum. Do not claim exact compound identity, phase identity, or formulation unless the data and metadata directly support it.

## Inputs

- Raw FTIR files such as `.csv`, `.txt`, `.xls`, `.xlsx`

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. Run `scripts/parse_ftir_csv.py` to extract the canonical `wavenumber_cm1` / `signal` series and basic metadata.
3. Run `scripts/summarize_ftir.py` on the parsed JSON to detect the main absorption-like bands and broad-band flags.
4. Read `references/data-structure.md`, `references/interpretation-guide.md`, `references/band-tables.md`, and `references/visualization-guide.md` before writing conclusions.
5. Run `scripts/plot_spectrum.py` to generate `.pdf` and `.png` outputs in `output/figures/`.
6. Report:
   - available metadata, columns, and units
   - full spectral range and axis orientation
   - the strongest absorption-like band position and intensity surrogate
   - main bands in the functional-group region and fingerprint region
   - whether broad O-H / N-H like or H-O-H related features are present
   - whether a clear strong carbonyl band is absent or present
   - key missing metadata and interpretation limits

## Output rules

- Quote numeric values with units.
- Separate observed bands from tentative assignments.
- Use conservative wording such as `consistent with`, `may indicate`, or `tentatively suggests`.
- If the signal channel is unlabeled, say so explicitly and avoid claiming absolute absorbance or transmittance values.
- If the file cannot be parsed, stop and explain what is missing or malformed.

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and parsing rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation logic and wording limits: `references/interpretation-guide.md`
- Common FTIR band anchors: `references/band-tables.md`
- Figure conventions: `references/visualization-guide.md`

## Limits

- Do not identify a specific compound from one FTIR spectrum alone.
- Do not convert unlabeled intensity values into absorbance or transmittance claims.
- Do not overassign weak shoulders or noisy endpoints as definitive bands.
- Do not state phase fraction, purity, or reaction completion without orthogonal evidence.
