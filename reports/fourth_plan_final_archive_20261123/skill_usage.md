# 项目 Skill 使用实录

宿主在本对话中提供项目 Skill 的名称、描述和路径。按本次任务的明确要求，使用 PowerShell `Get-Content -Raw -Encoding utf8` 主动读取[完整项目 Skill](../../.agents/skills/uci-har-experiment-workflow/SKILL.md)，并以 `Get-FileHash` 核对整份文件。SHA-256 为 `c868f07a3d3372c8f7931310ed9086ba9226758f3404cd6498427323a01b5647`。完整指令来自主动读取，宿主自动提供的内容为元数据。

阅读了其引用的[数据协议](../../docs/data_protocol.md)、[报告索引](../README.md)、[脚本索引](../../scripts/README.md)、[消融复现协议](../cnn_ablation_20261122/reproducibility.md)、[Mamba 归档](../../experiments/mamba_baseline_d_seed42_20261122/README.md)，另读 Task03 协议和 `ml-experiment-audit` 的冻结保护、分类与论文产物审计指南，使用 `pdf` 工作流作视觉检查。

实际执行了归档路径。报告汇总复用了 `scripts/build_har_research_report.py` 中只读的 `collect` 校验，扩展读取 Task03 已存记录，复用原始图。以 `pdftotext -layout` 提取原题，再以 XeLaTeX 编译并使用 Poppler 渲染，执行文档检查、合成测试和发布范围核验。脚本在独立归档目录生成表格与报告，模型训练入口、正式测试和推理均未运行。

Task03 原工程中的 Skill 读取与训练调用独立保存于 [Task03 Skill 证据](../gru_multiseed_task03_20261123/skill.md)，不计作本次最终归档的一次训练。检查执行结果与证据缺口见 [核验结果](verification.json)。
