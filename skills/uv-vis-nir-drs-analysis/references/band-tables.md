# Region Tables And Caution Anchors

This file is intentionally conservative. Use it for reporting ranges and screening language, not for definitive assignment.

## Wavelength region anchors

| Region | Approximate range (nm) | Safe reporting use |
| --- | --- | --- |
| UV | `200-400` | strong UV absorption, steep rise, edge-like behavior |
| Visible | `400-780` | visible absorption maxima, red or blue shift comparisons |
| Near-IR | `780-2500` | only mention when the measured data actually extend there |

## Current batch anchors

| Sample | Main maximum (nm) | Comment |
| --- | --- | --- |
| `example-1` | `420-424` | lowest peak amplitude in the batch |
| `example-2` | `423` | highest peak amplitude in the batch |
| `example-3` | `459` | clearly red-shifted versus `example-1/2` |
| `example-4` | `461-462` | clearly red-shifted and strongly absorbing |

## Kubelka-Munk and Tauc caution

- Kubelka-Munk analysis requires diffuse reflectance or a justified transform from reflectance-domain data.
- Tauc plots require a defensible transformed ordinate and an explicit transition assumption.
- If the export is only labeled as absorbance, report that limitation and stop short of numerical band-gap claims.
