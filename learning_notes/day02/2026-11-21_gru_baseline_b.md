# 2026-11-21｜GRU Baseline B正式实验

本页是工程事实与待理解问题，不冒充学生原答或教师新结论；历史Lesson01–02及CNN笔记保持不变。

先审计真实CNN源码、config、stdout/CSV、环境与哈希，再复用数据、标准化、种子42、Adam全参数、batch64、lr.001、FP32 CPU2线程、max30/patience8及验证选模。只换单层单向GRU9→64和最终h_n[-1]→Linear64→6；输入[B,128,9]，不是为匹配CNN修改数据。实际参数14790，两套GRU偏置需都计入。

训练30轮，最佳Epoch23，验证Macro-F1 95.7862%；最佳权重最终测试Accuracy 91.8222%、Macro-F1 91.9444%。best/last可重载，固定验证probe差0，测试仅一次。[完整报告](../../reports/gru_baseline_seed42_20261121_run01/execution_report.md) · [CNN对比](../../reports/gru_baseline_seed42_20261121_run01/cnn_gru_comparison.md)。

## 三个最值得理解的知识点

1. h_n[-1]是单层GRU最后状态，在本例等于sequence_output[:,-1,:]；它不是沿时间平均，也不是CNN的9路输入通道。
2. 公平对比要恢复真实运行配置，包括Adam默认选项、AMP、裁剪和DataLoader；相同seed不代表不同模型有相同初始化权重。
3. 验证选模和测试报告角色分开；Early Stopping按共同规则执行，不能因看到测试差异再换种子或配置。

CNN是局部卷积+下采样+时间均值，GRU是递归状态+末状态。参数量差异和本次指标差异可直接观察；不能据单次结果断言某机制导致改善。困难类别双向错误及F1需要一起看，不能只看Accuracy。[每类与错误分析](../../reports/gru_baseline_seed42_20261121_run01/cnn_gru_comparison.md)。

## 不足与下一步问题

单种子、固定人员划分，不含稳定性或跨数据集证明；CPU指纹历史记录不完整，计时范围不同也不支持严格速度比；没有单独推理计时。最明显的混淆以实际矩阵为准。后续可由教师决定多种子或按人员分析；本轮不追加调参、其他模型或消融。

训练无异常、未修复后重训；TypedStorage弃用警告不影响执行。机械绘图门禁缺失如实记载。没有新的学生作答或教师批改，不标教学问题已通过。
