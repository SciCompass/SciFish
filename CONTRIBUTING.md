# Contributing to SciFish

Thanks for considering a contribution. SciFish is built on the principle that **the domain expert is the judge** — every Skill in `main` has been signed off by someone who actually runs the instrument. We try to keep that bar.

## Where contributions land

- **`skills/<existing-skill>/references/*-tables.md`** — peak / band / binding-energy / characteristic-temperature tables. The lowest-friction contribution and very welcome.
- **`skills/<existing-skill>/references/file-format.md`** — vendor-export edge cases (encoding, layout variants, broken headers). If you have a real export the current parser fails on, open an Issue with a small redacted reproducer.
- **`skills/<existing-skill>/scripts/`** — parser/plot/report bug fixes. Keep changes minimal and behavior-preserving for existing test cases.
- **`skills/<new-instrument>-analysis/`** — entirely new instrument Skills. Please open an Issue describing the instrument and your domain background *before* sending a large PR; we'll discuss scope and whether the new Skill should ship with a paired `references/visualization-guide.md`.

## What we generally do not accept

- Generative-AI-only assignments without measured-data evidence (e.g. "this peak is X" with no spectrum).
- Removal of conservative wording rules (`consistent with`, `may suggest`, etc.) — those are load-bearing.
- "Helpful" defaults that hide failure modes (silent fallbacks that turn parse errors into empty outputs).

## PR checklist

Before opening a PR, please confirm:

- [ ] The Skill still parses every file in your local sample set without crashing.
- [ ] If you changed wording rules in `SKILL.md` or `references/interpretation-guide.md`, you've checked that the new wording does not loosen the *Limits* section.
- [ ] If you added a new dependency, you've added it to `INSTALL.md`.
- [ ] You haven't introduced absolute paths or machine-specific paths (`/Users/...`, `/home/...`).
- [ ] Outputs land under `output/` (not `workspace/`, not absolute paths).
- [ ] If you touched scripts, the script's `--help` still describes its flags accurately.

## Reviewer expectation

PR review is done by someone with domain familiarity for the affected instrument. Expect questions like *"why is this peak considered dominant when it's only 1.2× background?"* That is the bar — please don't take it personally.

## Reporting issues

When opening an Issue:

- Describe the **instrument and vendor export format** (e.g. "Bruker D8 `.raw` exported as ASCII via DIFFRAC.SUITE 2024").
- Attach a **small redacted sample** if licensing allows.
- Include the **exact error / wrong-output line** from the Skill's run, not a paraphrase.

## Code of conduct

Be kind. Be specific. Cite measurements. We don't need a longer document than that.
