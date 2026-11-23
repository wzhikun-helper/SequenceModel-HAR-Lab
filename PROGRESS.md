# 项目进度

更新于 2026-11-23。本页是当前状态的权威入口。单次运行、指标与来源见 [实验注册表](docs/experiment_registry.md)，历史时点见 [CHANGELOG](CHANGELOG.md)。

| 维度 | 当前状态 | 依据 |
| --- | --- | --- |
| 实验执行 | 数据实践、四模型 Seed42、CNN 九组配对（复用 A42）、Task03 GRU GPU 三种子已完成 | [数据审计与全部运行](reports/README.md) |
| 工程验收 | 原始运行中的阶段检查、历史测试及独立复算有档案。轻量 CI 的覆盖范围单列 | [轻量和真实数据复现](docs/verification.md) · [Task03 工程验收](reports/gru_multiseed_task03_20261123/acceptance.md) |
| 学习验收 | Day 01 12/12、Day 02 Lesson 01–02 理论通过；第四次规划 48/48 与 Task03 结果理解通过据教师反馈登记 | [Day 01 问答](learning_notes/day01/questions_01_12.md) · [Day 02 记录](learning_notes/day02/README.md) · [最终学习记录](learning_notes/fourth_plan_final_archive.md) |
| 逐题证据 | PARTIAL。原题与答案 48/48 已映射；历史逐题对话、原始批改及复测覆盖不全 | [台账](reports/fourth_plan_final_archive_20261123/question_mapping.csv) · [勘误](docs/fourth_plan_archive_errata.md) |
| 报告归档 | 已发布 13 页中文 LaTeX/PDF，归档时逐页检查并校验 SHA-256 | [最终归档](reports/fourth_plan_final_archive_20261123/README.md) |
| Task03 服务器原件 | PARTIAL。60 项中 18 项公开副本可复核，42 项未独立重算；权重哈希与公开清单已交叉核对 | [证据清单](reports/fourth_plan_final_archive_20261123/evidence_manifest.json) |
| Skill | 显式读取、真实报告生成和 Task03 训练使用有记录。全新会话自动加载完整指令仍未证实（PARTIAL） | [报告调用](reports/fourth_plan_final_archive_20261123/skill_usage.md) · [Task03 使用记录](reports/gru_multiseed_task03_20261123/skill.md) |

## 下一阶段研究

1. 预先固定新受试者划分、种子和评价准则，再检验跨划分稳定性。
2. 按受试者整理坐站错分并追踪错误来源。
3. 用共同硬件、精度、框架和计时边界比较成本，另行记录模型容量。

[项目治理核验](reports/repository_organization_20261123/acceptance.md) · [PR 最终清单](reports/repository_organization_20261123/final_release_checklist.md)

Task03 清单已逐项登记，18 个公开 Git 文件的哈希均匹配，42 个服务器原件仍为 PARTIAL。[60 项状态表](reports/repository_organization_20261123/task03_evidence_status.csv)

48 题历史原件重新分级为 0 FULL、9 PARTIAL、39 MISSING。总评 48/48 维持历史登记。[逐题状态表](reports/repository_organization_20261123/question_mapping.csv)

独立新会话已验证 Skill 元数据自动发现，并执行只读核验。全文由会话主动读取，完整指令自动注入仍为 PARTIAL。[实际会话复核](reports/repository_organization_20261123/skill_verification.md)
