#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from bloom_draw import infer_signal_mode

mpl.rcParams.update(
    {
        "figure.dpi": 300,
        "savefig.dpi": 600,
        "figure.figsize": (7.0, 2.8),
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 7.5,
        "axes.labelsize": 8.5,
        "axes.linewidth": 0.7,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def _to_abs_md(path: Path) -> str:
    return path.resolve().as_posix()


def _format_optional(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "无"
    return f"{float(value):.{digits}f}"


def _prepare_tauc_axes(wavelength_nm: np.ndarray, signal_values: np.ndarray, mode: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    conversion_factor = 1024.0 if mode == "reflectance" else 1240.0
    hv = conversion_factor / wavelength_nm
    if mode == "absorbance":
        mask = signal_values > 0
        base = signal_values[mask] * hv[mask]
        hv = hv[mask]
    elif mode == "transmittance":
        y = signal_values.copy()
        if np.nanmax(y) > 2.0:
            y = y / 100.0
        mask = (y > 0) & (y < 1)
        hv = hv[mask]
        alpha = -np.log10(y[mask])
        base = alpha * hv
    elif mode == "reflectance":
        y = signal_values.copy()
        if np.nanmax(y) > 2.0:
            y = y / 100.0
        mask = (y > 0) & (y < 1)
        hv = hv[mask]
        fr = ((1.0 - y[mask]) ** 2) / (2.0 * y[mask])
        base = fr * hv
    else:
        return np.array([]), np.array([]), np.array([])

    if len(hv) == 0:
        return np.array([]), np.array([]), np.array([])
    order = np.argsort(hv)
    hv = hv[order]
    base = np.clip(base[order], a_min=0.0, a_max=None)
    return hv, np.sqrt(base), np.square(base)


def _plot_panel(ax: plt.Axes, hv: np.ndarray, y: np.ndarray, candidate: dict | None, title: str, y_label: str) -> None:
    ax.plot(hv, y, color="#111827", linewidth=1.15, label=title)
    if candidate is not None:
        k = float(candidate["slope"])
        b = float(candidate["intercept"])
        eg = float(candidate["eg_ev"])
        hmin = float(candidate["segment_hv_min_ev"])
        hmax = float(candidate["segment_hv_max_ev"])
        xline = np.linspace(hmin, hmax, 120)
        yline = k * xline + b
        ax.plot(xline, yline, color="#b91c1c", linestyle="--", linewidth=1.0, label="Linear fit")
        ax.axvline(eg, color="#2563eb", linestyle=":", linewidth=0.95)
        ax.text(eg + 0.02, ax.get_ylim()[1] * 0.93, f"Eg={eg:.4f} eV", color="#1d4ed8", fontsize=7)
    ax.set_xlabel("Photon energy hν (eV)")
    ax.set_ylabel(y_label)
    ax.set_title(title, fontsize=8)
    ax.grid(False)
    ax.legend(frameon=False, fontsize=6.8, loc="best")


def _build_report_markdown(
    parsed: dict,
    summary: dict,
    summary_json_path: Path,
    output_dir: Path,
    generated_tauc: list[Path],
) -> str:
    source_name = Path(str(summary.get("source_file", "analysis"))).name
    source_stem = Path(source_name).stem
    figure_root = output_dir.parent
    overview_pdf = figure_root / f"{source_stem}.pdf"
    overview_png = figure_root / f"{source_stem}.png"
    source_dataset = str(summary.get("source_file", ""))

    samples = summary.get("samples", [])
    sample_count = int(summary.get("sample_count", len(samples)))
    if samples:
        wmin = min(float(item["wavelength_range_nm"][0]) for item in samples)
        wmax = max(float(item["wavelength_range_nm"][1]) for item in samples)
        step_values = [float(item["step_nm"]) for item in samples]
        step_nm = float(np.median(step_values))
    else:
        wmin = 0.0
        wmax = 0.0
        step_nm = 0.0

    batch_meta = parsed.get("batch_metadata", {})
    signal_label = str(batch_meta.get("光度值类型", "") or "unknown")
    ranking = summary.get("batch_ranking_by_peak_absorbance", [])
    ranked_lines: list[str] = []
    for idx, item in enumerate(ranking, start=1):
        ranked_lines.append(
            f"{idx}. 样品 `{item['sample_id']}`，峰值 {float(item['peak_absorbance']):.6f}（{float(item['peak_wavelength_nm']):.1f} nm）"
        )

    grouped_statement = "当前批次样品数不足，暂不形成样品间对比判断。"
    if len(ranking) >= 2:
        top = ranking[0]
        second = ranking[1]
        shift = float(second["peak_wavelength_nm"]) - float(top["peak_wavelength_nm"])
        shift_word = "红移" if shift > 0 else ("蓝移" if shift < 0 else "无明显位移")
        grouped_statement = (
            f"峰值最强样品 `{top['sample_id']}` 相比样品 `{second['sample_id']}` 高 "
            f"{float(top['peak_absorbance']) - float(second['peak_absorbance']):.6f}，"
            f"峰位对比呈 {shift_word} 趋势（{shift:+.1f} nm）。"
        )

    results_lines: list[str] = [
        f"本批次数据来自 `{source_dataset}`，共包含 `{sample_count}` 个有效样品。",
        f"测试窗口为 `{wmin:.1f}-{wmax:.1f} nm`，步长 `{step_nm:.1f} nm`，信号模式为 `{signal_label}`。",
        "从整体谱图看，样品在可见光到近红外区表现出可分辨的吸收/反射差异，可用于样品间对比分析。",
        "",
        "峰值排序如下：",
    ]
    if ranked_lines:
        results_lines.extend([f"- {line}" for line in ranked_lines])
    else:
        results_lines.append("- 无可用峰值排序信息。")
    results_lines.extend(
        [
            "",
            f"样品组对比显示：{grouped_statement}",
            "",
            "| 样品 | 主峰位置 (nm) | 主峰强度 | Edge Marker (nm) | Direct Eg (eV) | Indirect Eg (eV) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for sample in samples:
        eg = sample.get("eg_assessment", {})
        results_lines.append(
            f"| `{sample['sample_id']}` | {float(sample['peak_wavelength_nm']):.1f} | {float(sample['peak_absorbance']):.6f} | "
            f"{float(sample['edge_marker_nm']):.1f} | {_format_optional(eg.get('selected_direct_eg_ev'))} | "
            f"{_format_optional(eg.get('selected_indirect_eg_ev'))} |"
        )

    results_lines.extend(
        [
            "",
            "关键图像如下（已嵌入最终报告）：",
            f"![批次总览图](<{_to_abs_md(overview_png)}>)",
        ]
    )

    tauc_png_files = [path for path in generated_tauc if path.suffix.lower() == ".png"]
    if tauc_png_files:
        for file_path in sorted(tauc_png_files):
            stem_name = file_path.stem
            sample_label = stem_name.replace("-tauc", "")
            results_lines.append(f"![样品 {sample_label} 的 Tauc 图](<{_to_abs_md(file_path)}>)")

    discussion_lines = [
        "本批次数据表明样品之间存在可比较的光学响应差异，主要体现在主峰强度与峰位位置的变化。",
        "若样品给出了可用的直接/间接带隙估计值，则这些 Eg 结果可作为样品筛选、配方对比和趋势判断的依据。",
        "需要强调的是，当前结论以 UV-Vis/DRS 光谱证据为基础；对于机理归因、相结构指认或化学态解释，仍建议结合 XRD、XPS 或成分分析进行交叉验证。",
        "当谱图存在噪声、基线漂移或线性区重叠时，Eg 数值应按“区间一致性”优先解读，而不是过度放大单一样品的末位差异。",
    ]

    title = f"# 紫外可见近红外漫反射分析报告 - {source_stem}"
    body = [
        title,
        "",
        "## Results",
        "",
        *results_lines,
        "",
        "## Discussion",
        "",
        *discussion_lines,
        "",
    ]
    return "\n".join(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_json")
    parser.add_argument("summary_json")
    parser.add_argument("output_dir")
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    summary = json.loads(Path(args.summary_json).read_text(encoding="utf-8"))
    summary_map = {item["sample_id"]: item for item in summary["samples"]}

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_tauc_files: list[Path] = []
    for sample in parsed["samples"]:
        sample_id = sample["sample_id"]
        info = summary_map.get(sample_id)
        if info is None:
            continue
        eg = info.get("eg_assessment", {})
        if eg.get("decision") != "compute_eg":
            continue

        x = np.asarray([p["wavelength_nm"] for p in sample["points"]], dtype=float)
        y = np.asarray([p["absorbance"] for p in sample["points"]], dtype=float)
        mode, _ = infer_signal_mode(sample.get("metadata", {}))
        hv, y_indirect, y_direct = _prepare_tauc_axes(x, y, mode)
        if len(hv) == 0:
            continue

        fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
        direct_candidate = (eg.get("direct_candidates_ev") or [None])[0]
        indirect_candidate = (eg.get("indirect_candidates_ev") or [None])[0]

        _plot_panel(
            axes[1],
            hv,
            y_direct,
            direct_candidate,
            title=f"{sample_id} Direct Tauc",
            y_label="(Ahν)^2 (a.u.)",
        )
        _plot_panel(
            axes[0],
            hv,
            y_indirect,
            indirect_candidate,
            title=f"{sample_id} Indirect Tauc",
            y_label="(Ahν)^1/2 (a.u.)",
        )
        fig.suptitle(f"Tauc Plot - Sample {sample_id}", fontsize=9)
        stem = output_dir / f"{sample_id}-tauc"
        pdf_path = stem.with_suffix(".pdf")
        png_path = stem.with_suffix(".png")
        fig.savefig(pdf_path)
        fig.savefig(png_path, dpi=300)
        generated_tauc_files.extend([pdf_path, png_path])
        plt.close(fig)

    source_name = Path(str(summary.get("source_file", "analysis"))).name
    source_stem = Path(source_name).stem
    dataset_folder = Path(args.summary_json).parent.name
    report_dir = Path.cwd() / "workspace" / "reports" / dataset_folder
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{source_stem}.report.md"
    report_markdown = _build_report_markdown(
        parsed=parsed,
        summary=summary,
        summary_json_path=Path(args.summary_json),
        output_dir=output_dir,
        generated_tauc=generated_tauc_files,
    )
    report_path.write_text(report_markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
