# Data Structure

## Parsed JSON schema

`scripts/parse_uvvis_drs_zip.py` writes a batch-level JSON object with:

- `source_file`: input path (zip, file, or directory)
- `archive_entries`: all discovered source entries (archive entries, file names, or file-relative paths)
- `batch_metadata`: shared method metadata when available
- `samples`: list of sample records

Each sample record contains:

- `sample_id`
- `source_entry`
- `metadata`
- `summary`
- `points`

Each point contains:

- `index`
- `wavelength_nm`
- `absorbance`

## Summary JSON schema

`scripts/summarize_uvvis_drs.py` writes:

- `source_file`
- `sample_count`
- `batch_ranking_by_peak_absorbance`
- `samples`

Each summarized sample contains:

- `sample_id`
- `wavelength_range_nm`
- `step_nm`
- `point_count`
- `peak_wavelength_nm`
- `peak_absorbance`
- `mean_absorbance_200_300_nm`
- `mean_absorbance_350_500_nm`
- `mean_absorbance_700_800_nm`
- `edge_marker_nm`
- `edge_marker_derivative`
- `eg_assessment`
- `interpretation_path`

`eg_assessment` contains:

- `signal_mode`: inferred mode (`absorbance`, `transmittance`, `reflectance`, `unknown`)
- `signal_label`: raw signal label from metadata
- `should_calculate_eg`: whether the sample passes basic pre-checks and enters Eg screening
- `meaningful_for_eg`: whether at least one linear Tauc candidate passes rule thresholds
- `decision`: `compute_eg` or `peak_only`
- `reason`: explanation for Eg acceptance or skip
- `selected_direct_eg_ev`
- `selected_indirect_eg_ev`
- `direct_candidates_ev`: top direct-gap candidates with slope/intercept/r2/segment range
- `indirect_candidates_ev`: top indirect-gap candidates with slope/intercept/r2/segment range

Each candidate may also include:

- `segment_points`
- `score_dy`
- `score_k`
- `score_total`

## Fixed report output

Each completed analysis run also writes a Markdown conclusion file with the required sections:

- `Results`
- `Discussion`

Default path pattern:

- `output/reports/{dataset-folder}/{source-stem}.report.md`

## Current batch interpretation anchor

- `example-2` has the strongest visible-region maximum
- `example-3` and `example-4` are shifted to longer wavelengths than `example-1` and `example-2`
- All samples show lower absorbance in `700-800 nm` than around their visible maxima
