# 2026-11-19｜CNN Baseline A正式训练补充

本页是工程事实与待讨论问题，不是学生原答或教师新批改。此前Lesson01–02理论原文和通过结论保持原样，本轮正式结果仍待教师验收。

## 模型与配置

[B,9,128]→Conv9→64→ReLU→MaxPool(2)→Conv64→128→ReLU→时间平均→Linear128→6。两层K3/S1/P1、带偏置，共27,270参数。MaxPool把时间128减至64，不增加参数。不同于11月11日无MaxPool、无更新的最小工程，本轮正式遍历全部训练窗口并执行Adam更新。

固定seed42、batch64、Adam lr0.001、max30、patience8、drop_last=False、CrossEntropyLoss，训练shuffle。验证和测试不更新参数；1–6标签只在内存减1；Day 01划分/标准化不改。

## 真实结果与观察

15轮Early Stopping，最佳Epoch7。验证Accuracy 94.9049%、Macro-F1 94.7690%、Loss 0.11746946686007677。Epoch14虽Loss更低，但Macro-F1低于第7轮，不替换最佳。连续8轮无选模改善后停止。

最佳模型官方测试一次：Accuracy 89.7523%、Macro-F1 89.8202%。Checkpoint重载同一验证probe差0，完整验证回放一致。SITTING与STANDING双向误判190次；只描述错误分布，没有据测试重新选Epoch或配置。[完整曲线、每类指标与混淆矩阵](../../reports/cnn_baseline_seed42_20261119_run01/execution_report.md)。

## 问题与处理

无训练NaN/Inf、梯度/维度错误，未改配置重训。TypedStorage弃用警告不影响退出0。Icarus机械门禁文件缺失，沿用项目样式并实际查看图片，缺失如实记录。4项既有未追踪内容经用户同意移入logs备份，266文件哈希一致。没有新学生正式作答，不编造。

## 待用户理解的问题（未作答，不标通过）

1. 为什么第15轮停止却使用第7轮权重？
2. 验证Loss更低为何不一定替换最佳模型？
3. Macro-F1为何要明确六类平均与零分母规则？
4. Epoch内训练Loss与结束后固定模型测量有什么不同？
5. 为什么不能根据测试集结果重新选Epoch/种子/配置？
6. MaxPool改变哪个维度，为什么参数量没变？
7. 单种子、9位测试受试者支持与不支持哪些结论？

不开展其他模型或消融，不自行宣布Day 02全部通过。
