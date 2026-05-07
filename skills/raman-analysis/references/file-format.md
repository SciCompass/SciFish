# File Format Guide

## Accepted inputs

- `.txt`
- `.csv`
- tab-delimited text exports
- `.rar` bundles containing Raman text exports, note files, and preview images
- `.zip` bundles containing Raman text exports, note files, and preview images

## Confirmed export pattern for `1-1.txt`

- The file contains a two-column numeric series with no metadata header.
- Column 1 is the Raman shift in `cm^-1`.
- Column 2 is the measured intensity in arbitrary units.
- The observed spectrum spans about `400.097-3999.780 cm^-1`.

## Canonical columns

- `raman_shift_cm^-1`
- `intensity_au`

## Confirmed archive pattern for `5347_1774252661325_26031899879.rar`

- The archive expands to a bundle root with two sample folders:
  - `1-In2S3/`
  - `2-La-doped In2S3/`
- Each sample folder contains multiple Raman text exports such as `1-1.txt` or `2-3.txt`.
- The bundle also contains preview images (`.jpg`) and a note file `备注.txt`.
- `备注.txt` contains the operator note `样品在532激发下有荧光`, which must be preserved as interpretation context.
- The Raman text exports remain simple two-column numeric tables and can be parsed with the same canonical text parser used for single-file inputs.

## Heuristics

- Treat the first stable two-column numeric block as the spectrum data block.
- Drop blank rows.
- Sort data by `raman_shift_cm^-1` after parsing.
- If duplicate shifts exist, average the intensity values.
- Keep metadata empty when the file provides no header rows.
- When walking archive bundles, attempt numeric parsing only on `.txt`, `.csv`, or `.tsv` members; keep non-numeric text files as notes rather than forcing them through the spectrum parser.
- Preserve sample-folder names because they typically encode composition or treatment labels.

## Parser expectations

The single-spectrum parser should output:

- `source_file`
- `metadata`
- `columns`
- `points`
- `summary`

The summary block should include:

- total point count
- shift range
- median step size
- min and max intensity

The bundle parser should additionally output:

- `extracted_dir`
- `note_files`
- `sample_groups`
- per-spectrum `parsed_json` paths for downstream summarization
