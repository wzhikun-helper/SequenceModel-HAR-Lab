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

## 最终状态核验

上述 72 个文件是 `279800c` 的历史快照。最后一轮开始时，工作区干净。重新获取引用后，本地、远程整理分支、PR #1 均为 `2e896fd66203ad2b0213bd305f54bebb910d343b`；Base SHA 为 `3cd855f7059f5dcdc7a9a64555bfef4c41b6c870`。当时 PR 有 **18 个提交、78 个变更文件**，[Actions #45197696633](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/runs/45197696633) 在该 Head 成功。

| 项目 | 本轮核验 |
| --- | --- |
| 工程快照 | [`b02f455524d773b02f50b53f1add5ecb88f0a9bd`](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/commit/b02f455524d773b02f50b53f1add5ecb88f0a9bd)，PR 此时为 20 个提交、78 个文件。[Actions #45210908726](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/runs/45210908726) 运行在此 SHA，`public-docs` 与 `task03-report` 均成功 |
| 工作流修正 | 前一工程提交 `5aab77e` 的 pip 命令触发 YAML 解析错误。改为折叠块后，本地解析通过，并在 `b02f455` 确认 Actions 已实际调度两个作业 |
| 最终交付范围 | 报告器、工作流修正和本验收文档三次提交；对同一 Base 为 **21 个提交、78 个变更文件**。包含前期 Task03 和学习归档 |
| 最新 Head、CI 编号与结论 | [PR #1 交付状态](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/pull/1) 与 [Checks](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/pull/1/checks) 记录最终 SHA 和对应实际运行。发布文档的提交可从其 [Git 历史](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/commits/docs/repository-organization-20261123/reports/repository_organization_20261123/final_release_checklist.md) 定位 |
| 人工审查 | PR 开放，人工 Review 列表为空。本轮验收供人工审查，未登记 APPROVED |
| 本地测试 | Python 3.9.13，25 项标准库、16 项既有 PyTorch、8 项 Task03 行为测试通过。8 项 Task03 在 `python -O` 下独立重跑通过。53 个文档入口、694 个本地引用、YAML 解析与 Git 差异检查通过 |
| 远程测试范围 | `public-docs` 执行轻量文档、注册表、跟踪边界和标准库测试；`task03-report` 使用 Python 3.11 与固定版本的报告依赖，在 `-O` 下执行 8 项合成测试。既有 16 项 PyTorch 测试为本地证据 |

本轮使用原始三份公开类别表和训练历史复核新验证规则。三个种子分别有 22、15、30 个 epoch，最佳为 14、7、24，采样顺序一致。逐类指标按原有独立复算文件核对；未重新取得真实 logits。另核对 4 个冻结数据 SHA-256、102 个本地 Checkpoint 的前后摘要、历史发布清单、48 条题面及 PDF 中 15 行实验指标。Task03 的 18 份公开记录与 42 份服务器原件、逐题档案和 Skill 全文自动加载继续按本页上述证据边界登记。[最新安全复扫](security_audit.md#pr-最新工程提交的独立复扫)
