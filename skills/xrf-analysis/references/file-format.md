# File Format

## Supported inputs

- `.rar` bundles that unpack into one sample directory
- extracted directories containing `半定量.csv` and `谱图.csv`
- companion `.pdf` files for human review

## Encoding

- Default CSV decoding: `GB18030`
- Chinese headers are expected

## Semi-quantitative table structure

The file named like `*-半定量.csv` begins with metadata rows, a blank line, then a composition table.

Observed metadata keys:

- `文件名`
- `样品名`
- `分析日期`
- `样品类型`
- `组分类型`
- `匹配库`

Observed result columns:

| Raw label | Canonical name | Meaning |
| --- | --- | --- |
| `组分` | `component` | Oxide or reported component formula |
| `结果` | `result_mass_pct` | Semi-quantitative result |
| `单位` | `result_unit` | Usually `mass%` |
| `检测限` | `detection_limit` | Detection threshold |
| `元素谱线` | `element_line` | Reported elemental line, such as `Si-KA` |
| `强度` | `line_intensity` | Relative line intensity |
| `w/o 正常` | `normalized_weight_percent` | Vendor-specific normalized weight field |

## Scan trace structure

The file named like `*-谱图.csv` stores a single line-specific scan.

Observed columns:

- line label, shown in the first row only
- scan axis labeled `2 θ`
- relative intensity
- vendor-specific scan window label

## Parsing rules

- Parse the metadata block as key-value text.
- Detect the composition table from the `组分` header row.
- Convert result, detection-limit, and intensity fields to floats where possible.
- Parse the scan trace into ordered numeric points.
- Preserve the original line label even if later rows leave it blank.
- Treat the scan trace as XRF output, not diffraction data.
