---
name: xrf-analysis
description: Analyze XRF result bundles, extract oxide semi-quantitative tables and line-scan traces, and deliver a researcher-facing combined report with embedded figures and conservative composition interpretation.
allowed-tools: Bash, Read, Write, Edit
---

# XRF Analysis

Use this skill for XRF result bundles such as `.rar`, extracted folders, `.csv`, and vendor-exported PDF companions. Keep conclusions tied to the exported composition table and scan trace. Do not infer crystalline phase, mineral identity, or certified quantitative composition unless the file explicitly provides that evidence.

## Inputs

- Raw XRF files such as `.rar`, extracted directories, `.csv`, `.pdf`
- Optional instrument notes under `instruments/generic-xrf-analysis/`
- Optional expert Q/A under `datasets/generic-xrf-analysis/`

## Workflow

1. Read `references/file-format.md` before parsing an unfamiliar export.
2. Run `scripts/parse_xrf_bundle.py` on the archive or extracted sample folder to extract metadata, the semi-quantitative oxide table, and the scan trace into canonical JSON.
3. Run `scripts/summarize_xrf.py` on the parsed JSON to compute major components, low-level components, scan range, and interpretation warnings.
4. Read `references/data-structure.md` and `references/interpretation-guide.md` before writing conclusions.
5. Report:
   - available metadata and missing metadata
   - the dominant oxide components ranked by reported `mass%`
   - low-level or near-threshold components that require caution
   - the exported scan label, axis range, point count, and relative intensity range
   - interpretation limits, especially where XRF is being mistaken for XRD or mineral phase analysis
6. Apply report-delivery constraints for final handoff:
   - analyze every valid sample in the selected dataset or folder
   - default output is one combined report for the full batch; create per-sample reports only when explicitly requested
   - treat the final Markdown report as the primary deliverable; parsed JSON and temporary notes are support artifacts
7. Draft the final report in `output/reports/generic-xrf-analysis/` with `assets/report-template.md`. Write in a researcher-facing tone (suitable for materials-chemistry researchers as the primary reader); avoid developer/parser narration.
8. Prepare key figures for each analyzed sample and embed them in the report body:
   - prioritize exported companion figures when available and scientifically relevant
   - default figure type is composition-focused (for example ranked oxide composition chart)
   - do not generate standalone scan-trace figures unless the user explicitly requests scan plotting
   - use Markdown image syntax with absolute local file paths for every embedded figure
9. Keep the report free of developer-facing wording (JSON dumps, parser/debug narration, script internals, file index lists).

## Output rules

- Quote numeric values with units exactly as the export uses them.
- State clearly whether a value comes from the semi-quantitative table or the scan trace.
- Treat the semi-quantitative table as composition evidence, not phase proof.
- Separate observations from interpretation.
- Use conservative wording such as `reported as`, `detected at`, `suggests`, `consistent with`, or `cannot confirm`.
- Default output format is Markdown with:
  - a sample-info table (exclude operator and source path unless explicitly requested)
  - a composition table ranked by `mass%`
  - an interpretation summary section after the tables
  - embedded key figures with absolute local paths
- Default report language is Chinese. Switch to English only when the user explicitly requests English.
- Final delivery default is one combined Markdown report that covers all valid samples in the selected folder.
- The report must include: sample/experiment context, test-result overview, ranked composition table, low-level component caution, scan-trace overview, scientific interpretation, and concise conclusion with method boundaries.
- When completing the task, return the final report path, key figure paths, whether combined reporting was used, and a short Chinese finding summary unless the user requests another language.
- If the user asks for Chinese output, use Chinese headings and Chinese narrative while keeping numeric values and units unchanged.

## Preferred markdown structure

When generating a user-facing report, follow this structure:

1. `## XRF测试结果汇总（半定量）`
2. `### 样品信息` table with:
   - `样品编号`
   - `测试模式/标签`
   - `测试时间`
   - `结果性质` (for example `XRF半定量（单位：mass%）`)
3. `### 氧化物组成（按含量降序）` table:
   - `排名`
   - `组分`
   - `含量（mass%）`
4. `## 分析摘要`
   - overall composition behavior
   - dominant components
   - low-level components with cautious wording
   - interpretation limits (XRF composition vs phase identity)
5. `## 关键谱图`
   - embed key figures with absolute local paths using Markdown image syntax
6. `## 结论与边界`
   - concise conclusion
   - method boundaries and uncertainty notes

## Reference map

- Instrument context: `references/instrument-profile.md`
- File structure and parsing rules: `references/file-format.md`
- Parsed and summary schemas: `references/data-structure.md`
- Interpretation logic and wording limits: `references/interpretation-guide.md`

## Limits

- Do not convert XRF oxide percentages into definitive mineral or crystalline phase assignments.
- Do not treat a line-specific scan trace as an XRD diffractogram.
- Do not claim certified bulk composition accuracy from one semi-quantitative export.
- Flag near-threshold components clearly when the reported value is close to the detection limit.
