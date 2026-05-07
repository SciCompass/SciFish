# File Format

## Archive layout

- Container: ZIP archive
- Root folder inside the archive: `<archive-id>/`
- Each sample is represented by:
  - one `.txt` export containing metadata plus a numeric table
  - one `.vspd` companion file

## Text export structure

- Encoding: `gb18030`
- The numeric table begins after the header row:
  - `波长(nm),吸收值`
- All metadata above the numeric table should be preserved as optional key-value pairs

## Canonical columns

| Observed label | Canonical name | Unit |
| --- | --- | --- |
| `波长(nm)` | `wavelength_nm` | `nm` |
| `吸收值` | `absorbance` | arbitrary absorbance-domain unit |

## Parsing rules

- Decode text with `gb18030`.
- Read numeric rows only after the column header line.
- Convert both columns to floats and drop malformed rows.
- Keep sample names from the internal filename stem such as `example-1`.
- Preserve the table order; in the current batch it is ascending from `200.0` to `800.0 nm`.
- Preserve method metadata such as scan speed, interval, light-source switching, and detector switching.

## Current batch facts

- Sample count: `4`
- Points per sample: `601`
- Range: `200.0-800.0 nm`
- Step: `1.0 nm`
- Signal type recorded in the export: `吸收值`

## Caution

- Do not silently reinterpret this export as `%R`, `F(R)`, or `Kubelka-Munk`.
- The `.vspd` files may contain richer vendor data, but the `.txt` files are the primary reproducible analysis target for this skill version.
