# SequenceModel-HAR-Lab

**面向跨受试者人体活动识别的时序分类实验与学习记录。**

Subject-disjoint time-series classification on UCI HAR, with traceable data preparation and experiment records.

本项目以手机加速度计与陀螺仪的九路信号为输入，逐步研究序列模型如何识别人体活动。目前已完成官方数据获取、窗口审计、固定人员划分、训练集标准化与真实信号可视化；CNN、GRU、Transformer 和 Mamba 的实现与对比属于后续计划，**尚无模型训练结果**。

[数据协议](docs/data_protocol.md) · [复现指南](docs/reproducing_day01.md) · [真实信号](docs/day01/README.md) · [学习笔记](learning_notes/day01/README.md) · [进度](PROGRESS.md) · [审计记录](reports/README.md)

## 已完成的工作

| 内容 | 当前证据 |
| --- | --- |
| 官方来源与完整性 | UCI 官方 ZIP；本地 SHA-256、两层压缩包全部成员 CRC 检查 |
| 数据结构 | 10,299 个窗口；每窗口 **128 个时间点 × 9 个通道**；六类活动 |
| 跨受试者划分 | 训练、验证、测试受试者互不重叠；保留官方测试划分 |
| 标准化 | 仅最终训练集拟合各通道参数，再应用于验证集与测试集 |
| 产物验证 | 保存数组与原始文本、划分记录、标准化参数逐值复核 |

这些是数据准备与工程验证结果，不代表模型分类性能。详细证据见[数据审计报告](reports/day01_data_20261026_run02/day01_data_audit.md)与[独立复核结果](reports/day01_data_20261026_run02/independent_verification.json)。

## 数据与评估协议

数据采用 [UCI HAR](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones) 官方 `Inertial Signals`，保留窗口内的时间顺序。六类活动为步行、上楼、下楼、坐、站和躺；本阶段不使用官方 561 维工程特征作为序列输入。

| 集合 | 受试者人数 | 窗口数 | 选择规则 |
| --- | ---: | ---: | --- |
| 训练 | 17 | 6,037 | 官方训练受试者中，除验证人员之外的全部人员 |
| 验证 | 4 | 1,315 | 官方训练受试者 ID 升序前四人：**1、3、5、6** |
| 测试 | 9 | 2,947 | 保留官方测试人员、窗口顺序与标签 |

每窗口采样率 50 Hz、时长 2.56 秒。标准化沿训练窗口和时间两个轴计算每通道均值、总体标准差；验证集与测试集不参与拟合。人员 ID、类别分布、通道顺序及标签约定见[完整数据协议](docs/data_protocol.md)。

## 两个真实窗口

以下两图来自最终训练集的同一受试者 7；对应通道共用纵轴范围，保留 g 与 rad/s 物理单位。

<table>
  <tr><th>WALKING · 官方训练第 1397 行</th><th>STANDING · 官方训练第 1316 行</th></tr>
  <tr>
    <td><img src="docs/day01/walking_nine_channels.png" alt="WALKING 窗口的九路加速度与角速度信号" width="440"></td>
    <td><img src="docs/day01/standing_nine_channels.png" alt="STANDING 窗口的九路加速度与角速度信号" width="440"></td>
  </tr>
</table>

这两个指定样本用于展示窗口结构与信号变化，不据此推断整个活动类别的普遍差异。[查看原图说明与来源校验](docs/day01/README.md)。

## 快速开始

无需下载数据即可阅读文档、检查公开入口：

```powershell
git clone https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git
cd SequenceModel-HAR-Lab
python -B scripts/check_public_docs.py
```

如需复现数据准备流程，请按[复现指南](docs/reproducing_day01.md)配置独立环境，使用新的运行 ID 依次执行下载、审计、绘图与验证。数据脚本使用 NumPy、Matplotlib 和 Pillow，**不依赖 GPU 或模型训练**。

## 仓库导航

```text
SequenceModel-HAR-Lab/
├── docs/                     # 数据协议、复现指南、代表性信号图与小型元数据
├── learning_notes/day01/     # 概念笔记、理解题记录与教学原文
├── reports/                  # 数据审计、校验结果及历史执行档案
├── scripts/                  # 数据准备、绘图、验证与历史归档脚本
├── requirements-data.txt     # 已验证数据流程的直接依赖版本
└── PROGRESS.md               # 当前阶段、已完成事项与后续路线
```

原始数据、处理数组、权重和本地日志不进入版本管理；文档中仅保留两张代表图及必要的划分、标准化元数据。历史报告含执行时的本机路径，使用方式见[报告索引](reports/README.md)。

## 后续路线

- [x] Day 01：数据理解、跨受试者划分、预处理与审计。
- [ ] 序列模型：CNN、GRU、Transformer、Mamba 的实现与训练。
- [ ] 在统一数据协议下记录分类指标和模型对比。
- [ ] 根据实验结果开展误差分析与模块消融。

第四章与 Day 02 尚未开始。本轮更新仅整理文档与公开展示，不增加或暗示未执行的实验。

## 数据引用

Reyes-Ortiz, J., Anguita, D., Ghio, A., Oneto, L., & Parra, X. (2013). *Human Activity Recognition Using Smartphones*. UCI Machine Learning Repository. [DOI: 10.24432/C54S4K](https://doi.org/10.24432/C54S4K)。

数据使用与署名要求请以官方来源为准；下载来源、校验信息与已知限制记录在[数据审计报告](reports/day01_data_20261026_run02/day01_data_audit.md)中。
