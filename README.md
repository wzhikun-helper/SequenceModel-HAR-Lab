# SequenceModel-HAR-Lab

**用同一受试者划分研究时序活动分类、参数量匹配消融与训练随机性。**

简体中文 · [English](README.en.md) · [阅读路线](docs/README.md) · [实验注册表](docs/experiment_registry.md) · [当前进度](PROGRESS.md)

## 数据与评价

[UCI HAR](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones) 包含 30 名参与者的 10,299 个惯性窗口。每个窗口为 **128 × 9**，采样频率 **50 Hz**，预测六类活动。训练／验证／官方测试分别为 **17／4／9** 人、**6,037／1,315／2,947** 窗口，受试者互斥。通道标准化只在最终训练集拟合。验证 Macro-F1 优先选模，同分比较验证 Loss，官方测试用于最终评价。[冻结协议、标签与真实信号](docs/data_protocol.md)

## 四模型 Seed42

CNN 使用局部卷积，GRU 使用门控状态，Transformer 使用自注意力与位置编码，Mamba 使用选择性状态空间。

| 模型 | Accuracy | Macro-F1 | Loss | 参数量 | 设备 |
| --- | --- | --- | --- | --- | --- |
| CNN A | 89.7523% | 89.8202% | 0.290570 | 27,270 | CPU |
| GRU B | 91.8222% | 91.9444% | 0.255319 | 14,790 | CPU |
| Transformer C | 88.0896% | 88.0326% | 0.425905 | 34,502 | CPU |
| Mamba D | 88.7004% | 88.8610% | 0.379041 | 33,670 | RTX 3090 |

四组共用官方测试集。GRU 在本次四个运行中 Macro-F1 最高。单种子无法确定架构的一般排名，CPU 与 GPU 的训练时间缺少同硬件可比性。[逐运行配置与证据](docs/experiment_registry.md)

## CNN 三种子消融

Macro-F1 单位为百分比。残差 MLP 与 SE 有相同的新增参数量。

| 组别 | Seed42 | Seed43 | Seed44 | 均值 |
| --- | --- | --- | --- | --- |
| A · 原 CNN | 89.8202 | 88.5241 | 90.0424 | 89.4623 |
| B · CNN + SE | 89.7161 | 91.1212 | 89.5221 | 90.1198 |
| C · CNN + 残差 MLP | 89.6185 | 92.1449 | 88.6817 | 90.1484 |

SE 相对原 CNN 平均 **+0.6575 pp**，只有 Seed43 改善；相对等参数残差 MLP 平均 **−0.0286 pp**。当前缺少稳定独立增益的证据。[配对、样本标准差和原始报告](docs/experiment_registry.md#cnn-三种子消融)

## GRU Task03 GPU 三种子

| 种子 | Accuracy | Macro-F1 | Loss |
| --- | --- | --- | --- |
| 42 | 91.2793% | 91.3919% | 0.362237 |
| 43 | 89.7523% | 89.8447% | 0.313432 |
| 44 | 90.7024% | 90.7504% | 0.352929 |
| 均值 | 90.5780% | 90.6623% | 0.342866 |

本组为 RTX 3090 上的独立实验。历史 CPU GRU Seed42 保持独立；硬件和软件同时变化，无法单独归因。三种子共享受试者划分，只反映该划分下的训练随机性；SITTING 始终是 F1 最低类别。[Task03 逐类结果](reports/gru_multiseed_task03_20261123/comparison.md)

## 阅读与复现

```sh
git clone https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git
cd SequenceModel-HAR-Lab
python -B scripts/check_public_docs.py
python -I -S -B -m unittest discover -s tests -v
```

文档检查与 27 项标准库测试构成轻量 CI；其中包含数据契约和发布回归检查。16 项 PyTorch 合成测试另行运行。完整真实数据复现有独立历史记录。准备环境和依赖请按 [Day 01 复现指南](docs/reproducing_day01.md)、[模型入口](scripts/README.md) 及 [Task03 协议](docs/gru_task03_protocol.md) 选择，CUDA 构建参见 [Mamba 环境](experiments/mamba_baseline_d_seed42_20261122/docs/environment.md)。

| 入口 | 查找内容 |
| --- | --- |
| [docs/](docs/README.md) | 数据协议、环境、复现与实验注册 |
| [src/](src/har_lab) · [scripts/](scripts/README.md) · [configs/](configs/gru_task03) | 模型、执行入口和版本化配置 |
| [reports/](reports/README.md) · [experiments/](experiments/mamba_baseline_d_seed42_20261122/README.md) | 公开归档、复算记录、科研图表和 Mamba 实验 |
| [学习记录](learning_notes/fourth_plan_final_archive.md) · [项目 Skill](.agents/skills/uci-har-experiment-workflow/SKILL.md) | 教学验收与工作流 |
| [贡献说明](CONTRIBUTING.md) · [更新记录](CHANGELOG.md) | 新运行登记和保护规则 |

## 证据等级与后续研究

**PASS** 仅用于本次实查通过的范围。**PARTIAL** 表示原件缺口。Task03 的 60 项运行清单中，18 项公开副本可复核，42 项仍依赖服务器历史校验。教师总评 48/48 已登记，逐题对话覆盖仍为 PARTIAL。[最终报告与 48 题](reports/fourth_plan_final_archive_20261123/README.md)

后续方向为多受试者划分、多随机种子、分受试者分析坐站错分，以及在共同环境中测量运行成本。[项目进度和证据缺口](PROGRESS.md)

数据引用：[Human Activity Recognition Using Smartphones · DOI 10.24432/C54S4K](https://doi.org/10.24432/C54S4K)。
