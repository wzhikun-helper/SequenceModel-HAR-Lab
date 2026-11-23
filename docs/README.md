# 文档导航

1. [项目概览](../README.md) · [English](../README.en.md)。
2. [数据协议](data_protocol.md) · [信号图与冻结元数据](day01/README.md)。
3. 环境准备。数据流程见 [Day 01 指南](reproducing_day01.md)，CPU 基线依赖见 [requirements-cnn.txt](../requirements-cnn.txt)，CUDA 分别见 [Mamba](../experiments/mamba_baseline_d_seed42_20261122/docs/environment.md) 和 [Task03 环境快照](../reports/gru_multiseed_task03_20261123/input_audit.json)。
4. 模型实现。[CNN](../src/har_lab/cnn_baseline_a.py) · [GRU](../src/har_lab/gru_baseline_b.py) · [Transformer](../src/har_lab/transformer_baseline_c.py) · [Mamba](../experiments/mamba_baseline_d_seed42_20261122/src/mamba_baseline_d.py) · [CNN 消融](../src/har_lab/cnn_ablation.py)。
5. [实验注册表](experiment_registry.md)。查找运行、配置、历史、指标、权重记录和环境。
6. [复现与执行入口](../scripts/README.md) · [Task03 协议](gru_task03_protocol.md) · [测试范围](verification.md)。
7. [报告总索引](../reports/README.md) · [第四次学习规划最终报告](../reports/fourth_plan_final_archive_20261123/report.pdf)。

[权威进度](../PROGRESS.md) · [归档勘误](fourth_plan_archive_errata.md) · [整理前审计](repository_audit_20261123.md) · [开源组织参考](project_organization_references.md)
