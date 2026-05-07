#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def wetting_label_cn(angle: float | None) -> str:
    if angle is None:
        return "无法判断"
    if angle < 10:
        return "超亲水"
    if angle < 90:
        return "亲水（或接近临界）"
    if angle < 150:
        return "疏水"
    return "超疏水"


def symmetry_label_cn(label: str | None) -> str:
    mapping = {
        "good_symmetry": "左右差异<=2°，对称性好",
        "possible_hysteresis_or_surface_heterogeneity": "左右差异>2°，可能存在滞后或表面不均一",
        "insufficient_side_data": "左右数据不全，无法评估",
    }
    if label is None:
        return "无法评估"
    return mapping.get(label, label)


def quality_assessment_cn(label: str | None) -> str:
    mapping = {
        "mostly_symmetric_good_data_quality": "多数测试点左右差异在阈值内，液滴形态整体较对称，数据质量较好。",
        "mixed_symmetry_needs_spot_check": "左右对称性表现混合，建议对超阈值点位复核基线与局部表面状态。",
        "frequent_asymmetry_possible_hysteresis_or_nonuniform_surface": "超阈值点位较多，可能存在明显滞后或表面粗糙/化学不均一。",
        "insufficient_side_data": "左右角度数据不足，无法完成对称性质量判断。",
    }
    if label is None:
        return "暂无总体判断。"
    return mapping.get(label, label)


