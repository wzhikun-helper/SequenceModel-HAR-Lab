# 第五章消融复现

使用现有环境 E:/pythonenv/python39/python.exe，Python 3.9.13、torch 2.0.1+cpu、NumPy 1.24.4，CPU FP32、2 线程。数据为已审计的 Day 01 产物，执行入口复核全部冻结输入 SHA。实际配置与初始权重指纹见各运行目录。

本次先使用 `scripts/audit_cnn_ablation.py <已验证的远程SHA>` 创建独立审计证据，再使用 `scripts/train_cnn_ablation.py <A|B|C> <42|43|44> <新运行ID>` 执行。跳过 A42，保存其原历史评估。实际运行顺序为 B42、C42、Seed42 核验，随后 A43/B43/C43、Seed43 核验，最后 A44/B44/C44、Seed44 核验。现有目录由入口拒绝覆盖，独立核验入口 `scripts/verify_cnn_ablation.py <seed>` 按本报告的八个存档运行 ID 汇总，绘图入口 `scripts/report_cnn_ablation.py` 使用本轮归档及本地命令计时。

每组先在独立对象上运行两个训练 Batch。正式模型重新设置所有种子，先建立共享网络，再使用 PyTorch Linear 默认初始化新增模块。记录共享和完整初始状态指纹。批次顺序由独立 Loader Generator 复现，每轮保存输入和标签依次写入 SHA-256 的哈希。

选模使用完整验证集，最佳和最后模型分别在固定验证 Probe 下核对。最后测试只调用一次，独立复算仅读取预测与官方标签。训练入口进程耗时包含外部 Python 启动。新运行还单独记录包含批次顺序哈希、验证及保存最佳权重的 Epoch 循环耗时。旧 A42 入口不含单独预检查，且没有可比的纯 Epoch 循环耗时。

已发布的总结和图表使用了本次实际产生的 CSV 和 JSON。原始 stdout、权重和矢量图留在本地。新环境需具备相同的数据和经核实的环境与历史证据。
