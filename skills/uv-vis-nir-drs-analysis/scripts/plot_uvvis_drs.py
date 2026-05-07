#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 600,
    "figure.figsize": (3.8, 2.8),
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("output_stem")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    summary_map = {item["sample_id"]: item for item in summary["samples"]}
    palette = ["#1d4ed8", "#d97706", "#059669", "#b91c1c", "#7c3aed"]

    fig, ax = plt.subplots()
    y_min = None
    y_max = None
    for index, sample in enumerate(parsed["samples"]):
        x = np.asarray([point["wavelength_nm"] for point in sample["points"]], dtype=float)
        y = np.asarray([point["absorbance"] for point in sample["points"]], dtype=float)
        color = palette[index % len(palette)]
        ax.plot(x, y, label=sample["sample_id"], color=color, linewidth=1.1)
        info = summary_map[sample["sample_id"]]
        px = info["peak_wavelength_nm"]
        py = info["peak_absorbance"]
        ax.scatter([px], [py], color=color, s=12, zorder=3)
        ax.text(px + 6.0, py + 0.01, f"{sample['sample_id']} {px:.0f} nm", color=color, fontsize=6.5)
        y_min = float(y.min()) if y_min is None else min(y_min, float(y.min()))
        y_max = float(y.max()) if y_max is None else max(y_max, float(y.max()))

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Absorbance (a.u.)")
    ax.set_xlim(200.0, 800.0)
    pad = max(0.02, (y_max - y_min) * 0.08)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper right")

    output_stem = Path(args.output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".pdf"))
    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
