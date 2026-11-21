# 文档导航

第一次浏览建议按以下顺序阅读：

1. [项目概览](../README.md)：当前成果、真实样本与计划范围。
2. [数据与评估协议](data_protocol.md)：输入形状、受试者划分、类别分布与标准化约定。
3. [Day 01 复现指南](reproducing_day01.md)：环境、命令顺序、输出位置与验证边界。
4. [真实信号与元数据](day01/README.md)：可直接在线查看的代表图和小型参数文件。

| 阅读目的 | 入口 |
| --- | --- |
| 理解监督分类、信号窗口与预处理 | [学习笔记](../learning_notes/day01/README.md) |
| 检查原始回答和理解修正 | [正式理解题索引](../learning_notes/day01/questions_01_12.md) |
| 核对数据实践的实际执行结果 | [报告与历史档案](../reports/README.md) |
| 查找可运行的数据脚本 | [脚本说明](../scripts/README.md) |
| 核验GRU及CNN对比 | [GRU报告](../reports/gru_baseline_seed42_20261121_run01/execution_report.md)、[CNN配置审计](../reports/gru_baseline_preflight_20261121/audit_report.md)、[对比](../reports/gru_baseline_seed42_20261121_run01/cnn_gru_comparison.md) |
| 确认当前阶段 | [项目进度](../PROGRESS.md) |
| 复核CNN Baseline A正式训练 | [报告](../reports/cnn_baseline_seed42_20261119_run01/execution_report.md)、[复现说明](../reports/cnn_baseline_seed42_20261119_run01/reproducibility.md) |
| 复现CNN最小真实样本工程 | [Day 02运行说明](day02_cnn.md)、[工程报告](../reports/day02_cnn_20261111_run01/README.md)、[学习原答](../learning_notes/day02/README.md) |
| 区分轻量CI与真实数据完整复现 | [验证层次与运行证据](verification.md) |
| English overview | [README.en.md](../README.en.md) |
| 查看版本演进与提交约定 | [更新记录](../CHANGELOG.md)、[贡献说明](../CONTRIBUTING.md) |

数据与训练状态以已有证据为准。当前没有模型训练结果，历史教学记录中的训练流程说明不等于执行记录。
