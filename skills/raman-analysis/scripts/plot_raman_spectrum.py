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
    "figure.figsize": (3.5, 2.6),
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.minor.width": 0.5,
    "ytick.minor.width": 0.5,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "lines.linewidth": 1.0,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def load_parsed(path: Path) -> tuple[np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    x = np.asarray([row["raman_shift_cm^-1"] for row in payload["points"]], dtype=float)
    y = np.asarray([row["intensity_au"] for row in payload["points"]], dtype=float)
    return x, y


def load_summary(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["dominant_bands"]


def select_bands_for_plot(bands: list[dict], max_count: int = 5) -> list[dict]:
    selected = bands[:max_count]
    if not any(2500.0 <= float(band["raman_shift_cm^-1"]) <= 3200.0 for band in selected):
        high_shift_band = next(
            (band for band in bands if 2500.0 <= float(band["raman_shift_cm^-1"]) <= 3200.0),
            None,
        )
        if high_shift_band is not None:
            selected = selected + [high_shift_band]
    return selected


def plot_raman_spectrum(parsed_path: Path, summary_path: Path, output_stem: Path) -> None:
    x, y = load_parsed(parsed_path)
    bands = select_bands_for_plot(load_summary(summary_path), max_count=5)

    fig, ax = plt.subplots()
    ax.plot(x, y, color="#1f2937", linewidth=1.1)
    ax.set_xlabel("Raman shift (cm^-1)")
    ax.set_ylabel("Intensity (a.u.)")
    ax.set_xlim(float(x.min()), float(x.max()))
    q01 = float(np.percentile(y, 1))
    q05 = float(np.percentile(y, 5))
    q99 = float(np.percentile(y, 99))
    q995 = float(np.percentile(y, 99.5))
    span = max(q99 - q05, 1e-6)
    y_min = min(float(np.min(y)), q01 - span * 0.08)
    y_max = q995 + span * 0.18
    if float(np.max(y)) <= y_max * 1.25:
        y_max = max(y_max, float(np.max(y)) * 1.05)
    ax.set_ylim(y_min, y_max)
    label_offset = (y_max - y_min) * 0.025

    for band in bands:
        px = band["raman_shift_cm^-1"]
        py = band["intensity_au"]
        ax.axvline(px, color="#9ca3af", linestyle="--", linewidth=0.5, alpha=0.7)
        ax.scatter([px], [py], s=12, color="#b91c1c", zorder=3, edgecolors="white", linewidths=0.3)
        label_y = min(py + label_offset, y_max - label_offset * 0.6)
        ax.text(px, label_y, f"{px:.0f}", rotation=90, fontsize=6.5, color="#7f1d1d", ha="center", va="bottom")

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

    plot_raman_spectrum(Path(args.parsed_json), Path(args.summary_json), Path(args.output_stem))


if __name__ == "__main__":
    main()
