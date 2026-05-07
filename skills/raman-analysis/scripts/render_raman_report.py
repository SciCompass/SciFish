#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_single_report(parsed: dict, summary: dict, figure_png: str, figure_pdf: str) -> str:
    figure_png_abs = str(Path(figure_png).resolve()).replace("\\", "/")
    lines: list[str] = []
    lines.append("# Raman 综合分析报告（中文版）")
    lines.append("")
    lines.append("## 1. 样品与数据概况")
    lines.append(f"- 输入文件：`{parsed['source_file']}`")
    lines.append(
        f"- Raman shift 范围：`{parsed['summary']['shift_range_cm^-1'][0]:.3f}-"
        f"{parsed['summary']['shift_range_cm^-1'][1]:.3f} cm^-1`"
    )
    lines.append(f"- 数据点数：`{parsed['summary']['point_count']}`")
    lines.append(f"- 中位步长：`{parsed['summary']['median_step_cm^-1']:.3f} cm^-1`")
    lines.append(f"- 背景类型：`{summary['background_character']}`")
    lines.append("")
    lines.append("## 2. 图谱结果")
    lines.append(f"- 主峰数量：`{summary['band_count']}`")
    lines.append(f"- 最大强度：`{summary['max_intensity_au']:.4f}`")
    lines.append(
        f"- 荧光背景判断：`{str(summary['fluorescence_screening']['likely_present']).lower()}`"
    )
    lines.append(
        f"- 碳材料筛查：D-like=`{str(summary['carbon_screening']['has_d_like_band']).lower()}`，"
        f"G-like=`{str(summary['carbon_screening']['has_g_like_band']).lower()}`，"
        f"2D-like=`{str(summary['carbon_screening']['has_2d_like_band']).lower()}`"
    )
    lines.append("")
    lines.append("## 3. 图谱图像")
    lines.append(f"- PNG 图谱：`{figure_png}`")
    lines.append(f"- PDF 图谱：`{figure_pdf}`")
    lines.append("")
    lines.append(f"![Raman 图谱]({figure_png_abs})")
    lines.append("")
    lines.append("## 4. 结构化分析")
    lines.append("### 4.1 主峰与次峰")
    for band in summary["dominant_bands"][:5]:
        corrected = (
            f"{band['corrected_height_au']:.4f}"
            if band.get("corrected_height_au") is not None
            else "宽峰通道保留"
        )
        lines.append(
            f"- `{band['raman_shift_cm^-1']:.3f} cm^-1`：强度=`{band['intensity_au']:.4f}`，"
            f"相对强度=`{band['relative_intensity_pct']:.2f}%`，"
            f"prominence=`{band['prominence_au']:.4f}`，校正高度=`{corrected}`"
        )
    lines.append("")
    lines.append("### 4.2 综合判断")
    if summary["background_character"] == "broad_background_or_fluorescence_influenced":
        lines.append("- 当前谱图显示出较强宽背景或荧光影响，弱峰解释应保持保守。")
    else:
        lines.append("- 当前谱图以离散峰为主，主峰位置可用于保守的峰位筛查。")
    if summary["carbon_screening"]["has_d_like_band"] and summary["carbon_screening"]["has_g_like_band"]:
        ratio = summary["carbon_screening"].get("d_to_g_height_ratio")
        ratio_text = f"{ratio:.3f}" if ratio is not None else "未计算"
        lines.append(
            f"- 当前结果在 `~1343 cm^-1` 与 `~1592 cm^-1` 附近存在成对特征峰，"
            f"D/G 高度比约为 `{ratio_text}`。"
        )
    if any(2750.0 <= band["raman_shift_cm^-1"] <= 2950.0 for band in summary["dominant_bands"]):
        lines.append("- 高波数区保留了代表性宽峰，可用于描述宽带特征，但不宜直接做材料定性。")
    lines.append("- 该结果属于峰位筛查与谱形判断结果，若缺少参考谱，不应直接给出确定性材料归属。")
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
    report = render_single_report(parsed, summary, args.figure_png, args.figure_pdf)

    output_path = Path(args.output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
