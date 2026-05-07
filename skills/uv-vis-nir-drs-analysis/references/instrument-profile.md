# Instrument Profile - Shimadzu UV-3600 Plus DRS

## Instrument family

- Vendor: Shimadzu
- Family: UV-Vis-NIR spectrophotometry / diffuse reflectance style analysis
- Model observed in the current batch: `UV-3600 Plus`
- Software observed: `LabSolutions UV-Vis 1.12`

## Typical use cases

- Compare UV and visible absorption strength across samples
- Inspect broad absorption maxima and edge-like transitions
- Screen whether samples remain strongly absorbing in the long-wavelength region
- Prepare publication-style overlay plots for sample comparison
- Perform reflectance-domain follow-up such as Kubelka-Munk or Tauc only after confirming the exported signal domain

## Current batch anchors

- Source archive: `datasets/shimadzu-uv-3600-plus-drs/<archive-id>.zip`
- Internal sample files: `example-1.txt`, `example-2.txt`, `example-3.txt`, `example-4.txt`
- Exported signal type: `吸收值`
- Numeric range actually present: `200.0-800.0 nm` at `1.0 nm` spacing
- Strongest sample in the batch: `example-2`, with a broad maximum near `423 nm`
- More red-shifted samples in the batch: `example-3` and `example-4`, with maxima near `459-462 nm`

## Interpretation constraints

- Although the instrument family supports UV-Vis-NIR diffuse reflectance work, the current numeric export spans only `200-800 nm`.
- The exported channel is absorbance-domain, not verified raw reflectance.
- Safe conclusions include maxima, relative ranking, baseline behavior, and cautious edge-like comments.
- Unsafe conclusions include exact composition, definitive band-gap values, and mechanistic claims without independent confirmation.
