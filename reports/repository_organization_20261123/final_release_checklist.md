# PR #1 最终交付清单

开始时本地 `docs/repository-organization-20261123` 干净，HEAD 为 `77d6caf3ab508226023d49ee92bdd706d3427776`。执行 `git fetch origin` 后，实时核对 PR Head 和远程分支均为 `279800c5addaf939f48079d8f19bc83345b0f66b`，比本地多 9 个提交。逐项检查 7 个文件的远程改动后以 fast-forward 同步。此时 `git diff origin/main...HEAD --stat` 为 72 个文件，包含既有 Task03、最终归档及仓库整理由来的差异。基准 `main` 为 `3cd855f7059f5dcdc7a9a64555bfef4c41b6c870`，上一 Head 的 [CI 45192891843](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/runs/45192891843) 已完成并成功。

| 验收维度 | 状态 | 验收证据 | 遗留问题 |
| --- | --- | --- | --- |
| 仓库工程质量 | PASS | 最小修改，保留模型和训练入口，新增验证拒绝坏输入 | — |
| 文档与导航 | PASS | 双语默认分支克隆、安装入口、官方获取方式、数据落点、Task03 入口及证据状态一致 | — |
| 实验注册表 | PASS（公开记录） | 15 个独立运行，A42 仅计一次，原始指标与双语表格及注册表一致。[注册表](../../docs/experiment_registry.md) | 服务器原件分开列项 |
| Task03 报告代码 | PASS（合成行为验证） | 补齐未定义的 `require`；全部种子校验后写入新的报告目录。合成夹具覆盖正常报告、坏 Checkpoint、日志、指标、配置、行数、NaN 和 argmax，在 `python -O` 下运行 | 历史 logits 未重新复算 |
| 实验原始证据 | PARTIAL | 三份历史清单共 60 项，18 份公开 Git blob 的 SHA-256 匹配。[逐项状态](task03_evidence_status.csv) | 授权 SSH 认证失败和连接关闭，42 项服务器原件待取回 |
| 48 题学习档案 | PARTIAL | 48 道原题、编号、PDF 和 LaTeX 已交叉核对。独立补充表为 0 FULL、9 PARTIAL、39 MISSING。教师总评维持 48/48。[逐题状态](question_mapping.csv) | 逐题师生原文仍有限，第 23、24 题摘要映射差异保留 |
| Skill | PASS（发现与复用）／PARTIAL（全文自动注入） | 独立桌面会话自动获得元数据，按任务选择并主动读 `SKILL.md`，只读任务通过。[会话复核](skill_verification.md) | 未观察到全文自动注入 |
| 公开安全审计 | PASS（已扫描范围）／PARTIAL（历史隐私） | 原 15 项机器路径逐一检查，扫描 30 个提交和 PDF、PNG。未识别真实凭据。[公开审计](security_audit.md) | 已有提交含非 noreply 邮箱；清理公开历史需要独立授权 |
| GitHub Actions | 以最新 Head 的实际检查为准 | [PR #1 Checks](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/pull/1/checks)。本轮本地运行文档、25 项标准库、16 项 PyTorch 及 4 项 Task03 行为测试；4 项另在 `-O` 重跑 | GitHub 轻量 CI 与本地 PyTorch/报告测试是不同验证层 |
| 独立复现能力 | PASS（公开档案与合成验证）／PARTIAL（Task03 原件） | 当前报告器验证能力有独立合成证据。Day 01 有历史真实数据复现。[检查口径](../../docs/verification.md) | 服务器原件待从授权入口复核 |

## 修改与交付

- [报告器](../../scripts/report_gru_task03.py)、[行为回归测试](../../tests_torch/test_task03_report.py)、[文档和证据守卫](../../scripts/check_public_docs.py)。
- 双语首页、脚本索引、Task03 协议、报告导航和状态文档。公开审计、Skill 会话记录、60 项证据 CSV、48 题扩展 CSV 和本验收在当前目录。
- 通过 [PR #1](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/pull/1) 核对最终 Head、检查和提交列表。此清单所在提交可用 `git log --diff-filter=A --format=%H -- reports/repository_organization_20261123/final_release_checklist.md` 定位。PR 供人工审阅。

本轮没有改写历史题表、PDF、原始结果、源数据或权重。必要的人工作业为核对是否需要另行处理历史 Git 邮箱、恢复授权服务器访问以复算 42 项原件，以及补齐可提供的教师逐题原文。
