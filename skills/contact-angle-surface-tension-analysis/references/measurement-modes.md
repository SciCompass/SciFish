# Measurement Modes

## Sessile-drop contact angle

- Typical visible fields: `CA left`, `CA right`, baseline, droplet contour
- Main output: static contact angle in `deg`
- Typical interpretation: wettability or hydrophilic/hydrophobic screening
- Limits: does not directly provide surface tension or surface free energy

## Pendant-drop surface tension

- Typical visible fields: surface tension, interfacial tension, `IFT`, `SFT`, or `gamma`
- Main output: surface tension in `mN/m`
- Typical interpretation: liquid-air or liquid-liquid interfacial behavior
- Limits: should not be inferred from sessile-drop screenshots

## Rule for this skill

- First decide which mode is explicitly visible in the export.
- If only contact-angle overlays are present, keep the report in contact-angle mode.
- Mention surface tension only when the file explicitly shows a surface-tension metric.
