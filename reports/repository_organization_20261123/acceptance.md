# 科研仓库整理验收 · 2026-11-23

## A. 原始状态

基准为 `95f0047cfbcdea1bce493a6eec6f71b8c2cb53de`，本地工作区干净，实时远端查询与三个本地跟踪引用一致。main 为 `3cd855f7059f5dcdc7a9a64555bfef4c41b6c870`，Task03 为 `7a3dc521cbe31011be89e215177c135cebe410ce`。归档基准包含这两项历史。[前置审计、目录盘点和问题证据](../../docs/repository_audit_20261123.md)

## B–C. 参考原则与目录

研究了五个公开项目的职责分离、显式数据契约、环境说明和复现导航。沿用现有布局，将 `src/`、`scripts/`、`configs/` 作为模型、入口与配置索引，`docs/` 提供协议和注册表，`reports/` 与 `experiments/` 按运行保留证据，`learning_notes/` 保存历史学习记录，`tests/` 与 `tests_torch/` 维持原分工。[参考详情](../../docs/project_organization_references.md) · [整理后的阅读路线](../../docs/README.md)

## D. 文件变更

| 内容 | 文件 |
| --- | --- |
| 双语入口与状态 | [README](../../README.md)、[README.en](../../README.en.md)、[PROGRESS](../../PROGRESS.md)、[CHANGELOG](../../CHANGELOG.md) |
| 导航与注册 | [docs 索引](../../docs/README.md)、[reports 索引](../README.md)、[实验注册表](../../docs/experiment_registry.md) |
| 审计与勘误 | [仓库审计](../../docs/repository_audit_20261123.md)、[开源参考](../../docs/project_organization_references.md)、[48 题勘误](../../docs/fourth_plan_archive_errata.md)、本验收 |
| 维护与检查 | [贡献规范](../../CONTRIBUTING.md)、[项目 Skill](../../.agents/skills/uci-har-experiment-workflow/SKILL.md)、[验证说明](../../docs/verification.md)、[检查入口](../../scripts/check_public_docs.py)、[CI](../../.github/workflows/docs.yml) |

## E. 实验数据检查

四模型与 CNN 九组共用 A42，再加三个 Task03 运行，共 15 个独立运行。指标来源为实验原始 JSON。两份首页和注册表对照原始验证，CNN 按种子复算均值和配对差值，Task03 样本标准差与原始归档一致。GRU 在四个 Seed42 基线中测试 Macro-F1 为 91.9444%，为该对照最高。SE 相对原 CNN 的平均 +0.6575 pp 只在一颗种子为正。Task03 GPU GRU 平均 90.6623%，历史 CPU GRU 保持单独记录。固定划分上的种子波动不足以证明跨划分稳定性；设备及计时条件不同。[数值与逐运行证据](../../docs/experiment_registry.md)

## F–G. 学习归档与 Skill

通过已发布 PDF 文本、LaTeX、CSV 和教学原文核对第 10、12、43 题，新增独立勘误与流程图。历史 PDF、题目、表格、指标及发布清单保持原样。48 个编号及题面可核对，逐题师生原文完整性为 **PARTIAL**。教师总评 48/48 的历史登记继续有效。[勘误](../../docs/fourth_plan_archive_errata.md)

完整阅读并修订 Skill。现在明确先读协议和注册表、后审计及分类执行，训练要求授权和新目录。保留验证选模、最终测试、配置／日志／预测及哈希要求，归档后更新注册表。全新会话自动加载完整指令仍为 **PARTIAL**。[项目 Skill](../../.agents/skills/uci-har-experiment-workflow/SKILL.md)

## H. 检查和 CI

本地运行 50 个公开入口及 641 个本地链接检查、双语指标与 15 行注册字段、JSON 与 5 份 YAML/YML 解析、暂存边界及历史产物 Git 差异。原有 25 项标准库测试与 16 项 PyTorch 合成测试通过。CI 保持现有轻量工作流，精确允许跟踪项目 Skill，失败于其他受保护目录或产物。CI 不下载真实数据或运行训练。PR 的实时检查状态以 GitHub 为准。

## I. Git 交付

提交位于独立 [docs/repository-organization-20261123](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/tree/docs/repository-organization-20261123) 分支。该分支包含此前未合入 main 的 Task03 与最终归档历史。用 `git log --diff-filter=A --format=%H -- reports/repository_organization_20261123/acceptance.md` 查看本页提交，用 `git ls-remote origin` 核对发布 SHA 与受保护分支；[人工审查 PR](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/pulls?q=is%3Apr+head%3Adocs%2Frepository-organization-20261123) 随分支提交审查。

## J. 证据缺口

- **PARTIAL · Task03**：60 项哈希清单的 18 项公开副本可重新复核，42 项服务器原件（包括权重、预测和日志）沿用历史核验。本轮未现场复核服务器。
- **PARTIAL · 逐题原文**：原题完整，保存的同主题学生原答与定向教师摘要覆盖有限。
- **PARTIAL · Skill 自动加载**：记录显示元数据发现及显式读取，缺少新会话自动加载完整指令的证据。
