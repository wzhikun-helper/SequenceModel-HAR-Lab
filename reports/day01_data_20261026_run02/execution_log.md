# Day 01 实际执行日志索引

日期与时区：2026-10-26，Asia/Shanghai。所有路径相对 `D:\SequenceModel-HAR-Lab`。

| 顺序 | 实际操作 | 实际结果与记录 |
| --- | --- | --- |
| 1 | 读取 `reports/day01_startup_check.md`、`.gitignore`；列出项目和既有文件；查找 AGENTS/runtime/manifest | 保留原成果；无项目 runtime guard、冻结清单或 AGENTS 文件；新脚本使用全新目录、排除链接、独占创建输出 |
| 2 | 读取数据审计与绘图技能及相关参考；检查 matplotlib、paperfig | matplotlib 3.7.5 可用；paperfig 与技能原版 critique/style 辅助脚本缺失，未安装依赖 |
| 3 | 浏览 UCI 数据集 240 官方页，跟随 Download 链接 | 得到 archive.ics.uci.edu 官方 URL；网页工具因大文件上限拒绝读取 ZIP，未转向第三方 |
| 4 | 对启动报告、忽略规则、README、启动脚本取 SHA-256 | 保存于 `existing_files_baseline.json` |
| 5 | `python -B -u scripts/day01_download_uci.py day01_data_20261026_run01` | 退出 1，WinError 10013；`logs/day01_data_20261026_run01_download.log`，run01 `download_provenance.json` |
| 6 | 经工具权限审核重试：`python -B -u scripts/day01_download_uci.py day01_data_20261026_run02` | 退出 0，下载 61,005,872 字节并完成两层 CRC、SHA-256、解压；`logs/day01_data_20261026_run02_download.log` |
| 7 | 读取下载完成的 README、标签映射、provenance；列出九路训练信号文件 | 获得官方采样率、单位、窗口信息、文件结构；不改原始文件 |
| 8 | `python -B -u scripts/day01_audit_uci.py day01_data_20261026_run02` | 退出 1；schema、划分完成后在 scaler JSON 遇到 NumPy int64 序列化错误；保留 `audit/` 和旧 processed 失败现场 |
| 9 | 修复本次新增审计脚本：显式 int 转换、先序列化再创建 JSON、允许全新 attempt 名 | 仅修复本次新增脚本；启动成果、原始数据和失败现场不覆盖 |
| 10 | `python -B -u scripts/day01_audit_uci.py day01_data_20261026_run02 audit02` | 退出 0；audit02 数据审计、划分、scaler、三份 NPZ、源窗口 CSV 完成，29 原文件与启动成果哈希不变 |
| 11 | `python -B -u scripts/fig01_day01_signals.py day01_data_20261026_run02_audit02` | 退出 0，2 活动×3 格式；MPLCONFIGDIR 指向项目 logs，未更改用户绘图配置；日志 `logs/day01_data_20261026_run02_audit02_figures.log` |
| 12 | 直接打开两张 PNG | 九路标签、活动名、坐标轴、物理单位、来源与 n=1 脚注可见；相应通道共用纵轴尺度，无文字截断 |
| 13 | `python -B -u scripts/verify_day01_data.py day01_data_20261026_run02 day01_data_20261026_run02_audit02` | 退出 0；磁盘独立复核 PASS；结果 `independent_verification.json`，详细日志 `logs/day01_data_20261026_run02_audit02_verification.log` |
| 14 | 新建 `day01_data_audit.md` 与本日志索引；标注失败产物不可用 | 交付有效路径指向 `_audit02`；不把第一次失败当成完成 |

完整 Python traceback、下载进度、实际类别计数、标准化检查结果均保留在对应日志。原始网络异常的中文消息在 JSON/UTF-8 日志中完整保存，终端默认编码可能显示为乱码。

没有下载非 UCI 来源、训练模型、改原始文件、删除文件、改用户 Python/Conda/Git 设置、初始化 Git、提交、推送或上传数据。没有执行已安装技能中缺失的原版 critique 门禁，也没有声称该门禁通过。
