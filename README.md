<p align="center">
  <img src="docs/banner/scifish-hero.jpg" alt="SciFish — open-source AI-Agent skill library for materials characterization" />
</p>

<div align="center">

# ⌬ SciFish

### Open-source AI-Agent skill library for materials characterization

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-10-0d9488.svg)](#whats-in-v10)
[![Made for Claude Code](https://img.shields.io/badge/Made%20for-Claude%20Code-7c3aed.svg)](https://docs.claude.com/claude-code)
[![Codex CLI](https://img.shields.io/badge/Codex%20CLI-supported-1f2937.svg)](https://github.com/openai/codex)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](#install)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<br/>

[![Quick Start](https://img.shields.io/badge/Quick%20Start-→-0d9488?style=for-the-badge)](#install)
&nbsp;
[![10 Skills](https://img.shields.io/badge/10%20Skills-→-1f2937?style=for-the-badge)](#whats-in-v10)
&nbsp;
[![Landing Site](https://img.shields.io/badge/Landing%20Site-↗-7c3aed?style=for-the-badge)](https://scicompass.github.io/SciFish/)

</div>

---

SciFish is a curated set of **expert-validated, Agent-native Skills** that turn raw materials-characterization instrument exports into publication-ready figures and structured analysis reports. Drop a Skill into any Skill-aware AI Agent (Claude Code, Codex CLI) and the Agent gains the analytical judgment of a domain specialist for that instrument — with conservative wording, explicit observation/inference separation, and journal-grade visualization built in.

This is the open-source release of the Skill set that powers the [SciFish product](https://ai4s.shiyanjia.com/scifish/).

---

## What's in v1.0

Ten Skills, each iterated on real supplier exports and signed off by a domain expert:

| Skill | Domain |
|---|---|
| [`contact-angle-surface-tension-analysis`](skills/contact-angle-surface-tension-analysis/) | Goniometer / drop-shape analysis (wettability) |
| [`dls-analysis`](skills/dls-analysis/) | Dynamic light scattering (particle size) |
| [`ftir-analysis`](skills/ftir-analysis/) | Fourier-transform infrared spectroscopy |
| [`pl-analysis`](skills/pl-analysis/) | Photoluminescence spectroscopy |
| [`raman-analysis`](skills/raman-analysis/) | Raman spectroscopy (incl. multi-spectrum bundles) |
| [`tg-analysis`](skills/tg-analysis/) | Thermogravimetry (TGA) |
| [`tpd-tpr-tpo-analysis`](skills/tpd-tpr-tpo-analysis/) | Temperature-programmed desorption / reduction / oxidation |
| [`uv-vis-nir-drs-analysis`](skills/uv-vis-nir-drs-analysis/) | UV-Vis-NIR diffuse reflectance |
| [`xafs-analysis`](skills/xafs-analysis/) | X-ray absorption fine structure |
| [`xrf-analysis`](skills/xrf-analysis/) | X-ray fluorescence |

More instruments (BET, NMR, XPS, XRD, HRMS, EPR, ICP-OES/MS, GPC, DSC, TG-DSC, EA) are in our internal training pipeline and will land in subsequent releases as expert validation completes.

---

## What is a SciFish Skill

Every Skill is a self-contained directory:

```
<instrument>-analysis/
├── SKILL.md              # Agent-facing instructions: workflow + references map
├── VERSION.txt           # version + promotion timestamp
├── scripts/              # Python: parsing, peak/band detection, plotting, report rendering
├── references/           # Domain knowledge: file format, data structure, interpretation rules,
│                         #   peak/band tables, visualization conventions
└── assets/               # Report templates and other static resources
```

Three properties make these Skills different from "yet another analysis prompt":

1. **Self-contained & portable.** Drop any Skill directory into a Skill-aware Agent and it works — no project glue code.
2. **Workflow lives in `SKILL.md`; knowledge lives in `references/`.** Main instructions stay short and stable; tables and rules evolve independently and load on demand.
3. **Conservative by construction.** Every Skill enforces explicit separation between *observed* values and *inferred* assignments, blocks common over-claims (e.g. crystalline-phase identity from a single XRD scan; surface-free-energy from a sessile-drop screenshot), and emits journal-grade `.pdf` (vector) + `.png` (300 DPI) figure pairs.

---

## Install

See [`INSTALL.md`](INSTALL.md) for Claude Code and Codex CLI setups. The short version:

```bash
git clone https://github.com/SciCompass/SciFish
cp -R SciFish/skills/raman-analysis ~/.claude/skills/   # example: install just Raman
```

Each Skill expects standard scientific Python (`numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `lmfit`, ...). See [`INSTALL.md`](INSTALL.md) for a full dependency list.

---

## Use

Once the Skill is installed and your Agent recognizes it, the typical interaction is:

> "Analyze the Raman bundle at `~/data/sample-batch.zip` and write me a report."

The Agent loads `raman-analysis/SKILL.md`, follows the workflow there (parse the bundle → summarize per-spectrum → cross-replicate consistency check → plot → render Markdown report), and returns paths to the generated figures and report — all under `output/` in the current working directory.

---

## Roadmap

- **More Skills**: bring the remaining 11 instrument Skills out of internal validation and into this repo.
- **Examples**: ship redacted example datasets and expected outputs alongside each Skill so users can verify their setup end-to-end.
- **CI smoke tests**: lint and dry-run every Skill on every PR.
- **Multilingual reports**: Skills currently emit Chinese-default reports for several instruments; English templates are on the way.

---

## Contributing

We welcome contributions in any of these shapes:

- New instrument Skill (follow the four-folder structure above)
- New peak/band reference tables for existing Skills
- Edge-format support (vendor exports we haven't seen)
- Bug fixes and clearer interpretation rules

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the contribution workflow.

---

## How these Skills are made

Each Skill in this repo is the *output* of an internal training-and-evaluation harness called **SciSkillFactory**, which orchestrates expert-written Q/A test cases, automated Skill evaluation, and targeted Skill rewriting. The harness itself is not part of this open-source release; what we ship here is the *expert-signed-off* Skills it produces.

The collaboration principle behind every Skill is simple: **AI does the grunt work, the expert is the judge.** Parsing, plotting, and drafting are Agent jobs; "is this peak real?", "is this conclusion overclaimed?" are expert calls. This repo only contains Skills that have passed that bar.

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Acknowledgements

To every domain expert whose "no, redo it" turned a demo into a Skill that's safe to ship: thank you. This release exists because of your bar.
