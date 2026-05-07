# File Format Guide

## Confirmed export pattern

- File type: Excel 97-2003 `.xls`
- Worksheet layout: `Sheet1` contains the useful data; `Sheet2` and `Sheet3` are empty in the current sample set
- Header rows:
  - row 1: record label
  - row 2: column titles
  - row 3 onward: numeric data

## Confirmed columns

- `Size classes (nm)`
- `Intensity Distribution Data (%)`

## Parsing rules

1. Read `Sheet1`.
2. Skip the first two rows.
3. Use the first two columns and rename them to:
   - `size_nm`
   - `intensity_pct`
4. Coerce both columns to numeric values.
5. Drop empty rows.

## Practical checks

- The current samples typically contain about `69` valid size points.
- The size axis expands on an approximately logarithmic spacing.
- The second column is a percentage-style intensity signal and many bins can be `0`.

## Missing-field handling

Do not assume the following fields exist unless they are actually present:

- `zeta_potential_mv`
- `mobility`
- `conductivity`
- `z_average_nm`
- `pdi`

Treat these as optional inputs. If they are absent, report the missing data explicitly.
