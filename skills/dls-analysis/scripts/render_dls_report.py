#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def format_peak_lines(peaks: list[dict]) -> str:
    if not peaks:
        return "- 未检出可报告的次级峰"
    return "\n".join(
        f"- 峰{i + 1}：{peak['size_nm']:.3f} nm，强度 {peak['intensity_pct']:.3f}%"
        for i, peak in enumerate(peaks[:3])
    )


def format_warning_line(warnings: list[str]) -> str:
    if not warnings:
        return "未见额外多峰或异常尾部警告。"
    return "；".join(warnings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("figure_path")
    parser.add_argument("output_md")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    figure_path = Path(args.figure_path).resolve().as_posix()

    metadata = parsed.get("metadata", {})
    columns = parsed.get("columns", {})
    main_peak = summary.get("main_peak", {})
    nonzero_range = summary.get("nonzero_range_nm") or ["未知", "未知"]
    tail_flags = summary.get("tail_flags", {})
    zeta_available = bool(summary.get("zeta_available", False))
    top_peaks = summary.get("top_peaks", [])
    warnings = summary.get("warnings", [])

    direct_observation = (
        f"主峰位于 {main_peak.get('size_nm', 0.0):.3f} nm，"
        f"对应强度 {main_peak.get('intensity_pct', 0.0):.3f}%。"
    )
    interpretation = (
        "结果仅支持粒径强度分布层面的观察，可用于描述主峰位置、是否存在多峰迹象以及是否延伸至大颗粒尾部。"
    )
    zeta_boundary = (
        "原始文件未提供可解析的 zeta 电位相关字段，因此本报告不输出 Z-average、PDI、zeta potential、mobility 或 conductivity 结论。"
        if not zeta_available
        else "原始文件包含 zeta 相关字段，但本轮报告仍以当前 summary 为准。"
    )

    report = f"""# DLS 中文综合报告

## 样品与数据概况
- 源文件：`{parsed.get('source_file', 'unknown')}`
- 工作表：`{parsed.get('sheet_name', 'unknown')}`
- 记录标签：{metadata.get('record_label', 'unknown')}
- 分布类型：{summary.get('distribution_kind', 'unknown')}
- 数据列：粒径 `{columns.get('size_nm', 'unknown')}`；强度 `{columns.get('intensity_pct', 'unknown')}`

## 图谱结果
- 主峰位置：{main_peak.get('size_nm', 0.0):.3f} nm
- 主峰强度：{main_peak.get('intensity_pct', 0.0):.3f}%
- 非零分布范围：{nonzero_range[0]} - {nonzero_range[1]} nm
- 大颗粒尾部：{'是' if tail_flags.get('large_particle_tail') else '否'}
- 尾部终点：{tail_flags.get('tail_end_nm', 'unknown')} nm
{format_peak_lines(top_peaks)}

## 图谱图像
![DLS distribution]({figure_path})

## 结构化分析
- 直接观察：{direct_observation}
- 分析说明：{interpretation}
- 多峰/尾部提示：{format_warning_line(warnings)}
- 数据边界：{zeta_boundary}
"""

    output_path = Path(args.output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
