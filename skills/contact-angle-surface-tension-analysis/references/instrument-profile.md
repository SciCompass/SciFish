# Instrument Profile

## Scope

This skill targets contact-angle and surface-tension result bundles from drop-shape analysis instruments. The observed intake is a screenshot-heavy archive rather than a structured vendor workbook.

## Current observed intake

- Source file: `datasets/generic-contact-angle-surface-tension-analysis/705_1704694767540_2401010773.rar`
- Screenshot labels visible: `CA left` and `CA right`
- Measurement mode visible in the sample: sessile-drop contact angle
- Surface-tension values explicitly visible in the sample: none

## Practical questions this skill should answer

- What are the left and right contact angles for each detected droplet group?
- What is the mean contact angle and spread across groups?
- Are the left and right fits symmetric enough for a stable reading?
- Does the current export contain true surface-tension values or only contact-angle screenshots?

## Boundaries

- This skill may discuss surface tension only when the export visibly includes a named surface-tension metric.
- This skill should not infer material chemistry, surface free energy, or adhesion work from screenshot contact angles alone.
