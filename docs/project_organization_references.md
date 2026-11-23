# 科研仓库组织参考

查阅日期为 2026-11-23。以下为参考项目公开文档所示做法，以及本仓库采用的组织原则。

| 参考项目 | 可查的组织做法 | 本仓库对应 |
| --- | --- | --- |
| [tsai](https://github.com/timeseriesAI/tsai#input-data-format) | 公开输入契约，区分库、教程和示例 | 首页列时间点和通道，数据协议记数组布局、通道顺序及分割，学习材料留在学习笔记 |
| [Lightning Hydra Template](https://github.com/ashleve/lightning-hydra-template#project-structure) | 训练与评价入口分开，版本化配置、运行目录和 CI 分离 | 保留 `src/`、`scripts/`、`configs/` 现有职责，登记运行 ID、配置、源码与提交，原始输出留在独立运行目录 |
| [Mila ResearchTemplate](https://github.com/mila-iqia/ResearchTemplate#overview) | 提供独立文档和测试，使用可复现的配置入口 | 区分阅读路线、执行环境与测试范围，显式登记本地证据、轻量 CI 和研究复现的差别 |
| [state-spaces/mamba](https://github.com/state-spaces/mamba#installation) | 硬件、软件依赖及构建方式单独说明，按模型接口提供源码入口 | 从注册表链接官方版本固定的本地归档和 CUDA 环境说明 |
| [ASR1999/HumanActivityRecognition](https://github.com/ASR1999/HumanActivityRecognition#how-to-run-src_uci_har) | 分离信号和特征数据入口，区分训练、评估和展示结果 | 说明本研究使用九路时间窗口，索引数据协议、执行入口、测试指标、复算及图表各自来源 |

借鉴的是目录职责、配置与执行的分离，以及结果的追溯层次。现有程序、依赖管理和历史运行路径继续沿用。
