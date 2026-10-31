# 报告与历史档案

本目录保留实际执行时的结果与状态。文件名中的日期、运行 ID 和失败标记属于原始证据；不把旧报告中“当时尚无Git仓库”等文字当作当前项目状态。

## 推荐阅读

最新补充：[2026-10-31第一轮整改](remediation_round1_20261031/README.md)，包含独立venv全流程的真实运行、旧结果比较、轻量测试及归档复核；与下列历史原始报告分开保存。

| 目的 | 入口 |
| --- | --- |
| 数据实践完整结论 | [Day 01数据审计](day01_data_20261026_run02/day01_data_audit.md) |
| 最终成功运行的机器可读结果 | [audit02/audit_results.json](day01_data_20261026_run02/audit02/audit_results.json) |
| 独立产物复核 | [independent_verification.json](day01_data_20261026_run02/independent_verification.json) |
| 官方来源、文件大小与本地哈希 | [download_provenance.json](day01_data_20261026_run02/download_provenance.json) |
| 总体类别分布 | [class_distribution.csv](day01_data_20261026_run02/audit02/class_distribution.csv) |

跨文件的当前约定另有[数据协议](../docs/data_protocol.md)；可直接在线查看的图及小型元数据位于[docs/day01](../docs/day01/README.md)。

## 如何区分成功运行与失败现场

- `day01_data_20261026_run01/`：第一次下载因网络权限失败，保留真实来源记录。
- `day01_data_20261026_run02/`：官方下载成功；其 `audit/` 是首次序列化失败现场，**最终成功结果在 `audit02/`**。
- 当日有效处理产物为本地 `data/processed/day01_data_20261026_run02_audit02/`，不使用首次失败目录内的不完整参数。

## 历史执行档案

<details>
<summary>环境、教学归档与Git同步记录</summary>

- [启动环境检查](day01_startup_check.md)。
- [数据执行日志索引](day01_data_20261026_run02/execution_log.md)。
- [2026-10-28正式归档报告](day01_archive_20261028_run01/archive_report.md)：当次归档完成时尚未配置remote。
- [同步前检查](day01_github_preflight_20261028_run01/preflight.md)：用户提供地址之前的状态。
- [后续成功同步回执](day01_github_sync_20261028_run01/sync_receipt.md)：说明上述阻塞后如何完成首次同步。

</details>

## 可移植性与校验边界

历史文件中的绝对路径和被忽略的 `data/`、`outputs/`、`logs/` 链接仅在原执行机器上有效，不把本机路径改写为不存在的GitHub文件。按[复现指南](../docs/reproducing_day01.md)可在新的运行目录生成自己的产物。

历史哈希清单对应产生时的文件字节。README、导航和代码后续可能正常演进，因此旧的“已有文件未变化”结论有时间边界；不要对旧清单静默重算并冒充原始记录。当前文档导航由独立入口检查脚本验证。
