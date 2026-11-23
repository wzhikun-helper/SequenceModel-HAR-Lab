# 仓库整理前审计 · 2026-11-23

审计对象是归档基准 `95f0047cfbcdea1bce493a6eec6f71b8c2cb53de`。先执行 `git status --short --branch`、`git branch -avv`、`git log --graph --decorate --oneline --all`、`git remote -v`、`git ls-files`、`git diff --check`、`git ls-remote origin`，再以 Git 树、跟踪文件和公开实验档案核对内容。

| 分支 | 开始时本地 | GitHub 实时查询 |
| --- | --- | --- |
| main | `3cd855f7059f5dcdc7a9a64555bfef4c41b6c870` | 同一 SHA；默认分支 |
| experiment/gru-multiseed-task03 | 本地仅有 origin 跟踪引用 | `7a3dc521cbe31011be89e215177c135cebe410ce` |
| docs/fourth-plan-final-archive-20261123 | 当前分支，跟踪同名 origin | `95f0047cfbcdea1bce493a6eec6f71b8c2cb53de` |

本地工作区干净，基线领先关系由祖先检查确认。归档基准包含 Task03，Task03 包含 main，远程尚无整理分支。整理使用独立 `docs/repository-organization-20261123`。原远程为 [SequenceModel-HAR-Lab](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab)。

## 目录和文件清点

Git 树共 **453 文件、6,509,577 字节**。一级／二级目录按跟踪内容列出。根目录另有入口文件及依赖清单；测试代码直接位于两个测试目录。

| 一级 | 二级目录或根内入口 |
| --- | --- |
| `.agents/`、`.github/` | `skills/`、`workflows/` |
| `configs/`、`src/` | `gru_task03/`、`har_lab/` |
| `docs/` | `day01/` 和 Markdown 指南 |
| `experiments/` | `mamba_baseline_d_seed42_20261122/` |
| `learning_notes/` | `day01/`、`day02/` 与跨阶段笔记 |
| `scripts/` | `templates/` 和入口脚本 |
| `tests/`、`tests_torch/` | 各为平铺测试 |
| `reports/` · 数据／历史 | `day01_data_20261026_run01/`、`day01_data_20261026_run02/`、`day01_archive_20261028_run01/`、`day01_github_preflight_20261028_run01/`、`day01_github_sync_20261028_run01/`、`day01_repro_20261031_run01/`、`remediation_round1_20261031/` |
| `reports/` · 实验 | `day02_cnn_20261111_run01/`、`cnn_baseline_seed42_20261119_run01/`、`gru_baseline_preflight_20261121/`、`gru_baseline_seed42_20261121_run01/`、`transformer_preflight_20261122/`、`transformer_baseline_seed42_20261122_run01/`、`mamba_l0_20261122/`、`cnn_ablation_audit_20261122/`、`cnn_ablation_20261122/`、`gru_multiseed_task03_20261123/` |
| `reports/` · 研究报告 | `chapter06_lesson01_research_draft/`、`chapter06_lesson02_task01_revision/`、`fourth_plan_final_archive_20261123/` |

本地还有 `.git/`、`.venv/`、`checkpoints/`、`data/`（`raw/`、`processed/`）、`logs/`、`models/`、`outputs/`（`figures/`）。运行子目录为本地证据；扫描不打开认证文件、权重、预测原件或数据数组。

| 后缀 | 数量 |
| --- | --- |
| JSON／Markdown／CSV／Python | 186／75／72／48 |
| PNG／PDF／TeX／TXT | 22／12／9／8 |
| 无后缀／YAML／YML／SVG | 6／4／1／4 |
| SHA256／Shell／Diff／PowerShell | 2／2／1／1 |

最大文件是 WALKING 图（676,076 B），其次是 STANDING 图（403,786 B）和最终归档 PDF（373,459 B）。同 Git blob 有 18 组、23 个额外副本，例如 Task03 原配置快照和报告表格。保留这些历史副本以维持复现和哈希。

## 发现与整改

| 状态 | 证据 | 整改 |
| --- | --- | --- |
| 待修正 | 基准的英文首页同时写有 Mamba 已运行和未运行，并缺 Task03；中文首页和进度仍混有历史“待验收”状态 | 双语首页同步数值与边界，当前状态集中于 PROGRESS |
| 待修正 | CHANGELOG 缺 11 月 23 日；reports 索引未列 Task03 和最终归档；原 docs 路线偏重 Day 01 | 补实存入口和已完成记录，新增统一实验注册表 |
| 待修正 | CI 禁止整个 `.agents/`，与已追踪项目 `SKILL.md` 冲突 | 精确豁免项目 Skill，并覆盖常见运行、数据、权重及缓存 |
| PASS（链接路径） | 75 份跟踪 Markdown、570 个可解析本地路径，目标全部存在 | 现有入口检查外，保护新增导航与注册表。任意页面锚点和外部站点可用性不包含在此计数 |
| PASS（跟踪边界） | 跟踪路径与后缀扫描未发现原始数据、权重、运行日志或缓存；公开逐窗口预测 CSV 按现有实验档案保留 | 区分已发布小型证据与机器原始 stdout/服务器预测 |
| PARTIAL（敏感性） | 跟踪文本常见私钥和令牌模式未命中；15 个文件含历史机器路径，历史提交与二进制私人元数据未遍历扫描 | 不传播本机路径值；新提交显式列入文档并单独审查 |
| PARTIAL（历史证据） | Task03 60 项仅 18 项公开副本可重新核对，42 项仍依赖服务器历史清单。教师 48/48 与逐题原件覆盖范围不同 | 单列缺口，保持工程、学习、公开归档与源文件复核的状态独立 |
| 待修正 | 最终报告第 10 题历史复答与说明连读，第 12 题把判定放入“教师纠正”，第 43 题正文为箭头串 | 以单独勘误说明来源与表达，保留原 PDF、CSV 和发布清单 |

实读了双语首页、PROGRESS、CHANGELOG、CONTRIBUTING、docs 与 reports 索引、项目 Skill、四个基线报告、CNN 消融、Task03 正式报告和第四次学习规划最终归档。各归档中的历史阶段文字以其当时日期解释。
