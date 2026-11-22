# Mamba Baseline D｜L0 环境审计

2026-11-22，项目与数据核验通过。**L0 GPU 运行门禁未通过，L1–L3 未启动。** 停止原因是当前会话没有可进入并验证的 Linux CUDA 环境。

## 项目与数据

开始时工作区干净，本地 HEAD 与 GitHub main 均为 `8c08911e326466391777539f1ee54cd507b8a3aa`。审计重新计算 UCI HAR 原始两层 ZIP、固定数据和参数的 SHA-256，校验三份 NPZ 的窗口、通道、受试者、标签和有限值。训练、验证、测试为 6,037／1,315／2,947 窗口、17／4／9 人，受试者互不重叠。标准化参数来自最终训练集，输入采用已保存的 FP32 九路信号，历史入口在内存中把标签 1–6 映射到 0–5。

核对了 CNN A、GRU B、Transformer C 的配置、最佳 Checkpoint 字节哈希、重载与一次最终评价记录，以及 CNN 消融九组存档指标和三次独立核验。后续应沿用 Seed42、batch64、Adam lr 0.001、betas 0.9/0.999、eps 1e-8、weight decay 0、CrossEntropy、max30、patience8，验证 Macro-F1 优先、完全同值才比较较低验证 Loss。训练集合打乱，验证及测试按顺序读取，保留尾批。数据和结果复核仅读取已有记录和文件。

[机器审计证据与冻结哈希](project_audit.json) · [数据协议](../../docs/data_protocol.md) · [CNN 消融存档](../cnn_ablation_20261122/README.md)

## 计算环境与排查

| 检查 | 实际结果 |
| --- | --- |
| Windows | Windows 内核版本 10.0.26200，以 Python 平台记录为准 |
| NVIDIA | GeForce RTX 3060 Laptop GPU，6,144 MiB，驱动 580.88 |
| CUDA | `nvidia-smi` 报告驱动 CUDA 13.0，`nvcc` 为 Toolkit 13.3.73。两项均不能替代 Python 环境中的 CUDA Runtime |
| 本地 Python | Python 3.9.13，PyTorch 2.0.1+cpu，NumPy 1.24.4。PyTorch CUDA build 为 null，CUDA 可用性为 False |
| 本地导入 | `mamba_ssm`、`selective_scan_cuda`、`causal_conv1d` 均实际尝试导入并返回 ModuleNotFoundError |
| 本地工具 | GCC/G++ 为 Windows MinGW 13.2.0，ninja 1.12.0。可用空间 C 10.5 GiB、D 56.9 GiB、E 90.2 GiB |
| WSL | `wsl --list --verbose` 退出 1，`wsl --status` 退出 50，均提示安装。当前用户没有注册发行版 |
| 已配置 Linux 入口 | 三个 SSH 入口以 BatchMode 和严格主机密钥校验尝试。两个连接超时，一个认证失败，均退出 255。未进入远程 shell，无法核实 Ubuntu、GPU、CUDA、工具链、磁盘或安装权限 |

远程 Git 查询在受限会话中先因 Schannel 凭据错误失败，通过网络权限重跑读到了远程 SHA。SSH 盘点使用已有配置，固定短超时并保留严格主机密钥验证。系统级 WSL 安装涉及修改操作系统组件，本轮授权范围为项目独立环境。远程入口不可用时，本机亦无法在官方文档支持的平台上做有意义的 CUDA 安装修复。本轮未创建环境、装包、改驱动或传输数据。

## 官方实现和待验证版本

选定待验证来源为官方 tag `v2.2.6`，Git 查询指向 `d7b1ceb3c367ec9022925e812f507bcf706937c6`。目标类为 `mamba_ssm.modules.mamba_simple.Mamba`，即原始 Mamba Block。官方说明列出 Linux、NVIDIA GPU、PyTorch 1.12+、CUDA 11.6+。构建脚本要求 Python 3.9+，声明 torch、packaging、ninja、einops、triton、transformers。优化的 causal-conv1d 是可选组件。原始 Block 的非融合路径使用官方选择性扫描，核心接口调用 `selective_scan_cuda.fwd` 和 `selective_scan_cuda.bwd`。因此真正的 L0 核验须观测 CUDA 前向、反向及有限梯度。仅安装、导入或使用 CPU 参考计算均不能通过该门禁。

官方标签锁定了源码候选。由于目标主机尚未进入，依赖解析、CUDA/PyTorch ABI、编译和算子运行均未验证，无法生成已运行的完整环境锁。恢复时先盘点实际 GPU、驱动、CUDA Runtime/Toolkit、Python、编译器及空间，再以同一兼容环境完成 FP32 官方算子探针，保存实际依赖版本和日志。候选结构是单层、`d_model=64`、`d_state=16`、`d_conv=4`、`expand=2`、时间均值、原 Block 默认初始化和带偏置的线性投影。结构及参数量待实测后冻结。

[官方源码标签和安装说明](https://github.com/state-spaces/mamba/tree/v2.2.6) · [原始 Block](https://github.com/state-spaces/mamba/blob/v2.2.6/mamba_ssm/modules/mamba_simple.py) · [CUDA 前后向接口](https://github.com/state-spaces/mamba/blob/v2.2.6/mamba_ssm/ops/selective_scan_interface.py) · [构建与依赖](https://github.com/state-spaces/mamba/blob/v2.2.6/setup.py)

## 四模型对照状态

| 模型 | Test Accuracy | Test Macro-F1 | Test Loss | 参数量 | 最佳／实际 Epoch |
| --- | ---: | ---: | ---: | ---: | ---: |
| CNN A，历史 | 89.7523% | 89.8202% | 0.290570 | 27,270 | 7／15 |
| GRU B，历史 | 91.8222% | 91.9444% | 0.255319 | 14,790 | 23／30 |
| Transformer C，历史 | 88.0896% | 88.0326% | 0.425905 | 34,502 | 7／15 |
| Mamba D | 待运行 | 待运行 | 待运行 | 待实测 | 待运行 |

现有三项 Seed42 记录中 GRU 的 Macro-F1 最高。CNN 通过局部卷积汇聚窗口特征，GRU 使用递归末状态，Transformer 使用时间点间自注意力与时间平均。Mamba D 仍缺实测，无法核实其逐类表现、坐站混淆、显存、训练成本与指标权衡。L1 真实 Batch、L2 正式训练与独立测试、L3 四模型分析和结果图表均等待可用 CUDA 环境。若未来比较耗时，应分别记录硬件、精度和计时口径。单 Seed42 也无法估计训练随机性或跨受试者划分的变异。

[历史三模型证据](../transformer_baseline_seed42_20261122_run01/three_model_comparison.md)

## 归档检查

项目审计命令为 `python -B scripts/audit_mamba_l0.py`，退出 0，表示文件和历史记录核对完成。GPU 门禁另记为 BLOCKED。16 项现有 PyTorch 测试、25 项标准库数据契约测试和文档检查通过。代码和报告变更不包含私有 SSH 主机信息。本轮测试覆盖仓库的既有功能和归档，Mamba CUDA 算子仍待验证。
