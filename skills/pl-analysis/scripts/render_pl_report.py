#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt_number(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def fmt_peak_list(peaks: list[dict], limit: int = 4) -> list[str]:
    rows: list[str] = []
    for peak in peaks[:limit]:
        rows.append(
            f"- `{peak['emission_wavelength_nm']:.0f} nm`，counts=`{peak['counts']:.4f}`，"
            f"相对强度=`{peak['relative_intensity_pct']:.2f}%`，"
            f"prominence=`{peak['prominence_counts']:.4f}`"
        )
    return rows


def render_report(parsed: dict, summary: dict, figure_png: str, figure_pdf: str) -> str:
    figure_png_abs = str(Path(figure_png).resolve()).replace("\\", "/")
    lines: list[str] = []
    lines.append("# PL 综合分析报告（中文版）")
    lines.append("")
    lines.append("## 1. 样品与数据概况")
    lines.append(f"- 样品文件：`{parsed['source_file']}`")
    lines.append(f"- 可读扫描数：`{summary['scan_count']}`")
    lines.append(f"- 稳态发光数据：`{str(summary['steady_state_detected']).lower()}`")
    lines.append(f"- 可读瞬态衰减数据：`{str(summary['transient_decay_detected']).lower()}`")
    for scan_summary in summary["scans"]:
        parsed_scan = {scan["scan_name"]: scan for scan in parsed["scans"]}[scan_summary["scan_name"]]
        scan_info = parsed_scan["summary"]
        lines.append(
            f"- `{scan_summary['scan_name']}`：波长范围 "
            f"`{scan_info['wavelength_range_nm'][0]:.0f}-{scan_info['wavelength_range_nm'][1]:.0f} nm`，"
            f"最强峰 `{scan_summary['strongest_peak_nm']:.0f} nm`，最大计数 `{fmt_number(scan_summary['max_counts'])}`"
        )
    lines.append("")
    lines.append("## 2. 图谱结果")
    lines.append(f"- PNG 图谱：`{figure_png}`")
    lines.append(f"- PDF 图谱：`{figure_pdf}`")
    lines.append("")
    lines.append("## 3. 图谱图像")
    lines.append(f"![PL 图谱]({figure_png_abs})")
    lines.append("")
    lines.append("## 4. 结构化分析")

    parsed_scans = {scan["scan_name"]: scan for scan in parsed["scans"]}
    lines.append("### 4.1 单条扫描结果")
    for scan_summary in summary["scans"]:
        parsed_scan = parsed_scans[scan_summary["scan_name"]]
        scan_meta = parsed_scan["metadata"]
        scan_info = parsed_scan["summary"]
        lines.append(f"- `{scan_summary['scan_name']}`：")
        lines.append(
            f"  波长范围 `{scan_info['wavelength_range_nm'][0]:.0f}-{scan_info['wavelength_range_nm'][1]:.0f} nm`，"
            f"点数 `{scan_info['point_count']}`，步长 `{scan_info['median_step_nm']:.1f} nm`，"
            f"探测器 `{scan_meta['detector']}`，固定波长 `{scan_meta['fixed_or_offset_nm']}`"
        )
        lines.append(
            f"  最强峰 `{scan_summary['strongest_peak_nm']:.0f} nm`，最大计数 `{fmt_number(scan_summary['max_counts'])}`，"
            f"积分信号 `{fmt_number(scan_summary['integrated_above_baseline_counts_nm'])} counts·nm`，"
            f"负值占比 `{scan_summary['negative_fraction']:.4f}`"
        )
        peak_text = "；".join(
            [
                f"{peak['emission_wavelength_nm']:.0f} nm / {peak['counts']:.4f}"
                for peak in scan_summary["dominant_peaks"][:4]
            ]
        )
        lines.append(f"  主要峰：{peak_text}")
    lines.append("")

    lines.append("### 4.2 扫描间对比")
    if summary["comparisons"]:
        for comparison in summary["comparisons"]:
            lines.append(
                f"- `{comparison['scan_name']}` 相对 `{comparison['reference_scan_name']}` 的峰高比为 "
                f"`{comparison['max_count_ratio_vs_reference']:.4f}`，积分强度比为 "
                f"`{comparison['integrated_above_baseline_ratio_vs_reference']:.4f}`，"
                f"最强峰位移为 `{comparison['strongest_peak_shift_nm_vs_reference']:.1f} nm`。"
            )
    else:
        lines.append("- 当前仅有单条可读扫描，未形成扫描间对比结果。")
    lines.append("")

    lines.append("### 4.3 综合判断")

    if summary["steady_state_detected"]:
        lines.append("- 当前文件可以支持稳态 PL 发射谱分析。")
    if not summary["transient_decay_detected"]:
        lines.append("- 当前文件未提供可读的瞬态衰减数据，因此不能输出寿命常数、衰减拟合或淬灭机理结论。")

    strongest_scans = sorted(summary["scans"], key=lambda item: item["max_counts"], reverse=True)
    if len(strongest_scans) >= 2:
        reference = strongest_scans[0]
        weaker = strongest_scans[1]
        lines.append(
            f"- 从原始峰高看，`{weaker['scan_name']}` 明显弱于 `{reference['scan_name']}`，"
            f"但两者最强峰都位于 `~{reference['strongest_peak_nm']:.0f} nm` 附近，未见明显主峰漂移。"
        )

    if any(scan["negative_fraction"] > 0.5 for scan in summary["scans"]):
        lines.append("- 至少一条扫描存在较高负值占比，说明基线偏移或噪声影响较强，次峰解释应保持保守。")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("figure_png")
    parser.add_argument("figure_pdf")
    parser.add_argument("output_md")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    report = render_report(parsed, summary, args.figure_png, args.figure_pdf)

    output_path = Path(args.output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
