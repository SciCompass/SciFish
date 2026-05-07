# Instrument Profile

This working skill targets programmed chemisorption exports from Micromeritics AutoChem II 2920 style reports.

## Confirmed environment

- Vendor software banner: `MicroActive for AutoChem II 2920 Version 6.01`
- Confirmed report style: one Excel report page with metadata plus three side-by-side numeric panels
- Confirmed current mode from real files: `Temperature Programmed Reduction`
- Confirmed current sample label in the intake bundle: `h2-tpr`

## Supported use

- Extract the report metadata
- Recover the `signal_au` versus `temperature_c` curve
- Summarize dominant low-, mid-, and high-temperature events
- Compare runs by event count and dominant peak temperature

## Unsupported use

- Absolute chemisorption quantification without calibration
- Mechanistic reduction or oxidation assignment from the profile alone
- Guaranteed compatibility with all AutoChem report variants without a real sample file
