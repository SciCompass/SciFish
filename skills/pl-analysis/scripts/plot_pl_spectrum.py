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


def select_peaks_for_plot(peaks: list[dict], max_labels: int = 2, min_spacing_nm: float = 35.0) -> list[dict]:
    chosen: list[dict] = []
    for peak in peaks:
        px = float(peak["emission_wavelength_nm"])
        if any(abs(px - float(existing["emission_wavelength_nm"])) < min_spacing_nm for existing in chosen):
            continue
        chosen.append(peak)
        if len(chosen) >= max_labels:
            break
    return chosen


def ensure_strongest_peak_in_plot(peaks: list[dict], strongest_peak_nm: float) -> list[dict]:
    if any(abs(float(peak["emission_wavelength_nm"]) - strongest_peak_nm) < 1.5 for peak in peaks):
        return peaks
    strongest_peak = {
        "emission_wavelength_nm": strongest_peak_nm,
        "counts": 0.0,
    }
    return [strongest_peak] + peaks[:-1] if peaks else [strongest_peak]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("output_stem")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    summary_by_name = {scan["scan_name"]: scan for scan in summary["scans"]}
    colors = ["#1f2937", "#0f766e", "#b45309", "#7c3aed"]

    fig, ax = plt.subplots()
    global_min = None
    global_max = None
    q05_values: list[float] = []
    q995_values: list[float] = []
    curves: list[tuple[dict, np.ndarray, np.ndarray, str]] = []

    for idx, scan in enumerate(parsed["scans"]):
        x = np.asarray([row["emission_wavelength_nm"] for row in scan["points"]], dtype=float)
        y = np.asarray([row["counts"] for row in scan["points"]], dtype=float)
        color = colors[idx % len(colors)]
        curves.append((scan, x, y, color))
        global_min = float(np.min(y)) if global_min is None else min(global_min, float(np.min(y)))
        global_max = float(np.max(y)) if global_max is None else max(global_max, float(np.max(y)))
        q05_values.append(float(np.percentile(y, 5)))
        q995_values.append(float(np.percentile(y, 99.5)))

    y_floor = min(q05_values) if q05_values else (global_min if global_min is not None else 0.0)
    y_ceiling = max(q995_values) if q995_values else (global_max if global_max is not None else 1.0)
    signal_span = max(y_ceiling - y_floor, 1.0)
    y_min = y_floor - signal_span * 0.08
    y_max = y_ceiling + signal_span * 0.12

    for idx, (scan, x, y, color) in enumerate(curves):
        ax.plot(x, y, color=color, linewidth=1.25, label=scan["scan_name"])
        scan_summary = summary_by_name[scan["scan_name"]]
        peaks = select_peaks_for_plot(scan_summary["dominant_peaks"], max_labels=2)
        peaks = ensure_strongest_peak_in_plot(peaks, float(scan_summary["strongest_peak_nm"]))
        label_offset = signal_span * (0.035 + idx * 0.03)
        for peak in peaks:
            px = float(peak["emission_wavelength_nm"])
            py = float(peak["counts"]) if float(peak["counts"]) != 0.0 else float(np.interp(px, x, y))
            ax.axvline(px, color=color, linestyle="--", linewidth=0.45, alpha=0.45)
            ax.scatter([px], [py], s=14, color=color, edgecolors="white", linewidths=0.35, zorder=3)
            text_y = min(py + label_offset, y_max - signal_span * 0.03)
            ax.text(
                px,
                text_y,
                f"{px:.0f}",
                rotation=90,
                fontsize=6.5,
                color=color,
                ha="center",
                va="bottom",
            )

    x0 = np.asarray([row["emission_wavelength_nm"] for row in parsed["scans"][0]["points"]], dtype=float)
    ax.set_xlabel("Emission wavelength (nm)")
    ax.set_ylabel("Counts")
    ax.set_xlim(float(x0.min()), float(x0.max()))
    ax.set_ylim(y_min, y_max)
    ax.legend(frameon=False, fontsize=7, loc="upper left")

    output_stem = Path(args.output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".pdf"))
    fig.savefig(output_stem.with_suffix(".png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
