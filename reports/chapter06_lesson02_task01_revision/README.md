# 第六章 Lesson 02 · Task 01 报告证据修订

[修订版 PDF](report.pdf) · [本版 LaTeX](report.tex) · [原版 PDF](../chapter06_lesson01_research_draft/report.pdf) · [课程笔记](../../learning_notes/chapter06_lesson01.md)

## A42、B42、C42 的证据来源

原版写道：“同种子比较共享卷积与分类头的初值和训练读取顺序，A42 复用历史运行。”修订版在第 2 页分别注明训练时直接记录、历史指标及事后重建的来源。

| 运行 | 训练时直接记录 | 后续核对 |
| --- | --- | --- |
| A42 | 保留了 [训练历史](../cnn_baseline_seed42_20261119_run01/training_history.csv)、[配置](../cnn_baseline_seed42_20261119_run01/config.json)及[历史测试指标](../cnn_baseline_seed42_20261119_run01/test_metrics.json)。原训练未保存初始权重和逐轮批次顺序指纹 | 后续[审计](../cnn_ablation_audit_20261122/evidence.json)按原模型构造和 Seed42 配置重建初始化，在 [Seed42 独立复核](../cnn_ablation_20261122/independent_seed42.json)中按原数据加载器回放 15 轮顺序。A42 指标沿用历史结果 |
| B42 | [训练结果](../cnn_ablation_20261122/cnn_ablation_B_seed42_20261122_run01/training_result.json)保存共享部分的初始权重指纹，[训练历史](../cnn_ablation_20261122/cnn_ablation_B_seed42_20261122_run01/training_history.csv)保存 15 轮顺序指纹 | 初始共享权重指纹和 15 轮顺序均与重建匹配 |
| C42 | [训练结果](../cnn_ablation_20261122/cnn_ablation_C_seed42_20261122_run01/training_result.json)保存共享部分的初始权重指纹，[训练历史](../cnn_ablation_20261122/cnn_ablation_C_seed42_20261122_run01/training_history.csv)保存 13 轮顺序指纹 | 初始共享权重指纹和前 13 轮顺序均与重建匹配 |

共享初始权重的 SHA-256 为 `44e8f83f5c5bed58ad1d252fbd10c889aaa6237bd15eed2a4cdf08b2e2c977ee`。B42/C42 的逐轮指纹覆盖按训练中实际读取顺序依次写入的输入与标签张量字节。修订依据为训练时保存的 CSV/JSON、[原始训练入口](../../scripts/train_cnn_baseline_a.py)、[新运行写入逻辑](../../scripts/train_cnn_ablation.py)、[初始化审计](../../scripts/audit_cnn_ablation.py)和[加载器回放逻辑](../../scripts/verify_cnn_ablation.py)。本次只读取、核对既有证据。

## 编译与验证

本版使用[修订模板](../../scripts/templates/har_research_report.tex)，由 `ReportAssets` 直接引用[初稿归档](../chapter06_lesson01_research_draft/README.md)中的原始表格片段和矢量图。消融汇总与九组结果改为并排，保留两页版式。从本目录执行以下命令可复编，需与原报告目录保持相邻。

```powershell
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex
pdfinfo report.pdf
pdftoppm -r 115 -png report.pdf preview
```

- 实际使用 XeLaTeX（MiKTeX，追加 `-disable-installer`）编译两遍，均退出 0。A4 两页，Poppler 渲染退出 0。逐页确认中文、引用、数值对齐、图例和页码清晰，编译日志未检出箱体溢出、缺字、字体替代或未定义引用。
- 从原版与修订版 PDF 提取并对照 4 行基线、9 行消融和 3 行汇总，16 行均匹配。直接使用同一图文件，摘要和结论正文一致。39 项归档源与 4 项本地冻结数据的 SHA-256 复核通过。
- 项目文档检查及新增报告链接检查通过。标准库测试 25 项、PyTorch 测试 16 项通过。原始报告、实验产物、模型源码均保留。

工作止于 Lesson 02 Task 01。此轮没有训练或推理。新会话 Skill 自动发现与复用留待后续验证。
