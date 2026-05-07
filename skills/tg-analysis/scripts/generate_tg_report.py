#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import OrderedDict
from pathlib import Path


DISPLAY_EXTENSIONS = [".png", ".jpg", ".jpeg", ".svg", ".webp"]
ALL_FIGURE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".svg", ".webp", ".pdf", ".tiff", ".tif"]
METADATA_LABELS = {
    "INSTRUMENT:": "测试仪器",
    "DATE/TIME:": "测试时间",
    "SAMPLE MASS /mg:": "样品质量",
    "MATERIAL:": "样品材料",
    "PROTECTIVE GAS:": "保护气氛",
    "FLOW RATE /(ml/min):": "保护气流量",
    "FLOW RATE 1 /(ml/min):": "辅助气流量",
    "RANGE:": "升温程序",
    "OPERATOR:": "测试人员",
    "TYPE OF CRUCIBLE:": "坩埚类型",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", help="Parsed TG JSON produced by parse_tg_xls.py")
    parser.add_argument("summary_json", help="Summary JSON produced by summarize_tg.py")
    parser.add_argument("output_report", help="Markdown report output path")
    parser.add_argument("--figure-dir", help="Directory containing generated figure files")
    parser.add_argument("--figure-prefix", help="Filename prefix used to collect figures")
    parser.add_argument("--sample-label", help="Human-readable sample label for the report")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_prefix(path: Path) -> str:
    stem = path.stem
    known_suffixes = [
        ".regression",
        ".step-summary",
        ".summary",
        ".reparse",
        ".parsed",
    ]
    changed = True
    while changed:
        changed = False
        for suffix in known_suffixes:
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                changed = True
    return stem


def to_report_path(target: Path, report_path: Path) -> str:
    return Path(os.path.relpath(target, report_path.parent)).as_posix()


def to_image_markdown_path(target: Path) -> str:
    return target.resolve().as_posix()


def classify_figure(stem: str) -> tuple[str, str]:
    lower = stem.lower()
    if "comparison" in lower:
        return "comparison", "图形总览"
    if "steps" in lower:
        return "step", "台阶分析图"
    if "publication" in lower:
        return "publication", "发表级图谱"
    return "other", "其他结果图"


def collect_figures(figure_dir: Path, prefix: str) -> OrderedDict[str, dict]:
    groups: OrderedDict[str, dict] = OrderedDict()
    if not figure_dir.exists():
        return groups

    figure_files = sorted(
        path
        for path in figure_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ALL_FIGURE_EXTENSIONS and path.name.startswith(prefix)
    )
    for figure_path in figure_files:
        key = figure_path.stem
        category, section_title = classify_figure(key)
        if key not in groups:
            groups[key] = {
                "category": category,
                "section_title": section_title,
                "files": [],
            }
        groups[key]["files"].append(figure_path)
    return groups


def choose_display_figure(files: list[Path]) -> Path | None:
    ordered = sorted(
        files,
        key=lambda item: (
            DISPLAY_EXTENSIONS.index(item.suffix.lower()) if item.suffix.lower() in DISPLAY_EXTENSIONS else 999,
            item.suffix.lower(),
        ),
    )
    for path in ordered:
        if path.suffix.lower() in DISPLAY_EXTENSIONS:
            return path
    return None


def build_stage_table(stages: list[dict]) -> str:
    lines = [
        "| 台阶 | 起始温度 (°C) | DTG 峰温 (°C) | 终止温度 (°C) | 起始质量 (%) | 终止质量 (%) | 失重 (%) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not stages:
        lines.append("| 无 | N/A | N/A | N/A | N/A | N/A | N/A |")
        return "\n".join(lines)
    for idx, stage in enumerate(stages, start=1):
        lines.append(
            "| "
            f"台阶 {idx} | "
            f"{stage.get('start_c', 'N/A')} | "
            f"{stage.get('peak_c', 'N/A')} | "
            f"{stage.get('end_c', 'N/A')} | "
            f"{stage.get('start_mass_pct', 'N/A')} | "
            f"{stage.get('end_mass_pct', 'N/A')} | "
            f"{stage.get('mass_loss_pct', 'N/A')} |"
        )
    return "\n".join(lines)


def build_metadata_section(metadata: dict) -> list[str]:
    if not metadata:
        return ["- 当前数据文件未提供可直接读取的实验元数据。"]

    lines = []
    used = set()
    for key, label in METADATA_LABELS.items():
        if key in metadata:
            lines.append(f"- {label}：`{metadata[key]}`")
            used.add(key)
    for key in sorted(metadata):
        if key in used:
            continue
        lines.append(f"- {key.rstrip(':')}：`{metadata[key]}`")
    return lines


def build_observations(summary: dict) -> list[str]:
    stages = summary.get("stages", [])
    observations = [
        f"- 测试温区为 `{summary.get('temperature_range_c', ['N/A', 'N/A'])[0]} °C` 至 `{summary.get('temperature_range_c', ['N/A', 'N/A'])[1]} °C`。",
        f"- 初始相对质量为 `{summary.get('initial_mass_pct', 'N/A')} %`，终点残余为 `{summary.get('final_mass_pct', 'N/A')} %`，总失重为 `{summary.get('total_mass_loss_pct', 'N/A')} %`。",
    ]
    if stages:
        dominant = max(stages, key=lambda item: float(item.get("mass_loss_pct", 0.0)))
        observations.append(
            "- 主导失重台阶位于 "
            f"`{dominant.get('start_c', 'N/A')} °C` 至 `{dominant.get('end_c', 'N/A')} °C`，"
            f"DTG 峰温约为 `{dominant.get('peak_c', 'N/A')} °C`，"
            f"对应失重 `{dominant.get('mass_loss_pct', 'N/A')} %`。"
        )
        if len(stages) > 1:
            observations.append(f"- 自动识别得到 `{len(stages)}` 个主要失重台阶，可用于分段讨论热行为。")
    else:
        observations.append("- 当前曲线中未自动识别出清晰的失重台阶。")
    return observations


def build_interpretation(summary: dict) -> list[str]:
    stages = summary.get("stages", [])
    if not stages:
        return ["- 当前自动分析未识别出明确台阶，因此更适合基于整体 TG/DTG 轮廓进行定性判断。"]

    first_stage = min(stages, key=lambda item: float(item.get("start_c", 0.0)))
    dominant_stage = max(stages, key=lambda item: float(item.get("mass_loss_pct", 0.0)))
    return [
        f"- 低温段如存在较小失重台阶，可优先考虑吸附水、残余溶剂或弱结合小分子的脱除；本次首个台阶峰温约为 `{first_stage.get('peak_c', 'N/A')} °C`。",
        f"- 主失重过程集中在 `{dominant_stage.get('start_c', 'N/A')} °C` 至 `{dominant_stage.get('end_c', 'N/A')} °C`，通常对应样品主体结构的主要热分解或相对剧烈的挥发过程。",
        f"- 终点残余为 `{summary.get('final_mass_pct', 'N/A')} %`，可结合样品体系进一步讨论其是否与无机残留、灰分、填料或稳定炭化产物相关，但不宜仅凭 TG 结果直接定性。",
    ]


def build_limits(summary: dict) -> list[str]:
    warnings = summary.get("warnings", [])
    lines = ["- 台阶起止点与峰位来自自动算法识别，适合用于科研讨论和样品间比较，但不应视为绝对边界。"]
    if summary.get("dtg_source") == "estimated_from_mass":
        lines.append("- 当前 DTG 信号由 TG 曲线数值求导得到，峰位和峰强会受到平滑参数影响。")
    else:
        lines.append("- 当前 DTG 峰位优先基于导出文件中的原始导数信号识别。")
    lines.extend(f"- {warning}" for warning in warnings)
    return lines


def build_figure_sections(figure_groups: OrderedDict[str, dict], report_path: Path) -> list[str]:
    sections: list[str] = []
    ordered_categories = ["comparison", "step", "publication", "other"]
    for category in ordered_categories:
        grouped = [(key, value) for key, value in figure_groups.items() if value["category"] == category]
        if not grouped:
            continue
        title = grouped[0][1]["section_title"]
        sections.append(f"## {title}")
        sections.append("")
        for key, info in grouped:
            display = choose_display_figure(info["files"])
            pretty_name = key.replace("-", " ")
            sections.append(f"### {pretty_name}")
            if display is not None:
                sections.append(f"![{pretty_name}]({to_image_markdown_path(display)})")
                sections.append("")
            if category == "comparison":
                sections.append("- 该图用于展示不同样品或不同处理条件下整体 TG/DTG 行为的对比关系。")
            elif category == "step":
                sections.append("- 该图重点展示台阶起止点、台阶失重和对应 DTG 峰位，便于讨论分段热行为。")
            elif category == "publication":
                sections.append("- 该图为适合论文或正式汇报使用的精简版图谱。")
            else:
                sections.append("- 该图为补充结果图，可作为进一步讨论时的参考。")
            sections.append("")
    return sections


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_json)
    summary_path = Path(args.summary_json)
    output_report = Path(args.output_report)
    output_report.parent.mkdir(parents=True, exist_ok=True)

    parsed = load_json(input_path)
    summary = load_json(summary_path)

    sample_label = args.sample_label or derive_prefix(summary_path)
    figure_prefix = args.figure_prefix or derive_prefix(summary_path)
    if args.figure_dir:
        figure_dir = Path(args.figure_dir)
    else:
        workspace_root = output_report.parents[2] if len(output_report.parents) >= 3 else output_report.parent
        figure_dir = workspace_root / "figures" / output_report.parent.name
    figure_groups = collect_figures(figure_dir, figure_prefix)

    lines = [
        f"# TG 热重分析报告 - {sample_label}",
        "",
        "## 样品与实验信息",
        f"- 原始数据文件：`{Path(parsed.get('source_file', 'N/A')).name}`",
        *build_metadata_section(parsed.get("metadata", {})),
        "",
        "## 热失重结果概述",
        f"- 温度范围：`{summary.get('temperature_range_c', ['N/A', 'N/A'])[0]} °C` 至 `{summary.get('temperature_range_c', ['N/A', 'N/A'])[1]} °C`",
        f"- 初始相对质量：`{summary.get('initial_mass_pct', 'N/A')} %`",
        f"- 终点残余：`{summary.get('final_mass_pct', 'N/A')} %`",
        f"- 总失重：`{summary.get('total_mass_loss_pct', 'N/A')} %`",
        "",
        "## 台阶分析结果",
        build_stage_table(summary.get("stages", [])),
        "",
        "## 结果解读",
        *build_observations(summary),
        "",
        "## 可能的热行为解释",
        *build_interpretation(summary),
        "",
    ]

    figure_sections = build_figure_sections(figure_groups, output_report)
    if figure_sections:
        lines.extend(figure_sections)
    else:
        lines.extend(
            [
                "## 结果图谱",
                "",
                "- 当前未找到与本次分析对应的结果图片。",
                "",
            ]
        )

    lines.extend(
        [
            "## 说明与边界",
            *build_limits(summary),
            "",
        ]
    )

    output_report.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
