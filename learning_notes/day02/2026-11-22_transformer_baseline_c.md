# 2026-11-22｜Transformer C正式实验

工程事实与待理解问题，不冒充学生原答/教师批改。旧教学和基线记录不改。

Linear9→64，加固定正弦PE，单层Post-Norm Encoder(d64/head4/FF128/ReLU/p0)，时间均值后Linear64→6；34502可训练参数，PE的8192值是buffer。固定位置不学习，注意力及投影权重学习；没有CLS、额外归一化或输入缩放。

原数据/标准化/标签/seed42/Adam/batch64/CPU2线程/FP32/max30/patience8和验证选模均复用。预检查2真实Batch、梯度/更新/Checkpoint通过后完全重新初始化，并用初始哈希证明不带入检查更新。

实际15轮，最佳Epoch7，停止原因patience，验证Macro-F1 92.4534%；最佳模型一次测试Accuracy 88.0896%、Macro-F1 88.0326%。[完整报告](../../reports/transformer_baseline_seed42_20261122_run01/execution_report.md) · [三模型逐类/混淆/计时比较](../../reports/transformer_baseline_seed42_20261122_run01/three_model_comparison.md)。

需要理解：Post-Norm中残差与LayerNorm位置；固定正弦buffer与可训练参数的区别；时间均值与GRU最后状态的区别；验证选模/测试独立性；单种子与不同计时边界的结论限制。未提供新的学生作答，不标这些问题已通过。

辅助审计脚本编码启动差异保留失败证据，显式UTF8读取完成审计；正式模型训练无异常、不因表现改配置。Checkpoint/独立分类复核证据见报告，机械图表门禁缺失如实记录。后续由教师验收决定，未执行Mamba或消融，不宣布规划整体完成。
