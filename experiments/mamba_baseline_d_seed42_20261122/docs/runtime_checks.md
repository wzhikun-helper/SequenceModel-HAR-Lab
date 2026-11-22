# L0–L3 执行核验

L0 对一个真实训练窗口验证官方扩展的 CUDA 前向与反向各一次。已安装的原始 Mamba 模块与固定官方源码逐字节相同。L1 使用两个 64 窗口的真实训练 Batch，输入为 [64,128,9]，输出为 [64,6]。两批损失为 1.812567 和 1.781713，各调用一次官方 CUDA 前反向。原始 Block 的 9 个参数张量均得到有限非零梯度，每批优化后均发生变化。预检查权重重载后输出逐元素相等。

L2 重新初始化并与 Seed42 初始参数逐个比较。第 3 轮验证 Macro-F1 为 94.3887%，第 11 轮连续八轮无改善后早停。正式训练循环耗时约 2.681 秒，记录口径含训练、逐轮验证和最佳权重保存。PyTorch 峰值 allocated 为 148,045,824 B（141.19 MiB），reserved 为 159,383,552 B（152.00 MiB）。该口径为 PyTorch 分配器，不含 CUDA 上下文和其他程序。Best、Last 权重在验证输入上重载一致，最大误差 0。

L3 检查 2,947 行预测的官方顺序、标签和 logits。分类统计与正式测试一致，独立以 FP64 重算交叉熵与正式测试的差值约为 1.05e−9。独立核验只读取预测产物，测试模型正式前向遍历一次。

[CUDA 门禁](../audit/cuda_runtime.json) · [两批预检查](../reports/preflight.json) · [训练历史](../reports/training_history.csv) · [重载证据](../reports/checkpoint_reload.json) · [独立复算](../reports/independent_verification.json) · [四模型比较](../reports/four_model_comparison.md)