def value_or_dash(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def translate_notice(message: str) -> str:
    mapping = {
        "The current sample is a screenshot bundle, not a structured numeric report.": "当前输入是截图包，不是结构化数值原始表。",
        "Liquid identity, droplet volume, and acquisition method are not visible in the supplied images.": "现有截图未提供液体类型、液滴体积与采集方法信息。",
        "OCR-derived values should be treated as approximate until checked against the original vendor export or multimodal cross-check.": "OCR 提取值属于近似读数，需结合原始导出或多模态复核确认。",
        "No explicit surface-tension value was visible in the parsed screenshots.": "截图中未识别到明确的表面张力字段。",
        "No contact-angle values were extracted from the bundle.": "当前数据未提取到可用接触角数值。",
        "Duplicate screenshots were detected and excluded from the summary.": "检测到重复截图，统计时已去重。",
    }
    return mapping.get(message, message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("output_markdown")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))

    image_records = parsed.get("image_records", [])
    group_summaries = summary.get("group_summaries", [])
    sample_summaries = summary.get("sample_summaries", [])
    quality = summary.get("data_quality_symmetry", {})
    cross_sample = summary.get("cross_sample_comparison", {})

    lines: list[str] = []
    lines.append("# 接触角数据分析报告（材料化学研究版）")
    lines.append("")
    lines.append("## 一、研究对象与数据概览")
    lines.append(f"- 数据源：`{parsed.get('source_file', '')}`")
    lines.append(f"- 测量模式：`{summary.get('measurement_mode_detected', 'unknown')}`")
    lines.append(f"- 图片总数：{parsed.get('image_file_count', 0)}")
    lines.append(f"- 去重后参与计算图片数：{parsed.get('unique_image_count', 0)}")
    lines.append(f"- 可解析接触角分组数：{summary.get('groups_with_contact_angle', 0)} / {summary.get('group_count', 0)}")
    lines.append("- 报告用途：用于材料表面润湿行为、样品间界面性质差异与测试数据可信度的科研比较。")
    lines.append("")

    lines.append("## 二、判定标准与数据处理方法")
    lines.append("- 润湿性判据：平均接触角 `<90°` 倾向亲水，`90°–150°` 倾向疏水，`>=150°` 可判定为超疏水。")
    lines.append("- 对称性/滞后指标：`|Left CA - Right CA|`；通常 `<=2°` 视为液滴形态对称性较好、基线选择较可靠。")
    lines.append("- 提取策略：逐图读取 `left_ca/right_ca/average_ca`，无法识别字段记为 `null`，不进行主观补值。")
    lines.append("")

    lines.append("## 三、实验结果")
    lines.append("### 3.1 逐图提取结果（按提取规范输出）")
    lines.append("提取字段：`left_ca`、`right_ca`、`average_ca`、`unit`。当图片只识别出单值角度时，按规范将其记为 `average_ca`。")
    lines.append("")
    lines.append("| 图片 | 样品 | 组别 | left_ca | right_ca | average_ca | unit | 润湿性判定 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for record in image_records:
        average = record.get("average_ca")
        lines.append(
            "| {path} | {sample} | {group} | {left} | {right} | {avg} | {unit} | {wetting} |".format(
                path=record.get("relative_path", "-"),
                sample=record.get("sample_id", "-"),
                group=record.get("group_id", "-"),
                left=value_or_dash(record.get("left_ca")),
                right=value_or_dash(record.get("right_ca")),
                avg=value_or_dash(average),
                unit=record.get("unit", "degree"),
                wetting=wetting_label_cn(average),
            )
        )
    lines.append("")

    lines.append("### 3.2 分组统计与样品润湿性")
    lines.append("| 样品 | 组别 | 左接触角(deg) | 右接触角(deg) | 平均接触角(deg) | 左右差值(deg) | 润湿性 | 对称性评估 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for group in group_summaries:
        mean_value = group.get("mean_contact_angle_deg")
        left_value = group.get("left_contact_angle_deg")
        right_value = group.get("right_contact_angle_deg")
        diff_value = group.get("left_right_difference_deg")
        lines.append(
            "| {sample} | {group_id} | {left} | {right} | {mean} | {diff} | {wetting} | {symmetry} |".format(
                sample=group.get("sample_id", "-"),
                group_id=group.get("group_id", "-"),
                left=value_or_dash(left_value),
                right=value_or_dash(right_value),
                mean=value_or_dash(mean_value),
                diff=value_or_dash(diff_value),
                wetting=wetting_label_cn(mean_value),
                symmetry=symmetry_label_cn(group.get("symmetry_assessment")),
            )
        )
    lines.append("")

    lines.append("### 样品级汇总")
    if sample_summaries:
        lines.append("| 样品 | 可读分组数 | 平均接触角(deg) | 最小值(deg) | 最大值(deg) | 平均左右差值(deg) | 判定 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for sample in sample_summaries:
            lines.append(
                "| {sample_id} | {count} | {mean} | {min_v} | {max_v} | {asymmetry} | {wetting} |".format(
                    sample_id=sample.get("sample_id", "-"),
                    count=sample.get("readable_group_count", 0),
                    mean=value_or_dash(sample.get("mean_contact_angle_deg")),
                    min_v=value_or_dash(sample.get("min_contact_angle_deg")),
                    max_v=value_or_dash(sample.get("max_contact_angle_deg")),
                    asymmetry=value_or_dash(sample.get("mean_left_right_difference_deg")),
                    wetting=wetting_label_cn(sample.get("mean_contact_angle_deg")),
                )
            )
    else:
        lines.append("- 当前数据未形成可用的样品级统计。")
    lines.append("")

    lines.append("### 3.3 同订单样品横向比较")
    if cross_sample.get("enabled"):
        ranking = cross_sample.get("ranking_by_mean_contact_angle_desc", [])
        ranking_text = " > ".join(
            f"{item.get('sample_id')}({value_or_dash(item.get('mean_contact_angle_deg'))} deg)"
            for item in ranking
        )
        lines.append(f"- 平均接触角排序（高到低）：{ranking_text}")
        lines.append(
            "- 样品间最大均值差：{diff} deg（最高：{high}；最低：{low}）".format(
                diff=value_or_dash(cross_sample.get("max_between_sample_diff_deg")),
                high=cross_sample.get("highest_sample", {}).get("sample_id", "-"),
                low=cross_sample.get("lowest_sample", {}).get("sample_id", "-"),
            )
        )
    else:
        lines.append("- 本订单可解析样品少于 2 个，不执行横向比较。")
    lines.append("")

    stats = summary.get("contact_angle_statistics", {})
    mean_deg = stats.get("mean_deg")

    lines.append("## 四、材料化学视角解读")
    if mean_deg is None:
        lines.append("- 当前未获得足够可用接触角数据，无法进行可靠的材料表面润湿性解读。")
    else:
        lines.append(
            "- 从可读数据看，样品整体平均接触角为 {mean} deg（范围 {min_v}–{max_v} deg），说明该批材料表面总体表现为**{wetting}**。".format(
                mean=value_or_dash(mean_deg),
                min_v=value_or_dash(stats.get("min_deg")),
                max_v=value_or_dash(stats.get("max_deg")),
                wetting=wetting_label_cn(mean_deg),
            )
        )
    if cross_sample.get("enabled"):
        highest = cross_sample.get("highest_sample", {})
        lowest = cross_sample.get("lowest_sample", {})
        lines.append(
            "- 横向比较显示，不同样品间润湿性存在可量化差异：{high_id}（{high_v} deg）高于 {low_id}（{low_v} deg），最大均值差 {diff} deg。".format(
                high_id=highest.get("sample_id", "-"),
                high_v=value_or_dash(highest.get("mean_contact_angle_deg")),
                low_id=lowest.get("sample_id", "-"),
                low_v=value_or_dash(lowest.get("mean_contact_angle_deg")),
                diff=value_or_dash(cross_sample.get("max_between_sample_diff_deg")),
            )
        )
        lines.append("- 该差异可作为材料配方、表面改性或工艺条件优化的比较依据之一。")
    lines.append("")

    lines.append("## 五、数据质量与不确定性评估")
    threshold = quality.get("left_right_difference_threshold_deg")
    groups_with_both = quality.get("groups_with_both_sides", 0)
    within_threshold = quality.get("groups_within_threshold", 0)
    over_threshold = quality.get("groups_over_threshold", 0)
    ratio = quality.get("within_threshold_ratio")
    lines.append(
        "- 左右差异（Hysteresis indicator）定义：`|Left CA - Right CA|`；本报告阈值采用 `{threshold}`°（<=2° 视为对称性较好）。".format(
            threshold=value_or_dash(float(threshold)) if threshold is not None else "-"
        )
    )
    lines.append(f"- 可评估左右差异的分组数：{groups_with_both}")
    lines.append(f"- 阈值内分组（<=2°）：{within_threshold}")
    lines.append(f"- 超阈值分组（>2°）：{over_threshold}")
    if ratio is not None:
        lines.append(f"- 阈值内占比：{float(ratio) * 100:.1f}%")
    lines.append(f"- 质量判断：{quality_assessment_cn(quality.get('overall_assessment'))}")
    lines.append("- 解释依据：左右差异在 2° 以内通常对应液滴形态更对称、基线选取更可靠；若差异持续偏大，常提示局部粗糙或化学不均一并可能导致接触角滞后。")
    lines.append("")

    lines.append("## 六、结论（面向材料化学研究）")
    if mean_deg is None:
        lines.append("- 未提取到足够的接触角数值，无法给出整体润湿性结论。")
    else:
        lines.append(
            "- 在可读数据范围内，整体平均接触角为 {mean} deg（范围 {min_v}–{max_v} deg），整体表现为**{wetting}**。".format(
                mean=value_or_dash(mean_deg),
                min_v=value_or_dash(stats.get("min_deg")),
                max_v=value_or_dash(stats.get("max_deg")),
                wetting=wetting_label_cn(mean_deg),
            )
        )
    if cross_sample.get("enabled"):
        highest = cross_sample.get("highest_sample", {})
        lowest = cross_sample.get("lowest_sample", {})
        lines.append(
            "- 同订单横向比较显示：{high_id}（{high_v} deg）> ... > {low_id}（{low_v} deg），样品间最大均值差 {diff} deg。".format(
                high_id=highest.get("sample_id", "-"),
                high_v=value_or_dash(highest.get("mean_contact_angle_deg")),
                low_id=lowest.get("sample_id", "-"),
                low_v=value_or_dash(lowest.get("mean_contact_angle_deg")),
                diff=value_or_dash(cross_sample.get("max_between_sample_diff_deg")),
            )
        )
    if summary.get("groups_with_surface_tension", 0) == 0:
        lines.append("- 本批图片未见明确表面张力字段（如 surface tension / IFT / SFT / gamma），因此不输出表面张力结论。")

    lines.append("")
    lines.append("## 七、限制与置信度说明")
    for item in summary.get("limitations", []):
        lines.append(f"- {translate_notice(item)}")
    for warning in summary.get("warnings", []):
        lines.append(f"- 说明：{translate_notice(warning)}")

    output_path = Path(args.output_markdown)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
