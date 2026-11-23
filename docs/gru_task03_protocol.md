# Task 03 · GRU 匹配实验协议

历史 CPU Seed42 的配置、模型源码、训练脚本和 30 轮记录来自仓库原归档。六个源码文件均匹配历史 SHA-256。Git 工作副本的配置使用 LF，恢复历史 CRLF 后原配置和逐轮日志分别匹配历史清单。旧 stdout 的清单存在，原文件未取回。

[历史原配置](../configs/gru_task03/cpu_seed42_archived.json) · [历史 GRU 日志表](../reports/gru_baseline_seed42_20261121_run01/training_history.csv) · [源码与输入核验](../reports/gru_multiseed_task03_20261123/input_audit.json) · [GPU 配置](../configs/gru_task03/gpu_base.yaml)

## 共享条件

- 单层单向 GRU，输入 9，隐藏 64，带偏置。输入 `[B,128,9]`，batch-first，隐状态由零开始，dropout 为 0，使用 `h_n[-1]` 和带偏置的 Linear(64,6)，共 14,790 个可训练参数。
- FP32 交叉熵，mean reduction，ignore index −100，label smoothing 0。Adam 的 lr 0.001、betas 0.9/0.999、eps 1e-8、weight decay 0。其余 Adam 选项取真实归档。自动 foreach/fused 选项保留，PyTorch 可因设备选择不同实现。
- Batch 64，最多 30 轮，8 轮未改善即早停。严格更高 Validation Macro-F1 入选，精确同分比较更低 Validation Loss。训练打乱，验证与测试顺序读取，0 个加载 worker，保留尾批，关闭 pin memory。
- 三个 GPU 配置仅 Seed 不同。初始化前固定 Python、NumPy 和 PyTorch CPU/CUDA RNG。模型通过原构造函数在 CPU 初始化后转入 CUDA。DataLoader 使用独立同 Seed 的 Torch Generator，逐轮记录实际官方行号的哈希。FP32 下关闭 AMP 和 TF32，启用确定性设置。
- 三个集合保持 6,037／1,315／2,947 窗口和 17／4／9 名互不重叠的受试者。复用冻结数组和训练集 scaler，加载时将标签 1–6 映射至 0–5。三组测试输入 SHA-256 相同。

## 运行与复核

在完整 Git 克隆的干净预备提交上，使用现有 Linux CUDA 环境，通过历史来源、数据哈希、GPU、磁盘和实样本门禁。将已核验冻结文件链接到 `data/processed/day01_data_20261026_run02_audit02`，为每次运行选择新的输出目录。命令中的准入 JSON 必须来自当次检查，包含预备提交、四个冻结输入哈希及通过状态。

```bash
python -B -u scripts/train_gru_task03.py --preflight "$RUNS/audit/gpu_preflight"
for seed in 42 43 44; do
  python -B -u scripts/train_gru_task03.py --seed "$seed" \
    --out "$RUNS/seed$seed" --admission "$RUNS/audit/admission.json"
done
```

每次正式执行将完整命令、起止时间和退出码与 stdout 一并保存为各运行的 `training.log`，以单独一行 `Exit code 0` 记录成功。新运行完成后执行 `python -B scripts/report_gru_task03.py "$RUNS" "$FROZEN_DATA" "$NEW_REPORT"`，先验证三组的保存 logits、指标、权重哈希和采样证据，再把图、复算和新 SHA-256 清单写入新报告目录。运行目录保持只读，历史清单继续按生成当时的范围解释。公开副本的范围见 [60 项状态表](../reports/repository_organization_20261123/task03_evidence_status.csv)。

历史 CPU 采用 Windows 和 PyTorch 2.0.1，本次 GPU 采用 Ubuntu 和 PyTorch 2.5.1+cu121。CPU 结果仅作为历史参考。平台、版本和后端共同变化，速度和分数差异均不能归因于 GPU 单独作用。

报告器使用现存预测独立复核六类别的 Precision、Recall、F1 和 Support，按原始顺序核对类别表与公开 JSON。训练历史须有从 1 开始的连续 epoch、有限非负 Loss、区间 `[0, 1]` 内的 Accuracy 和 Macro-F1，以及与运行结果一致的采样指纹。三组均通过后才创建报告输出。
