# 实验报告与证据索引

按实验类别查找原始运行档案、后续复核和派生产物。最新验收状态见 [PROGRESS](../PROGRESS.md)；每个运行的完整性、配置和 Checkpoint 记录见 [实验注册表](../docs/experiment_registry.md)。

| 类别 | 原始归档或执行依据 | 复核和派生成果 |
| --- | --- | --- |
| 数据获取与审计 | [来源](day01_data_20261026_run02/download_provenance.json) · [最终审计 audit02](day01_data_20261026_run02/day01_data_audit.md) | [逐值独立复核](day01_data_20261026_run02/independent_verification.json) · [真实信号图](../docs/day01/README.md) |
| 数据独立复现 | [独立环境和执行记录](remediation_round1_20261031/README.md) · [独立下载记录](day01_repro_20261031_run01/download_provenance.json) | [复现验证](day01_repro_20261031_run01/independent_verification.json) · [两次比较](remediation_round1_20261031/comparison/comparison.json) |
| CNN Baseline A | [正式运行](cnn_baseline_seed42_20261119_run01/execution_report.md) · [最小工程](day02_cnn_20261111_run01/README.md) | [独立复算](cnn_baseline_seed42_20261119_run01/independent_result_verification.json) · [混淆矩阵](cnn_baseline_seed42_20261119_run01/confusion_matrix.png) |
| GRU Baseline B | [正式运行](gru_baseline_seed42_20261121_run01/execution_report.md) · [前置审计](gru_baseline_preflight_20261121/audit_report.md) | [独立复算](gru_baseline_seed42_20261121_run01/independent_verification.json) · [CNN 与 GRU](gru_baseline_seed42_20261121_run01/cnn_gru_comparison.md) |
| Transformer Baseline C | [正式运行](transformer_baseline_seed42_20261122_run01/execution_report.md) · [前置审计](transformer_preflight_20261122/audit_report.md) | [独立复算](transformer_baseline_seed42_20261122_run01/independent_verification.json) · [三模型比较](transformer_baseline_seed42_20261122_run01/three_model_comparison.md) |
| Mamba Baseline D | [Linux CUDA 正式运行](../experiments/mamba_baseline_d_seed42_20261122/README.md) | [独立复算](../experiments/mamba_baseline_d_seed42_20261122/reports/independent_verification.json) · [四模型比较](../experiments/mamba_baseline_d_seed42_20261122/reports/four_model_comparison.md) |
| CNN SE 消融 | [九组原始指标入口](cnn_ablation_20261122/results.csv) · [前置审计](cnn_ablation_audit_20261122/README.md) | [完整报告](cnn_ablation_20261122/README.md) · [A42 重建与 B42/C42 直录](cnn_ablation_20261122/independent_seed42.json) · [配对图](cnn_ablation_20261122/paired_differences.png) |
| GRU Task03 | [三种子运行入口、配置、日志表和清单](gru_multiseed_task03_20261123/README.md) | [独立复算与工程验收](gru_multiseed_task03_20261123/acceptance.md) · [汇总与混淆矩阵](gru_multiseed_task03_20261123/comparison.md) |
| 第四次学习规划 | [最终归档](fourth_plan_final_archive_20261123/README.md) · [48 题台账](fourth_plan_final_archive_20261123/question_mapping.csv) | [最终 PDF](fourth_plan_final_archive_20261123/report.pdf) · [历史初稿](chapter06_lesson01_research_draft/README.md) · [A42 证据修订](chapter06_lesson02_task01_revision/README.md) · [独立勘误](../docs/fourth_plan_archive_errata.md) |
| 历史失败与整改 | [首次下载失败](day01_data_20261026_run01/download_provenance.json) · [首次序列化失败](day01_data_20261026_run02/audit/FAILED_ATTEMPT_DO_NOT_USE.txt) · [Mamba 早期 L0](mamba_l0_20261122/README.md) · [Task03 恢复](gru_multiseed_task03_20261123/recovery.md) | [整改与复现](remediation_round1_20261031/README.md) · [Day 01 启动](day01_startup_check.md) · [同步前检查](day01_github_preflight_20261028_run01/preflight.md) · [同步回执](day01_github_sync_20261028_run01/sync_receipt.md) |

## 公开证据和本地原件

- CSV 历史、配置和测试指标用于追溯原运行。复算 JSON 是后续依据冻结预测、标签或归档记录进行的核对。统计、图和 PDF 是派生产物。
- 原始数据与运行权重、机器 stdout 和大体积预测文件应留在当地。Task03 的逐样本预测与检查点原件在服务器。60 项文件清单中 **18 项公开副本可直接复核，42 项服务器文件尚未独立重新核验（PARTIAL）**。
- 失败记录保留原含义。Day 01 的 `audit/` 为首次序列化失败现场；有效结果在 `audit02/`。历史 Git 状态和机器路径按归档时间解读。[课程原始归档](day01_archive_20261028_run01/archive_report.md)

[PR #1 最终交付清单](repository_organization_20261123/final_release_checklist.md) · [公开安全审计](repository_organization_20261123/security_audit.md) · [新会话 Skill 复核](repository_organization_20261123/skill_verification.md)
