# 第四次学习规划最终归档

[中文研究报告 PDF](report.pdf) · [LaTeX 源文](report.tex) · [48 题映射](question_mapping.csv) · [项目进度](../../PROGRESS.md)

## 原题与教师记录

48 道题逐项摘自原规划 `第四次学习规划.pdf` 第 12–15 页。原版每组印刷编号 1–6，全局题号按章节范围补齐为 1–48，CSV 保留原组内编号、标题、页码和题面。提供的两份 Markdown 为主题学习笔记，题面来自 PDF。

教师总评 **48/48 通过**和 GRU Task03 结果理解通过均据本次任务提供的验收说明登记。已找到 4 条 Day 01 同主题历史逐字原答（对应第 4、5、10、12 题，教师验收问句与 PDF 题面有差异），其余 44 题以归档成果支撑整理答案。48 道答案均作为归档整理，逐字引用单列。第 5、14、24、32、35 和 48 题的定向验收按提供的摘要登记。摘要所称第 24 题主题与 PDF 第 23 题吻合，PDF 第 24 题涉及任务、模型家族与具体代表的区别，台账保留这一题号差异。未恢复的逐字问答、批改和复测记录在逐题台账注明。[历史 Day 01 原文索引](../../learning_notes/day01/questions_01_12.md)

## 实验与审计

| 内容 | 归档 |
| --- | --- |
| 四个 Seed42 基线 | [数值 CSV](four_models.csv) · [四模型原档案](../../experiments/mamba_baseline_d_seed42_20261122/reports/four_model_comparison.md) |
| CNN 九组消融 | [配对 CSV](cnn_ablation.csv) · [九组原始结果](../cnn_ablation_20261122/results.csv) · [A42 与 B42/C42 的指纹来源](../chapter06_lesson02_task01_revision/README.md) |
| Task03 GPU 三种子 | [数值 CSV](gru_task03.csv) · [三种子比较](../gru_multiseed_task03_20261123/comparison.md) · [工程验收](../gru_multiseed_task03_20261123/acceptance.md) |
| 核验与来源 | [Skill 执行](skill_usage.md) · [输入证据清单](evidence_manifest.json) · [核验结果](verification.json) · [发布 SHA-256](SHA256SUMS) |

四模型与九组消融共 12 个独立运行（共用 A42），另加 Task03 三组。表格从各运行归档数值生成。复用原始四模型／消融矢量图及 Task03 混淆矩阵，无新的模型运行。Task03 的 60 项清单中，公开副本的 18 项可直接核对，剩余 42 项仅有服务器历史校验记录。Best/Last 哈希在运行结果和清单内一致。服务器访问失败，未重算其实际权重和预测文件的哈希。

## 复编

从本目录执行两轮 XeLaTeX。中文字体使用 Windows 系统宋体和黑体，或 TeX 的 Fandol 字体。保留相邻报告目录以便引用原图。测试和编译证据见核验结果。

```powershell
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex
pdfinfo report.pdf
pdftoppm -r 115 -png report.pdf preview
```

本归档基于 Task03 提交 `7a3dc521cbe31011be89e215177c135cebe410ce`。发布提交可用 `git log --diff-filter=A --format=%H -- reports/fourth_plan_final_archive_20261123/report.pdf` 查询。

`SHA256SUMS` 以发布提交的 Git 文件字节为准，覆盖本次全部交付文件（清单自身除外），路径相对仓库根目录。启用自动换行转换的检出可通过 `git show <发布提交>:<路径>` 读取原始 Git 内容再核对哈希。
