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
    "figure.figsize": (6.8, 4.6),
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def load_trace(path: Path) -> tuple[dict, np.ndarray, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    x = np.asarray([row["temperature_c"] for row in payload["points"]], dtype=float)
    y = np.asarray([row["signal_au"] for row in payload["points"]], dtype=float)
    return payload, x, y


def load_summary(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def event_color(direction: str) -> str:
    return "#b91c1c" if direction == "positive" else "#1d4ed8"


def is_signal_inverted(metadata: dict) -> bool:
    return str(metadata.get("signal_inverted", "")).strip().lower() == "yes"


def display_direction(raw_direction: str, inverted: bool) -> str:
    if not inverted:
        return raw_direction
    return "positive" if raw_direction == "negative" else "negative"


def select_display_events(summary: dict, inverted: bool) -> list[dict]:
    if inverted:
        preferred = summary.get("negative_events", [])
        fallback = summary.get("positive_events", [])
    else:
        preferred = summary.get("positive_events", [])
        fallback = summary.get("negative_events", [])

    events = list(preferred[:3])
    if not events and summary.get("dominant_event"):
        events.append(summary["dominant_event"])
    if len(events) < 3:
        events.extend(fallback[: 3 - len(events)])
    return events[:3]


def plot(parsed_path: Path, summary_path: Path, output_stem: Path) -> None:
    parsed, x, y = load_trace(parsed_path)
    summary = load_summary(summary_path)
    metadata = parsed.get("metadata", {})
    mode = summary.get("analysis_mode", metadata.get("analysis_mode", "unknown"))
    inverted = is_signal_inverted(metadata)
    y_display = -y if inverted else y

    fig, ax = plt.subplots()
    ax.plot(x, y_display, color="#1f4e79", linewidth=1.2)
    ax.set_xlabel("Temperature (C)")
    ax.set_ylabel("Signal (a.u.)")
    ax.set_xlim(float(np.min(x)), float(np.max(x)))
    y_min = float(np.percentile(y_display, 1))
    y_max = float(np.percentile(y_display, 99))
    span = max(y_max - y_min, 1e-6)
    ax.set_ylim(y_min - span * 0.08, y_max + span * 0.15)
    ax.axhline(0.0, color="#9ca3af", linewidth=0.6, linestyle="--", alpha=0.8)

    events = select_display_events(summary, inverted)

    seen = set()
    deduped_events = []
    for event in events:
        shown_direction = display_direction(event["direction"], inverted)
        key = (shown_direction, round(float(event["peak_temperature_c"]), 2))
        if key in seen:
            continue
        seen.add(key)
        deduped_events.append({**event, "shown_direction": shown_direction})

    for event in deduped_events[:5]:
        px = float(event["peak_temperature_c"])
        py = -float(event["peak_signal_au"]) if inverted else float(event["peak_signal_au"])
        color = event_color(event["shown_direction"])
        ax.axvline(px, color=color, linestyle="--", linewidth=0.7, alpha=0.65)
        ax.scatter([px], [py], s=22, color=color, zorder=3)
        ax.text(px, py + span * 0.035, f"{px:.0f}", color=color, fontsize=7,
                rotation=90, ha="center", va="bottom")

    sample_label = metadata.get("sample_label", parsed_path.stem)
    suffix = " (display-flipped)" if inverted else ""
    ax.set_title(f"{mode} profile - {sample_label}{suffix}", fontsize=10)

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
