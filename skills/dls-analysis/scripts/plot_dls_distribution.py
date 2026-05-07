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
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def load_points(path: Path) -> tuple[np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    x = np.asarray([row["size_nm"] for row in payload["points"]], dtype=float)
    y = np.asarray([row["intensity_pct"] for row in payload["points"]], dtype=float)
    return x, y


def load_peaks(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("top_peaks", [])


def plot(parsed_path: Path, summary_path: Path, output_stem: Path) -> None:
    x, y = load_points(parsed_path)
    peaks = load_peaks(summary_path)

    fig, ax = plt.subplots()
    ax.plot(x, y, color="#1f4e79", linewidth=1.2)
    ax.set_xscale("log")
    ax.set_xlabel("Particle size (nm)")
    ax.set_ylabel("Intensity distribution (%)")
    ax.set_xlim(float(x.min()), float(x.max()))
    ax.set_ylim(0.0, max(float(y.max()) * 1.15, 5.0))

    for peak in peaks[:3]:
        px = peak["size_nm"]
        py = peak["intensity_pct"]
        ax.axvline(px, color="#9ca3af", linestyle="--", linewidth=0.6)
        ax.text(px, py + max(float(y.max()) * 0.04, 0.6), f"{px:.0f} nm",
                fontsize=6.5, color="#7f1d1d", rotation=90, ha="center", va="bottom")

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".pdf"))
    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("output_stem")
    args = parser.parse_args()
    plot(Path(args.parsed_json), Path(args.summary_json), Path(args.output_stem))


if __name__ == "__main__":
    main()
