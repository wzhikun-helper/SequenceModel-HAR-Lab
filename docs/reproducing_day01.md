# Day 01 数据流程复现

本指南说明现有脚本的调用顺序。当前整理只检查脚本和文档，不重新下载数据、运行预处理或训练模型；实际已执行结果见[2026-10-26 审计](../reports/day01_data_20261026_run02/day01_data_audit.md)。

## 1. 准备独立环境

原数据流程使用 Python 3.9.13、NumPy 1.24.4、Matplotlib 3.7.5、Pillow 9.5.0。根目录依赖文件记录这些已验证直接依赖，没有声称其他版本已验证；它不是完整锁文件。数据流程不需要 PyTorch 或 CUDA。

以下是 Windows PowerShell 示例，在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-data.txt
python -B scripts/check_public_docs.py
```

## 2. 使用新的运行 ID

脚本采用独占新建文件和运行目录，以保留历史成果。同一运行 ID 不能直接反复执行；失败目录也会保留。请选用不存在的新 ID，不要清空旧目录来迁就命令。

```powershell
$Run = 'har_repro_001'
$Artifacts = "${Run}_audit02"
python -c "from pathlib import Path; Path('logs').mkdir(exist_ok=True)"
```

`logs/` 不在版本管理中，fresh clone 需要先创建。运行 ID 只使用字母、数字和下划线，以兼容后续验证脚本。

## 3. 按顺序执行

每条命令成功后再进入下一条；PowerShell 中可用 `$LASTEXITCODE` 检查退出码。下载失败应先检查对应来源记录，不改用不明镜像。

```powershell
# 官方下载、两层ZIP检查与解压
python -B -u scripts/day01_download_uci.py $Run

# 全部窗口审计、固定人员划分、训练集标准化
python -B -u scripts/day01_audit_uci.py $Run audit02

# 从指定的最终训练窗口生成两活动九路信号图
python -B -u scripts/fig01_day01_signals.py $Artifacts

# 独立读取原始文件与保存产物，检查逐值对应关系
python -B -u scripts/verify_day01_data.py $Run $Artifacts
```

这里刻意使用 `audit02`：现有验证脚本读取该审计子目录。它是目录名称约定，并不意味着一次全新复现必须先运行一个失败的 `audit`。绘图元数据和验证日志也只写入新路径。

## 4. 查看输出

| 目录 | 内容 | Git追踪 |
| --- | --- | --- |
| `data/raw/<Run>/` | 官方压缩包、解压原始文件 | 否 |
| `data/processed/<Artifacts>/` | 划分CSV、训练参数、三集合NPZ、绘图源窗口 | 否 |
| `reports/<Run>/` | 下载来源、CRC/SHA-256清单、审计与独立复核 | 需人工审查后选择提交 |
| `outputs/figures/<Artifacts>/` | 两活动PNG/PDF/SVG、图表清单 | 否 |
| `logs/` | 实际执行日志 | 否 |

期望的数据形状与人数见[数据协议](data_protocol.md)。标准化参数只能由最终训练人员拟合；不要改变官方测试集，也不要按窗口随机拆分同一人的相邻记录。

## 5. 脚本的适用范围

- 上述四个脚本是数据流程入口，均不训练模型。
- `scripts/archive_day01_20261028.py` 和 `scripts/prepare_day01_git_sync.py` 是有固定历史路径的一次性归档工具，不能当作通用数据预处理入口重新运行。
- 既有 `verify_day01_data.py` 使用断言检查，不要加 `python -O`，否则会关闭这些检查。
- 历史 `day01_data_20261026_run02/` 的首次处理目录包含已标记的失败产物；当日有效处理产物 ID 是 `day01_data_20261026_run02_audit02`。
- 全量数据复现、依赖重新安装或新环境兼容性检查不包含在本次公开文档整理中。
