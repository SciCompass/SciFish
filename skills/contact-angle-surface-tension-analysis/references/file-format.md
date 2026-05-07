# File Format Guide

## Accepted inputs

- `.rar` and `.zip` bundles containing screenshot images
- `.bmp`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`
- Image directories extracted from a vendor archive

## Confirmed export pattern for `705_1704694767540_2401010773.rar`

- Top folder: `2401010773/`
- Main files: `1.bmp` to `5.bmp`
- Related screenshots: `1-1.bmp` to `5-5.bmp`
- Duplicate subfolder exists: `2401010773/新建文件夹/`
- OCR-visible overlays use `CA left` and `CA right`

## Canonical fields

- Per-image fields:
  - `sample_id`
  - `group_id`
  - `left_ca`
  - `right_ca`
  - `average_ca`
  - `unit`
  - `surface_tension_mn_m`
  - `ocr_text`
- Group-level fields:
  - `left_contact_angle_deg`
  - `right_contact_angle_deg`
  - `mean_contact_angle_deg`
  - `left_right_difference_deg`

## Heuristics

- Extract archives before OCR.
- Deduplicate repeated files by content hash, not by file name.
- Convert bitmap screenshots to normalized PNG before running OCR.
- Group screenshots by numeric stem prefix, for example `4` for `4.bmp` and `4-2.bmp`.
- Use the group-level median rather than a single readout when OCR varies across screenshots in one group.
- If only a single angle field is visible (`Angle` / `Angel`), map it to `average_ca`.

## Failure modes

- OCR may miss one side of the angle overlay on a crowded or low-contrast image.
- A screenshot bundle may not contain surface-tension values at all.
- Duplicate folders should not be counted twice in the final statistics.
