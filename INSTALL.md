# Install

Three platforms are supported out of the box. Pick the one that matches your Agent.

## 1. Python dependencies (required for all platforms)

The Skills' scripts assume a standard scientific Python stack. Install once:

```bash
pip install numpy pandas scipy matplotlib seaborn lmfit pymatgen fabio h5py xraydb periodictable openpyxl chardet requests
```

Recommended Python: **3.8+**. A virtualenv (`python3 -m venv .venv && source .venv/bin/activate`) is encouraged.

Some Skills have additional optional dependencies (for example, `xafs-analysis` works best with [Larch](https://xraypy.github.io/xraylarch/)). Each Skill's `references/instrument-profile.md` calls these out explicitly when required.

## 2. Install the Skills you need

### Claude Code

Drop any Skill directory into your Claude Code skills folder:

```bash
git clone https://github.com/SciCompass/SciFish
cp -R SciFish/skills/raman-analysis ~/.claude/skills/
cp -R SciFish/skills/contact-angle-surface-tension-analysis ~/.claude/skills/
# ... repeat for any Skill you want
```

Restart Claude Code. The Skill is now invocable by name.

### Codex CLI

Codex CLI auto-loads Skills from its configured skill paths. Either symlink the cloned `skills/` directory into the path Codex watches, or copy individual Skill directories there. Consult `codex --help` for the exact location on your version.

## 3. Where outputs land

Every Skill writes its outputs under `output/` *relative to the current working directory*:

```
<your-cwd>/
└── output/
    ├── data/        # parsed/intermediate JSON
    ├── figures/     # journal-grade .pdf + .png pairs
    └── reports/     # final Markdown reports
```

If you want to redirect outputs elsewhere, every Python script under `skills/<name>/scripts/` accepts `--output-dir` (and equivalent flags). See each Skill's `SKILL.md` for the exact CLI surface.

## 4. Sanity check

A 30-second smoke test for any Skill:

```bash
cd /tmp/scifish-test && mkdir -p output
# Use any small example file matching the Skill's expected input format.
python ~/SciCompass/SciFish/skills/ftir-analysis/scripts/parse_ftir_csv.py path/to/your/file.csv
ls output/
```

If you see parsed JSON appear under `output/`, the Skill's environment is set up correctly.

## Troubleshooting

- **`ModuleNotFoundError`**: re-run the `pip install` command from step 1 inside your active environment.
- **Skill not detected by Agent**: confirm the directory was placed in the Agent's Skill path and that the Agent has been restarted.
- **`output/` not created**: most scripts create it automatically; if not, `mkdir -p output/{data,figures,reports}` first.
- **Encoding errors on Chinese supplier exports**: Skills already auto-detect via `chardet`; if a specific file fails, please open an Issue with a small reproducing example.
