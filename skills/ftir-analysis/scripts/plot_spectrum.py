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
    "figure.figsize": (3.6, 2.7),
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


def load_parsed(path: Path) -> tuple[np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    x = np.asarray([row["wavenumber_cm1"] for row in payload["points"]], dtype=float)
    y = np.asarray([row["signal"] for row in payload["points"]], dtype=float)
    return x, y


def load_summary(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bands = payload["main_bands"]
    selected = bands[:5]

    # Ensure the functional-group region remains visible even when fingerprint
    # peaks dominate the prominence ranking.
    if not any(float(band["wavenumber_cm1"]) >= 2500.0 for band in selected):
        functional_group_band = next(
            (band for band in bands if float(band["wavenumber_cm1"]) >= 2500.0),
            None,
        )
        if functional_group_band is not None:
            selected = selected + [functional_group_band]

    return selected


def plot_spectrum(parsed_path: Path, summary_path: Path, output_stem: Path) -> None:
    x, y = load_parsed(parsed_path)
    bands = load_summary(summary_path)

    fig, ax = plt.subplots()
    ax.plot(x, y, color="#1d3557", linewidth=1.1)
    ax.set_xlabel("Wavenumber (cm^-1)")
    ax.set_ylabel("Signal (a.u. or %)")
    ax.set_xlim(float(x.max()), float(x.min()))

    # Use robust percentiles to avoid endpoint artifacts flattening visible peaks.
    p1, p99 = np.percentile(y, [1, 99])
    y_low = float(min(p1, min((band["signal"] for band in bands), default=p1)))
    y_high = float(max(p99, max((band["signal"] for band in bands), default=p99)))
    span = max(y_high - y_low, 1e-6)
    pad = span * 0.12
    ax.set_ylim(y_low - pad, y_high + pad)

    for band in bands:
        px = band["wavenumber_cm1"]
        py = band["signal"]
        ax.axvline(px, color="#9ca3af", linestyle="--", linewidth=0.5, alpha=0.8)
        ax.scatter([px], [py], s=14, color="#7f1d1d", zorder=3)
        ax.text(px, py + pad * 0.20, f"{px:.0f}", rotation=90, fontsize=6.5,
                color="#7f1d1d", ha="center", va="bottom")

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
    plot_spectrum(Path(args.parsed_json), Path(args.summary_json), Path(args.output_stem))


if __name__ == "__main__":
    main()
