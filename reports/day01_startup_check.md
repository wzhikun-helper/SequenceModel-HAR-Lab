# Day 01 启动检查与操作日志

检查日期：2026-10-26，Asia/Shanghai。完整环境复核时间：10:12:04–10:12:09。

## 结论

当前环境具备使用 CPU 读取 UCI HAR 空白分隔文本的基础条件。已通过 NumPy 内存文本读取检查（特征矩阵 2×3、整数标签 2 个、特征均为有限数，退出码 0）。此检查仅验证读取基础能力，不是对真实 UCI HAR 文件、维度、标签或划分的验收。真实数据尚未下载。

当前 PyTorch 为 CPU 构建，不能使用 GPU。GitHub 推送条件尚不齐备。此次按“只准备最小项目骨架”的范围执行，没有初始化 Git 仓库。

## 实际环境

| 项目 | 实际结果 |
| --- | --- |
| 项目路径 | `D:\SequenceModel-HAR-Lab`，启动时已存在、为空 |
| Windows 运行时报告 | `Microsoft Windows 10.0.26200` |
| Windows 注册表 | ProductName=`Windows 10 Home China`；DisplayVersion=`25H2`；Build=`26200.9711`；EditionID=`CoreCountrySpecific` |
| PowerShell | 7.6.6 Core |
| Python | 3.9.13，64 位；`E:\pythonenv\python39\python.exe` |
| Python launcher | `py -0p` 仅列出上述 Python 3.9 |
| PyTorch | 2.0.1+cpu，导入成功 |
| PyTorch CUDA runtime / cuDNN | 均为 None |
| PyTorch CUDA 可用性 | False；设备数 0 |
| GPU | NVIDIA GeForce RTX 3060 Laptop GPU，6144 MiB |
| NVIDIA 驱动 | 580.88 |
| nvidia-smi 显示 CUDA | 13.0（驱动侧信息，不代表 PyTorch 已启用 CUDA） |
| CUDA Toolkit / nvcc | release 13.3，V13.3.73 |
| nvcc 路径 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\nvcc.exe` |
| NumPy / pandas / SciPy | 1.24.4 / 2.0.3 / 1.10.1，均导入成功 |
| Git | 2.55.0.windows.3 |

Windows 名称按系统原始字段保留，未根据版本号猜测或改写营销名称。nvcc 与驱动显示的 CUDA 版本不同，未编译或执行 CUDA 程序，不能据此宣布 GPU 计算栈验证通过。

## Git 与 GitHub 推送检查

- `git rev-parse --show-toplevel`：非 Git 仓库；也未检测到父目录仓库。
- 当前项目 `.git`：不存在。remote、branch、status：不适用。
- Git 的有效 `user.name`、`user.email` 已配置；未记录具体姓名和邮箱。
- 有效 `credential.helper` 为 `manager`；只检查配置，未读取凭据内容。
- PATH 中未发现 GitHub CLI `gh`。这不是 Git 推送的必要条件。
- 没有项目 remote；GitHub 身份认证、目标仓库写权限及网络推送访问未验证，因此不能宣称可以推送。
- 没有执行 `git init`、`git add`、`git commit`、`git push`，也没有改动全局 Git 配置。

`.gitignore` 已排除本地 data/models/checkpoints/outputs/runs/logs 目录、常见权重与二进制数据、归档、虚拟环境、缓存及常见密钥文件。它是后续提交的基础防护，不能替代首次提交前对待暂存文件的人工审查；当前没有暂存文件或提交。

## 实际操作日志

1. 列出项目目录及隐藏文件：目录存在且为空，因此没有覆盖已有项目文件。
2. 检查 `D:\AGENTS.md` 与项目 `AGENTS.md`：均未发现。
3. 首次使用默认 PowerShell 配置启动时，用户 profile 中的 Conda hook 报 `StandardOutputEncoding is only supported when standard output is redirected`。此后使用不加载 profile 的方式完成检查；未修改用户 profile 或 Conda。
4. `Get-CimInstance Win32_OperatingSystem` 被当前执行环境拒绝访问。改用 .NET OSDescription 和只读注册表查询，成功取得上表结果；未请求额外权限。
5. 执行 Python、PyTorch、NVIDIA、nvcc、Git 版本检查及内存文本读取检查。没有安装、升级或切换依赖。
6. 仅新增 `.gitignore`、`README.md`、`scripts/check_day01.ps1`、本报告，以及空目录 `src/`、`data/`、`models/`、`logs/`、`reports/`。`scripts/` 内只有环境检查脚本。
7. 执行环境检查脚本，保存原始输出至 `logs/day01-environment-20261026-101204-208.txt`。日志使用新建文件模式，遇到同名文件会失败，不覆盖旧日志。
8. 保存后复核文件清单、日志内容、Python 读取测试退出码与 `.git` 缺失状态。

未下载数据、未读取真实 HAR 数据、未训练模型、未创建模型权重、未访问密钥内容、未提交或推送、未删除任何文件、未修改项目外文件。

## 交给 ChatGPT 验收后的待决定事项

1. 确认本报告后，明确 UCI HAR 数据来源或已有本地路径，以及下一项读取验收要求。真实文件的存在性、目录结构、形状、标签与受试者划分尚待验证；本次不执行这些操作。
2. 需要版本管理时，再决定初始化本地仓库、分支名称、GitHub 仓库地址及认证方式；首次提交前检查暂存清单，排除数据、权重、密钥及个人信息。
3. 如果下一阶段需要 GPU，再选择兼容的独立 Python/PyTorch 环境并验证 CUDA；读取 UCI HAR 文本无需先解决 GPU。

工程执行停在 Day 01 启动检查，等待教学与验收决定下一项任务。
