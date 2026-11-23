# Task 03 · GRU GPU 三种子

2026-11-23 UTC。正式训练准入十项全通过。依次完成 Seed42、43、44，分别使用由验证集选中的 Best 权重对官方测试集执行一次模型评价。已复算三份预测、校验全部权重与运行文件。等待教师验收。

[准入结果](admission.json) · [历史配置与新配置](../../docs/gru_task03_protocol.md) · [环境与输入审计](input_audit.json) · [真实 Batch 检查](integrated_preflight.json) · [Skill 记录](skill.md) · [启动检查恢复](recovery.md)

[三种子比较](comparison.md) · [机器可读汇总](summary.json) · [训练曲线](training_curves.png) · [混淆矩阵](confusion_matrices.png) · [逐类指标](class_metrics.png)

| Seed | 实际配置 | 训练历史 | 测试 | 独立复算 | 文件哈希 |
| ---: | --- | --- | --- | --- | --- |
| 42 | [YAML](seed42/config.yaml) | [CSV](seed42/training_history.csv) | [指标](seed42/test_metrics.json) · [类别](seed42/classification_report.csv) | [JSON](seed42/independent_verification.json) | [SHA256SUMS](seed42/SHA256SUMS) |
| 43 | [YAML](seed43/config.yaml) | [CSV](seed43/training_history.csv) | [指标](seed43/test_metrics.json) · [类别](seed43/classification_report.csv) | [JSON](seed43/independent_verification.json) | [SHA256SUMS](seed43/SHA256SUMS) |
| 44 | [YAML](seed44/config.yaml) | [CSV](seed44/training_history.csv) | [指标](seed44/test_metrics.json) · [类别](seed44/classification_report.csv) | [JSON](seed44/independent_verification.json) | [SHA256SUMS](seed44/SHA256SUMS) |

服务器独立保存每种子的权重、原始 stdout、含 logits 的逐样本预测和单独混淆图。公开 SHA256SUMS 记录这些服务器文件的哈希。历史 Windows stdout 和原权重在服务器未找到。历史运行的逐轮表、配置与指标可按原清单复核，恢复 CRLF 后字节一致。

[实验验收](acceptance.md)
