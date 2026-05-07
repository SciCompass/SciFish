#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def clean_vendor_text(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip()
    replacements = {
        "掳C": "°C",
        "鲁": "^3",
        "cm^3 STP/min": "cm^3 STP/min",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text or "unknown"


def is_signal_inverted(metadata: dict) -> bool:
    return str(metadata.get("signal_inverted", "")).strip().lower() == "yes"


def display_direction(raw_direction: str, inverted: bool) -> str:
    if not inverted:
        return raw_direction
    return "positive" if raw_direction == "negative" else "negative"


def direction_label(raw_direction: str, inverted: bool) -> str:
    shown = display_direction(raw_direction, inverted)
    return "上行事件" if shown == "positive" else "下行事件"


def format_event_lines(events: list[dict], label: str, inverted: bool) -> str:
    if not events:
        return f"- {label}：未检出"
    lines = []
    for idx, event in enumerate(events[:3], start=1):
        shown_signal = -float(event["peak_signal_au"]) if inverted else float(event["peak_signal_au"])
        lines.append(
            f"- {label}{idx}：{event['peak_temperature_c']:.2f} °C，"
            f"{direction_label(event['direction'], inverted)}，"
            f"显示信号 {shown_signal:.6f} a.u.，"
            f"prominence {event['prominence_au']:.6f} a.u."
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("figure_path")
    parser.add_argument("output_md")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    metadata = parsed.get("metadata", {})
    figure_path = Path(args.figure_path).resolve().as_posix()
    inverted = is_signal_inverted(metadata)

    dominant = summary.get("dominant_event") or {}
    warnings = summary.get("warnings", [])
    warning_text = "；".join(warnings) if warnings else "无额外警告。"
    mode = summary.get("analysis_mode", metadata.get("analysis_mode", "unknown"))
    sample_label = metadata.get("sample_label", "unknown")
    signal_inverted = clean_vendor_text(metadata.get("signal_inverted", "unknown"))
    displayed_direction = direction_label(dominant.get("direction", "unknown"), inverted) if dominant else "unknown"
    display_note = "已按可读性将图谱上下翻转显示。" if inverted else "图谱保持原始方向显示。"
    if inverted:
        positive_events = summary.get("negative_events", [])
        negative_events = summary.get("positive_events", [])
    else:
        positive_events = summary.get("positive_events", [])
        negative_events = summary.get("negative_events", [])

    report = f"""# TPD/TPR/TPO 中文综合报告

## 样品与数据概况
- 源文件：`{parsed.get('source_file', 'unknown')}`
- 样品标签：{clean_vendor_text(sample_label)}
- 分析模式：{clean_vendor_text(mode)}
- 开始时间：{clean_vendor_text(metadata.get('started_at'))}
- 结束时间：{clean_vendor_text(metadata.get('completed_at'))}
- 测得流量：{clean_vendor_text(metadata.get('measured_flow_rate'))}
- 信号反转标记：{signal_inverted}

## 图谱结果
- 数据点数：{summary.get('point_count', 0)}
- 温度范围：{summary.get('temperature_range_c', ['unknown', 'unknown'])[0]} - {summary.get('temperature_range_c', ['unknown', 'unknown'])[1]} °C
- 原始信号范围：{summary.get('raw_signal_range_au', ['unknown', 'unknown'])[0]} - {summary.get('raw_signal_range_au', ['unknown', 'unknown'])[1]} a.u.
- 主导事件：{dominant.get('peak_temperature_c', 'unknown')} °C，{displayed_direction}，温区 `{dominant.get('temperature_band', 'unknown')}`
{format_event_lines(positive_events, '主要事件', inverted)}
{format_event_lines(negative_events, '次要反向事件', inverted)}

## 图谱图像
![TPD/TPR/TPO profile]({figure_path})

## 结构化分析
- 直接观察：当前文件可确认是 {clean_vendor_text(mode)} 曲线，主导事件位于 {dominant.get('peak_temperature_c', 'unknown')} °C。
- 分析说明：{display_note} 当前 skill 输出的是相对信号随温度变化的事件筛查结果，适合描述主峰温度、事件方向和高低温分布，不适合直接换算绝对吸附/还原/氧化量。
- 风险提示：{warning_text.replace('Signal inverted flag is set in the vendor report; inspect event direction before assigning physical meaning.', '原始报告标记了 Signal inverted，因此事件方向需要结合仪器输出方向一起解释。')}
- 数据边界：除非原始文件明确提供校准和积分规则，否则不能把当前信号直接解释成绝对 uptake、site density、stoichiometry 或具体机理。
"""

    output_path = Path(args.output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
