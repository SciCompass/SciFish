# Instrument Profile

## Working identity

- Skill target: generic photoluminescence spectroscopy archive
- Current grounded dataset: `datasets/generic-pl-analysis/4011_1704907518256_2401011361-H20.zip`
- Vendor hint from binary headers: likely Edinburgh Instruments export family
- Confirmed readable mode in this dataset: steady-state `Emission Scan`

## Observed metadata from the current archive

- Excitation wavelength (`Fixed/Offset`): `808.00 nm`
- Emission range: `900.00-1600.00 nm`
- Step size: `1.00 nm`
- Text-scan labels: `Em-Ex808`, `H2O-Em-Ex808`
- Source labels seen: `TCSPC Laser`, `Pulsed Laser`
- Detector labels seen: `NIR PMT`, `EXT RED / Ext red PMT`

## Intended use

This skill version is intended for:

- parsing PL text exports from zipped instrument packages
- extracting peak wavelength and relative intensity
- comparing multiple scans within one archive
- generating publication-style emission-spectrum figures

## Boundaries

- The readable `.txt` members support steady-state emission analysis.
- The `.FS` members should be treated as raw binary context only unless a dedicated decoder is added later.
- Transient PL conclusions are out of scope unless a readable decay export is provided.
