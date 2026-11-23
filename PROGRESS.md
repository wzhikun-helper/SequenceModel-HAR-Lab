# 项目进度

更新日期：2026-11-23。当前阶段 **第六章 Lesson 02 · Task 01 文档修订完成，等待复核。**

## 实验进度

| 阶段 | 状态 | 交付 |
| --- | --- | --- |
| 数据获取与审计 | 已完成 | 官方来源、压缩包 CRC、本地 SHA-256、窗口与标签检查 |
| 受试者划分 | 已完成 | 17 人训练 / 4 人验证 / 9 人测试，人员不重叠 |
| 预处理 | 已完成 | 最终训练集拟合标准化参数；三集合使用同一参数 |
| 真实信号观察 | 已完成 | WALKING、STANDING 各一个九路窗口 |
| 学习验收 | 第三章 12/12 通过 | 教师确认的[最终笔记](learning_notes/day01/2026-10-28_teacher_final_notes.md) |
| CNN最小工程 | 本地执行通过，待教师验收 | 六个真实训练窗口、前向/反向、未训练权重本地保存与重载一致；无优化器更新 |
| CNN Baseline A | 已执行，待教师验收 | Seed42，最佳Epoch7，15轮Early Stopping；测试Accuracy 89.7523% / Macro-F1 89.8202% |
| GRU Baseline B | 已执行，待教师验收 | Seed42，最佳Epoch23，实际30轮；测试Accuracy 91.8222% / Macro-F1 91.9444% |
| Transformer C | 已执行，待验收 | 最佳Epoch7，实际15轮；测试Accuracy 88.0896% / Macro-F1 88.0326% |
| CNN SE / 等参数残差 MLP 消融 | 已执行，待教师验收 | 三组 × Seed 42、43、44，复用历史 A42。[完整报告](reports/cnn_ablation_20261122/README.md) |
| Mamba D | 已执行，待教师验收 | RTX 3090，最佳第 3 轮，实际 11 轮。官方测试 Accuracy 88.7004% / Macro-F1 88.8610%。[实验档案](experiments/mamba_baseline_d_seed42_20261122/README.md) |
| 第六章 Lesson 01 | 已执行报告调用，待教师验收 | [项目 Skill](.agents/skills/uci-har-experiment-workflow/SKILL.md)生成中文科研报告初稿。通过 Skill 发起正式训练仍待执行。[课程记录](learning_notes/chapter06_lesson01.md) |
| 第六章 Lesson 02 · Task 01 | 文档修订完成，Task 02 待开始 | [修订报告与证据](reports/chapter06_lesson02_task01_revision/README.md)明确 A42 重建与 B42/C42 直接记录的区别，补充 Skill、脚本与实验记录的定义。 |

训练集 6,037 窗口，验证集 1,315 窗口，测试集 2,947 窗口。[协议与元数据](docs/data_protocol.md) · [数据独立复核](reports/day01_data_20261026_run02/independent_verification.json)。

## 里程碑

| 日期 | 事项 |
| --- | --- |
| 2026-10-26 | 完成环境检查、UCI HAR 数据实践与独立产物复核。 |
| 2026-10-28 | 归档最终笔记和可恢复问答；初始化 main，完成首批 GitHub 同步及哈希核验。 |
| 2026-10-30 | 整理公开首页、数据协议、复现指南与历史档案导航，增加文档入口检查。 |
| 2026-10-31 | 收紧首页信息层次，增加英文概览、贡献约定、更新记录与自动文档检查。 |
| 2026-10-31（第一轮整改） | 独立venv与新ID完成真实数据全流程复现及旧结果对比；新增25个轻量共享契约测试，复核问答证据类型。 |
| 2026-11-11 | 教师确认Lesson 01–02理论通过；完成CNN真实样本最小工程，保存实际命令、损失、梯度与重载证据；取回五轮教学原文。 |

2026-10-28 已核验的同步提交为 `b6ac9ced33474068f69f4505d38a01222a9e6562`；这只是当日快照，不作为后续最新提交的固定值。[当日同步回执](reports/day01_github_sync_20261028_run01/sync_receipt.md)。

## 2026-11-19正式训练证据

[完整报告](reports/cnn_baseline_seed42_20261119_run01/execution_report.md) · [配置/CSV/图表](reports/cnn_baseline_seed42_20261119_run01/README.md) · [学习补充](learning_notes/day02/2026-11-19_cnn_baseline_a.md)。数据划分、标准化与.gitignore未改，测试不选模。

## 2026-11-21 GRU证据

先审计CNN实际配置，再执行GRU；[审计报告](reports/gru_baseline_preflight_20261121/audit_report.md) · [完整实验](reports/gru_baseline_seed42_20261121_run01/execution_report.md) · [CNN对比](reports/gru_baseline_seed42_20261121_run01/cnn_gru_comparison.md) · [学习补充](learning_notes/day02/2026-11-21_gru_baseline_b.md)。原CNN成果和.gitignore未改。

## 2026-11-22 Transformer证据

[完整报告](reports/transformer_baseline_seed42_20261122_run01/execution_report.md) · [三模型比较](reports/transformer_baseline_seed42_20261122_run01/three_model_comparison.md) · [学习补充](learning_notes/day02/2026-11-22_transformer_baseline_c.md)。只读旧实验，数据、标准化及.gitignore不变。

## 学习记录的完整性

教师确认第三章正式理解题 12/12 通过。现存教学原文只覆盖原题 4、5、10、12 及 3.2 节的局部读图问答；其余八题的学生原答和逐题批改未取回。验收结论与原始记录完整性分别记录，不用教师解释补造学生回答。[问答索引](learning_notes/day01/questions_01_12.md)。

Day 01已结课；本轮用户明确授权Day 02 CNN最小工程。教师后续阶段准入仍由教师决定，工程自检不等于正式训练或教师验收。[Day 02学习记录](learning_notes/day02/README.md) · [工程报告](reports/day02_cnn_20261111_run01/README.md)。

## 第一轮整改结果

- 完整真实数据复现：通过；官方下载、审计/标准化、绘图、磁盘逐值验证全部退出0。三集合数组完全相同、训练均值/标准差差值为0、两张PNG像素一致。
- 轻量测试：25个合成契约测试在禁用site packages的独立Python中通过；共享逻辑接入真实流程、文档检查和既有CI，未另建数据下载CI。
- 图表差异：PDF/SVG文件字节不同，已保存生成时间差异及SVG路径/文本对比，不把数值一致混同为所有文件字节一致。
- 归档：新增逐字原文／教师摘要／缺失分类索引，本轮没有取得新增原始对话；12/12历史验收结论和原教学文本未改。
- 当时的证据与限制：[整改报告](reports/remediation_round1_20261031/README.md)。2026-10-31尚未进入第四章与Day 02；当前状态见本页顶部。本轮不改写历史报告。
