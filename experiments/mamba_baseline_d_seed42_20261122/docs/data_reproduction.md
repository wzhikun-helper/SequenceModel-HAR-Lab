# 冻结数据复现

官方 UCI 来源、外层及内层 ZIP、29 个原始文件均匹配历史 SHA-256。使用 GitHub main 的固定源代码运行原 Day 01 下载和预处理，产生 Linux NPZ。独立审计重新从文本信号计算每个标准化值，与 Linux NPZ 逐元素一致，训练集均值和总体标准差与历史公开 scaler 逐值一致。

原 Day 01 处理在 Windows 上生成 ZIP 系统标记 0 和 32 位原生整数窗口索引。Linux 则写入对应的 ZIP 系统标记 3 和 64 位窗口索引。恢复脚本重建原封装和索引精度，历史 scaler 字节直接取自项目已发布的同一文件。恢复的三份 NPZ 及 scaler SHA-256 均逐字节匹配历史冻结值。未改变九路信号的任何 FP32 数值、标签、受试者或行顺序。

在干净的原仓库工作副本中用新 ID 运行，Python 与依赖版本见环境记录。

```bash
python -B -u scripts/day01_download_uci.py har_linux_seed42_20261122
python -B -u scripts/day01_audit_uci.py har_linux_seed42_20261122 audit02
```

设 `REPO` 为原仓库工作副本，`DATA` 为上述运行生成的处理目录。从 Mamba 实验项目根目录执行。

```bash
python -B scripts/audit_data.py "$REPO" har_linux_seed42_20261122 \
  har_linux_seed42_20261122_audit02 audit/data.json
python -B scripts/restore_frozen_data.py "$REPO" "$DATA" data/frozen audit/data.json
```

[数据审计](../audit/data.json) · [冻结 SHA-256](../audit/frozen_data.json)
