---
name: uci-har-experiment-workflow
description: Audit or summarize archived SequenceModel-HAR-Lab runs, generate a Chinese LaTeX/PDF research report and figures, or route a separately authorized UCI HAR training run to an existing entry point.
---

# UCI HAR 实验工作流

先判定任务是只读核验、报告汇总还是用户明确授权的新训练。从仓库根目录先读取[数据协议](../../../docs/data_protocol.md)，再查 [实验注册表](../../../docs/experiment_registry.md) 和 [报告入口](../../../reports/README.md)。审计当前 HEAD、配置和证据来源后按任务范围执行。只读核验直接比较公开归档、冻结哈希及指标来源，保留原数据、分割、配置、历史运行与 Checkpoint。

## 汇总与报告

1. 从仓库根目录读取 [数据协议](../../../docs/data_protocol.md) 和 [报告入口](../../../reports/README.md)。记录 Git HEAD、状态，以及请求中指定的实验来源。服务器已有公开归档时，从对应 Git 提交核验；直接服务器核验需要已授权的访问入口。
2. 用具备 Matplotlib 的 Python 运行 `python -B scripts/build_har_research_report.py --output reports/<新目录>`。它从原运行的指标、配置和模型摘要核对四个 Seed42 基线和九个消融位置，复用 A42，核对混淆矩阵与类别指标、配对 CSV 和样本标准差，并调用 `scripts/fig05_har_research.py` 生成同源图。保留输入 SHA-256、制表 CSV 与图的 PDF、PNG、SVG。脚本失败时保留失败信息，解决数据差异后用新目录重试。
3. 在报告目录运行两遍 `xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex`。模板使用 Windows 的字体文件或 TeX 的 Fandol 字体。用 Poppler 将全部页面渲染成 PNG，逐页检查表宽、列对齐、图中文字、引用和分页。记录命令、退出码、脚本、输入、生成物、检查结论。
4. Macro-F1 为六类 F1 的算术平均。归档 Loss 来自原模型；混淆矩阵不能复算交叉熵。对比种子使用百分点和样本标准差。固定划分上的三个种子不能代表其他划分，单种子无法支持模型家族的一般排名。CPU 与 CUDA 的计时缺少共同条件。

## 新训练入口

只在任务明确授权新运行时进入。使用冻结的 `data/processed/day01_data_20261026_run02_audit02`，先核验 6037/1315/2947 窗口、受试者互斥、官方 1–6 标签加载时映射为 0–5，以及由最终训练集拟合的既有标准化参数。配置、入口与审计证据见 [训练脚本索引](../../../scripts/README.md) 和 [Mamba 环境及运行说明](../../../experiments/mamba_baseline_d_seed42_20261122/README.md)。

- CNN A：`python -B scripts/train_cnn_baseline_a.py <audit|preflight|train> <新运行ID>`，阶段顺序为 audit、preflight、train。
- GRU B / Transformer C：`python -B scripts/train_gru_baseline.py <新运行ID>` 或 `python -B scripts/train_transformer_baseline.py <新运行ID>`，各自包含预检查。
- CNN 消融：`python -B scripts/train_cnn_ablation.py <A|B|C> <42|43|44> <新运行ID>`，按 [配对协议](../../../reports/cnn_ablation_20261122/reproducibility.md) 核对共享初始化和顺序。
- Mamba D：使用官方 CUDA 环境及归档入口 `scripts/check_cuda.py`、`scripts/run_mamba.py`、`scripts/verify_and_compare.py`，参数见对应实验说明。

使用新的 Run ID 与输出目录。先过环境和真实 Batch 门禁，再按已存配置以验证 Macro-F1 选模，同分比较验证 Loss。最佳模型重载通过后只做一次预定测试。保留实际配置、提交、种子、训练历史、测试指标、逐类指标、混淆矩阵、重载、原始日志及预测和相应 SHA-256。权重、原始日志和受控预测留在运行环境。既有 `verify_*.py` 可能默认写入历史目录，核对参数与写入目标后再执行。

## 核验与归档

回查输入 SHA-256 和历史 Git 差异。完成正式归档后更新实验注册表及报告索引。分别登记同期记录、重建记录和历史原件缺口；证据不全标 PARTIAL。运行项目测试、文档检查及暂存区审查。仅按授权提交源码、公开配置、汇总指标及报告，通过正常推送核对远程 SHA。通过 Skill 构建报告、发起训练和自动加载完整指令分别记证据。
