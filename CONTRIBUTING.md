# 科研项目贡献规范

状态由 [PROGRESS](PROGRESS.md) 维护。先读 [数据协议](docs/data_protocol.md)、[实验注册表](docs/experiment_registry.md) 与 [项目 Skill](.agents/skills/uci-har-experiment-workflow/SKILL.md)。

## 实验与证据

1. 保留既有运行、配置、数据处理参数、失败现场与教学原文。获得授权的新训练使用新 Run ID 和输出目录。运行 ID 可由模型、种子、日期及序号组成。
2. 版本化配置，记录实际执行提交、入口、命令与退出码、环境、种子、数据和 scaler SHA-256。训练和测试受试者隔离，仅训练集拟合预处理；验证集采用预先约定的规则选模，测试集只做选模后的最终评价。
3. 本地保留 Best/Last Checkpoint、原始日志和逐样本预测。记录哈希、字节、重载检查和预测复算范围。公开提交限于源码、配置、允许发布的汇总证据、图表和文档；明细证据按数据发布约定处理。
4. 报告标注指标口径、分割、种子、参数、轮数和设备，区分实际观测、重建及无法复查的原件。图表引用原始记录，私人原件可用 SHA-256 配合适用的存储定位说明。完成归档后更新实验注册表和报告导航；证据缺失标 PARTIAL。
5. 后续勘误创建独立版本或勘误页，保留历史 PDF、发布 SHA-256 和逐字原答。

## 检查与 Git

```sh
python -B scripts/check_public_docs.py
python -I -S -B -m unittest discover -s tests
git diff --check
git status --short --branch
```

已有 PyTorch 环境时，运行 `python -B -m unittest discover -s tests_torch`。轻量 CI 只验证文档、数据契约和跟踪边界，完整真实数据复现单独登记。整理在独立分支上进行，分阶段提交，注明验证范围。审查暂存路径，排除原始数据、权重、凭据、大型日志和环境。通过 PR 交由人工审查。
