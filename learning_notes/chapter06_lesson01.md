# 第六章 Lesson 01 · 项目 Skill 与报告复核

本轮使用 [UCI HAR 项目 Skill](../.agents/skills/uci-har-experiment-workflow/SKILL.md) 生成了[中文报告初稿](../reports/chapter06_lesson01_research_draft/report.pdf)。调用读取历史记录，训练入口供未来单独授权的任务使用。本轮未通过 Skill 发起正式训练，等待教师验收。

## 为什么 SE 的均值提高还不足以证明稳定有效？

本次可访问的记录包括 [第五章学习笔记](chapter05_cnn_ablation.md)、[消融总结](../reports/cnn_ablation_20261122/README.md) 与[配对差值](../reports/cnn_ablation_20261122/paired.csv)。学生最初的逐字回答、原回答的具体问题、教师原话以及学生复答尚无可引用记录。以下为工程复核形成的理解对照。

| 环节 | 证据与理解 |
| --- | --- |
| 容易产生的初步推断 | 看到 SE 平均 Macro-F1 高于原 CNN，容易把平均改善理解成换一个种子也会改善。此项是待讨论的推断。 |
| 实验依据 | 按 Seed42、43、44 配对，SE−原 CNN 为 −0.1041、+2.5970、−0.5204 个百分点。SE 的三种子均值为 90.1198%，原 CNN 为 89.4623%，等参数量残差 MLP 为 90.1484%。 |
| 修正后的工程理解 | 平均改善主要由 Seed43 驱动，三组配对只有一组高于原 CNN。SE 对等参数 MLP 的差值也有正有负。结论限于同一固定受试者划分上的三个种子。 |
| 待回答问题 | 增加预先约定的种子和受试者划分后，增益方向是否更一致？变动主要来自哪些受试者及活动类别？ |

[实际调用、命令和证据索引](../reports/chapter06_lesson01_research_draft/README.md)
