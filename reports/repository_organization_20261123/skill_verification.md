# 项目 Skill · 独立会话复核

测试提示要求只读核对官方 UCI HAR 测试窗口数和 A42 的批次顺序来源，并记录系统提供的指导。提示未包含项目 Skill 的名称、路径或预期答案。

| 检查 | 实际观察 | 状态 |
| --- | --- | --- |
| 独立 CLI 会话 | `codex exec --ephemeral --sandbox read-only --json` 启动了会话，但默认模型返回 HTTP 400 `model_not_found`，退出 1 | 该入口未完成 |
| 独立桌面项目会话 | 新建本地项目会话，转交同一只读任务；任务完成。首次文件读取直接指向 `SKILL.md`，前面没有目录搜索 | PASS |
| 自动发现 | 新会话确认宿主提供名称、简介、路径，按任务选用了项目 Skill | PASS |
| 完整指令自动加载 | 新会话通过 `Get-Content -LiteralPath` 主动读取完整指令；未观察到宿主直接注入全文 | PARTIAL |
| 只读结论 | 官方测试 2,947 窗口；A42 是按原加载器和 Seed42 事后重建的 15 轮顺序指纹。会话复查两份归档的 SHA-256 和工作区状态 | PASS |

核对来源为 [Day 01 审计](../day01_data_20261026_run02/audit02/audit_results.json) 与 [Seed42 复核](../cnn_ablation_20261122/independent_seed42.json)。通过桌面工具读取该独立会话的完成状态、首次命令和最终回答。原报告 [显式调用](../fourth_plan_final_archive_20261123/skill_usage.md) 与 [Task03 使用记录](../gru_multiseed_task03_20261123/skill.md) 保留历史语境。

人工复核可在新建同项目会话中照用上述只读问题。先记录宿主暴露的目录，再检查命令序列，区分提供完整指令与执行后读取文件。若希望验证根本无需显式读取的全文自动注入，还需从客户端取得能证明该事件的上下文记录。
