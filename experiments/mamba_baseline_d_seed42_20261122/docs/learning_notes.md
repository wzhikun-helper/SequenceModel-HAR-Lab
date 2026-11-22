# Mamba D 学习笔记

这个分类器在每个时间点将 9 路传感器值投影到 64 维。原始 Mamba Block 保留 128 个时间点，随后沿时间轴取均值，线性层输出六类 logits。原始 Block 的输入依赖选择性状态更新与深度因果卷积属于模型本体。实验关闭可选的融合路径，通过官方 CUDA selective scan 完成状态扫描。L0 验证已安装代码与固定官方版本一致，再检查 CUDA 调用及梯度。L1 用两个真实训练 Batch 检查交叉熵、原始 Block 梯度和 Adam 更新。 [Mamba 论文](https://arxiv.org/abs/2312.00752) · [官方 Mamba Block](https://github.com/state-spaces/mamba/blob/v2.2.6/mamba_ssm/modules/mamba_simple.py)

正式模型重新按 Seed42 初始化。早停和最佳权重只根据验证 Macro-F1 及并列时的验证 Loss。最佳权重确定后对官方测试集前向遍历一次，独立核验按官方样本顺序检查预测，并从保存的 logits 复算混淆矩阵和交叉熵。

对照利用已有的 CNN、GRU、Transformer 测试存档。误判分析关注坐站双向混淆、三类步行之间的错分，以及 LAYING 的漏报与误报。混淆矩阵支持描述错误集中在哪些分类对。机制归因还需要额外的受控实验。单次 Seed42 与一套受试者划分也无法估计重复训练的变异。
