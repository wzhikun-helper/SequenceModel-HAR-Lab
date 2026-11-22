# Mamba Baseline D · UCI HAR · Seed42

在 Linux RTX 3090 上执行单层官方 Mamba v2.2.6、FP32、Seed42。官方测试 2,947 个窗口，Accuracy **88.7004%**，Macro-F1 **88.8610%**，Loss **0.379041**。模型有 33,670 个可训练参数，最佳第 3 轮，第 11 轮早停。正式测试指标由保存的预测独立复算，实验等待教师验收。

核心结构为 Linear(9,64)、官方原始 Mamba Block（d_model=64、d_state=16、d_conv=4、expand=2）、时间均值与 Linear(64,6)。两份官方原始 ZIP、三份冻结数组和标准化参数均匹配历史 SHA-256。验证选模仅使用 Validation Macro-F1 和同分时的 Validation Loss。

[四模型比较](reports/four_model_comparison.md) · [逐类指标](figures/class_metrics.png) · [混淆矩阵](figures/confusion_matrices.png) · [L0–L3 运行核验](docs/runtime_checks.md)

[数据复现](docs/data_reproduction.md) · [独立环境](docs/environment.md) · [固定配置](configs/seed42.json) · [学习笔记](docs/learning_notes.md)

## 复现实验

使用 [环境记录](docs/environment.md) 安装依赖并构建固定官方 CUDA 扩展，用 [数据流程](docs/data_reproduction.md) 生成冻结的四份输入。保留当前仓库工作副本作为 PROJECT，准备一个新的可写 RUN 目录和冻结输入 DATA 目录。使用独立环境的 Python，从本实验归档目录执行。

```bash
mkdir -p "$RUN"/{audit,reports,checkpoints,figures}
python -B -u scripts/check_cuda.py "$DATA" "$OFFICIAL_MAMBA_SOURCE" "$RUN/audit/cuda_runtime.json"
python -B -u scripts/run_mamba.py --project "$PROJECT" --data "$DATA" --run-dir "$RUN"
python -B -u scripts/verify_and_compare.py "$PROJECT" "$DATA" "$RUN"
```

RUN 中的权重、逐样本预测和执行日志在服务器本地保留。公开存档包含汇总指标、哈希及图表。历史基线和环境审计的起始源码为 `a94ca6d58f6eede9cb08a6f4989a8dfbcbcb14c8`。
