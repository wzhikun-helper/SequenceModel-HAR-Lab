# Day 02｜CNN最小工程复现

目标是检查真实数据到模型、损失、梯度与checkpoint的连接，不运行训练循环、优化器更新、验证选模或测试集评价。[实际报告](../reports/day02_cnn_20261111_run01/README.md)与[学习记录](../learning_notes/day02/README.md)分别存放。

## 环境和前置数据

本次实际使用Windows、Python 3.9.13、PyTorch 2.0.1+cpu、NumPy 1.24.4和CPU，无CUDA。复用已有可用环境，没有为本轮修改全局依赖。[requirements-cnn.txt](../requirements-cnn.txt)是直接依赖快照，不是完整锁文件。

需要安装时可另建venv，使用官方索引；这些安装命令是复现说明，本次没有重新安装或验证安装流程：

```powershell
python -m venv .venv/cnn
.\.venv\cnn\Scripts\python.exe -m pip install --index-url https://pypi.org/simple numpy==1.24.4
.\.venv\cnn\Scripts\python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.0.1+cpu
```

先按[Day 01指南](reproducing_day01.md)获得完整通过的`<SourceRun>_audit02`产物及`reports/<SourceRun>/independent_verification.json`。本轮使用`day01_repro_20261031_run01`，不重新下载、不重新划分或拟合标准化。原始数据和数组不随Git发布，因此fresh clone须先完成Day 01。

## 执行

在根目录，使用有PyTorch的Python；每次使用不存在的新运行ID：

```powershell
python -B -m unittest discover -s tests_torch -v
python -B -u scripts/day02_cnn_smoke.py day02_cnn_new_run --source-run day01_repro_20261031_run01 --seed 20261111
```

脚本先复核Day 01的29个原始文件哈希、训练标签/受试者、全部训练窗口与原始信号及已存标准化参数的逐值一致性；不重新拟合。每个官方活动选择最终训练集中的第一行，共6个窗口，本次均为受试者7。此选择仅用于连接验证，不构成泛化评价。

保存布局为[B,128,9]，以`permute(0,2,1).contiguous()`变为[B,9,128]。标签仅在内存映射`target=official_id-1`，给CrossEntropyLoss提供0–5整数；磁盘标签仍是1–6。

## 固定配置与输出

[模型代码](../src/har_lab/cnn.py)：Conv1d(9,64,3,1,1)→ReLU→Conv1d(64,128,3,1,1)→ReLU→AdaptiveAvgPool1d(1)→Flatten→Linear(128,6)。两层卷积和分类层均带偏置，不含BatchNorm、Dropout或额外模块。分类层输出logits，不先做softmax。原规划全文未取得，卷积参数采用本轮任务的明确默认值，也与已取得的教师教学配置一致；ReLU是本轮明确记录的实现选择。

- `reports/<Run>/result.json`：小型公开审计证据，含环境、源文件哈希、样本ID、逐层形状、梯度和checkpoint哈希。
- `checkpoints/<Run>/untrained_state_dict.pt`：本地忽略的初始权重，不含梯度与优化器状态。一次反向后未执行更新，保存的state_dict逐项等于初始状态。
- 权重用`weights_only=True`、`map_location='cpu'`加载，`strict=True`匹配结构；两个模型在eval/no_grad下对比同一输入，要求逐值相同。

脚本遇错返回非0；独占创建目录，不清理失败现场或覆盖已有结果。需要完整stdout、退出码、时间时，可像本轮一样用外部命令记录器写入被忽略的`logs/`；入口脚本本身只在成功时写result.json。

## 测试范围

`tests_torch/`含4个CPU合成测试，验证布局与数值拒绝、参数量、标签映射、反向及checkpoint往返。本轮本地已运行；现有轻量GitHub CI仍只运行标准库文档检查和25个Day 01契约测试，不安装PyTorch、不下载UCI数据。轻量CI通过不表示CNN真实运行通过。

损失只属于一个未训练模型的单批检查，不报告Accuracy/F1或任何训练收敛结论。后续正式CNN训练及GRU、Transformer、Mamba和消融未执行。
