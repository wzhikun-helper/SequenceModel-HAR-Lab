# PR #1 公开仓库安全与隐私审计

审计起点为 `279800c5addaf939f48079d8f19bc83345b0f66b`，旧路径统计来自 `95f0047cfbcdea1bce493a6eec6f71b8c2cb53de`。本机没有 gitleaks 或 ExifTool，使用本地 Python 正则、Git 对象读取、Poppler 和 Pillow 补充扫描。通过 `git rev-list --all`、`git ls-tree -rz`、`git cat-file --batch` 枚举和读取 **30 个可达提交、543 个唯一 blob**（509 文本、34 二进制）。覆盖开始时 458 个跟踪路径、相对 main 的 72 个 PR 路径和本地引用可达的旧版本。历史路径与当前路径集合相同，仍逐个扫描了只在历史版本出现的内容。未查未获取的远程引用、私有日志、Git 不可达对象或 GitHub 缓存。

## 恢复并核对原 15 个文件

| 文件 | 检查内容 | 发现的问题 | 处理措施 | 状态 |
| --- | --- | --- | --- | --- |
| [`reports/cnn_ablation_20261122/check_commands.json`](../../reports/cnn_ablation_20261122/check_commands.json) | Windows 执行入口及日志定位；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/cnn_ablation_20261122/reproducibility.md`](../../reports/cnn_ablation_20261122/reproducibility.md) | CPU 解释器和复现环境；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/cnn_ablation_20261122/run_commands.json`](../../reports/cnn_ablation_20261122/run_commands.json) | 各次运行的 Windows 命令参数；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/cnn_ablation_audit_20261122/evidence.json`](../../reports/cnn_ablation_audit_20261122/evidence.json) | 审计环境和解释器；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/cnn_baseline_seed42_20261119_run01/commands.json`](../../reports/cnn_baseline_seed42_20261119_run01/commands.json) | CNN 正式运行命令；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/cnn_baseline_seed42_20261119_run01/reproducibility.md`](../../reports/cnn_baseline_seed42_20261119_run01/reproducibility.md) | CNN 解释器、运行环境；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/day01_archive_20261028_run01/README.diff`](../../reports/day01_archive_20261028_run01/README.diff) | 历史文档差异／工作区路径；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/day01_startup_check.md`](../../reports/day01_startup_check.md) | 启动时的工作目录与环境；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/day02_cnn_20261111_run01/README.md`](../../reports/day02_cnn_20261111_run01/README.md) | 最小试验命令与解释器；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/day02_cnn_20261111_run01/commands.json`](../../reports/day02_cnn_20261111_run01/commands.json) | 最小试验保留的命令参数；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/gru_baseline_seed42_20261121_run01/commands.json`](../../reports/gru_baseline_seed42_20261121_run01/commands.json) | 历史 CPU GRU 运行命令；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/gru_baseline_seed42_20261121_run01/reproducibility.md`](../../reports/gru_baseline_seed42_20261121_run01/reproducibility.md) | 历史 CPU GRU 环境；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/mamba_l0_20261122/project_audit.json`](../../reports/mamba_l0_20261122/project_audit.json) | 本地环境与远程检查分类；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/transformer_baseline_seed42_20261122_run01/commands.json`](../../reports/transformer_baseline_seed42_20261122_run01/commands.json) | Transformer 运行命令；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |
| [`reports/transformer_baseline_seed42_20261122_run01/reproducibility.md`](../../reports/transformer_baseline_seed42_20261122_run01/reproducibility.md) | Transformer 解释器与运行环境；核对个人目录、网络定位及凭据模式 | 保留科研环境路径；未发现需处理的匹配 | 保留原件 | PASS |

## 其他覆盖面与处置

| 范围 | 检查内容 | 发现的问题 | 处理措施 | 状态 |
| --- | --- | --- | --- | --- |
| 工作树、PR 与文本历史 | 用户目录、Windows/Linux 绝对路径、挂载路径、邮件、常见内网主机与 SSH 地址、私钥、GitHub/API 令牌、JWT、带身份验证的 URL 和密码赋值 | 未识别真实凭据；锁文件中的点分数字来自依赖版本和构建名 | 保留源码及归档；人工复核新增提交范围 | PASS（已执行模式） |
| Git 作者与提交者字段 | 对 30 个可达提交检查邮箱类型 | 发现两组非 noreply 公开邮箱服务地址，分别覆盖 18 和 12 个提交；例如 `127eeaa`、`1073082` 可定位到对应历史记录 | 本轮提交采用 GitHub noreply；报告不复述字段值。已有历史仍可见，进一步清理须独立授权 | PARTIAL |
| 12 个 PDF blob | Poppler 检查 Author、Creator、Producer、CreationDate、ModDate、自定义元数据、XMP 及提取文本；另筛查嵌入文件标记 | 有 Creator、Producer、CreationDate；未检出 Author、ModDate、XMP、自定义字段或嵌入文件标记 | 保留 PDF 字节和归档哈希 | PASS（已枚举字段） |
| 22 个 PNG blob | Pillow 检查文本字段、软件标记、尺寸元数据、EXIF、XMP | 软件与 dpi 字段；未检出 EXIF、XMP 或身份字段 | 保留原图 | PASS |
| SVG、Office 与隐藏对象 | SVG 位于 text blob 扫描；另枚举常见 Office 容器 | 无跟踪 DOCX、PPTX、XLSX；字段与文本检查未遍历所有可能的二进制对象及编码 | 保留剩余检查边界，不以无匹配证明无风险 | PARTIAL |

本轮未识别到要求轮换的真实凭据。若需变更任何已有公开提交的作者邮箱或清理 GitHub 缓存，应先确定所有权、影响范围和授权。原始报告、权重、历史记录及数据未做删除或重写。
