# SequenceModel-HAR-Lab

**跨受试者人体活动识别 · 可追溯的数据准备与序列模型实验**

简体中文 · [English](README.en.md)

[![Documentation checks](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/workflows/docs.yml/badge.svg)](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab/actions/workflows/docs.yml)

基于 UCI HAR 手机传感器信号，研究多通道时序数据的表示、预处理与独立评价。当前已完成数据基础阶段：官方数据校验、跨受试者划分、训练集标准化和真实窗口可视化。序列模型对比尚未开始。

**128 × 9** 每窗口输入 · **50 Hz** 采样率 · **6** 类活动 · **30** 位受试者

[复现指南](docs/reproducing_day01.md) · [数据协议](docs/data_protocol.md) · [文档导航](docs/README.md) · [项目进度](PROGRESS.md) · [更新记录](CHANGELOG.md)

## 项目内容

| 已完成 | 实现与证据 |
| --- | --- |
| 官方数据获取 | UCI来源、ZIP成员CRC、本地SHA-256、安全解压 |
| 窗口与标签审计 | 全部18路信号文件、10,299个窗口、六类活动与受试者ID |
| 跨受试者协议 | 训练17人、验证4人、测试9人；保留官方测试集 |
| 标准化与复核 | 仅最终训练集拟合；独立复核保存数组与原始行的对应关系 |

[数据审计报告](reports/day01_data_20261026_run02/day01_data_audit.md) · [独立复核结果](reports/day01_data_20261026_run02/independent_verification.json)

## 数据协议

使用官方已预处理的九路 `Inertial Signals`，保留时间顺序；不把561维工程特征当作序列输入。数组布局为 **N × 128 × 9**，标签保留官方1—6。

| 集合 | 人数 | 窗口数 | 划分规则 |
| --- | ---: | ---: | --- |
| 训练 | 17 | 6,037 | 官方训练人员，排除验证集 |
| 验证 | 4 | 1,315 | 官方训练ID升序前四人：1、3、5、6 |
| 测试 | 9 | 2,947 | 官方测试人员、顺序与标签完整保留 |

三集合受试者互不重叠；标准化参数仅从最终训练集拟合。[人员ID、类别分布与标准化定义](docs/data_protocol.md)。

## 真实信号

WALKING与STANDING各展示一个最终训练窗口，均来自受试者7，保留g与rad/s物理单位，对应通道使用相同纵轴范围。这是样本观察，不是类别总体比较或模型性能结果。

<details>
<summary>展开九路信号对照图 · WALKING / STANDING</summary>

<table>
  <tr><th>WALKING · 官方训练第1397行</th><th>STANDING · 官方训练第1316行</th></tr>
  <tr>
    <td><img src="docs/day01/walking_nine_channels.png" alt="WALKING窗口九路真实信号" width="420"></td>
    <td><img src="docs/day01/standing_nine_channels.png" alt="STANDING窗口九路真实信号" width="420"></td>
  </tr>
</table>

[完整图表说明与来源校验](docs/day01/README.md)

</details>

## 使用与复现

```powershell
git clone https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git
cd SequenceModel-HAR-Lab
python -B scripts/check_public_docs.py
```

以上检查仅用Python标准库，不下载数据。完整的数据准备命令、已验证依赖和新运行目录约定见[Day 01复现指南](docs/reproducing_day01.md)。数据流程无需GPU或PyTorch。

## 验证状态

| 验证层 | 最新证据 | 范围 |
| --- | --- | --- |
| 轻量CI | 文档检查与25个合成契约测试；运行状态见上方Actions标识 | 不下载完整数据、不训练、不需要第三方包或GPU |
| 独立环境真实数据复现 | 2026-10-31已完整运行并通过，与旧运行的数值及PNG像素一致 | 新venv、新运行ID、官方重新下载、实际审计/标准化/绘图/逐值复核 |

[整改报告与实际运行证据](reports/remediation_round1_20261031/README.md) · [两层验证的范围与限制](docs/verification.md)。轻量CI通过不能替代真实数据完整复现通过。

| 目录 | 内容 |
| --- | --- |
| [docs/](docs/README.md) | 数据协议、复现指南、代表图与小型元数据 |
| [scripts/](scripts/README.md) | 下载、审计、绘图和验证入口 |
| [learning_notes/](learning_notes/day01/README.md) | 知识笔记、理解题与原始教学记录 |
| [reports/](reports/README.md) | 审计结果、校验清单与历史执行档案 |

数据集、处理数组、模型权重和本地日志不进入版本管理。[变更与贡献约定](CONTRIBUTING.md)。

## 当前阶段与后续计划

数据基础与Day 01学习验收已完成。CNN、GRU、Transformer和Mamba的训练、统一指标对比与消融分析均为后续计划；**尚无模型训练结果**。第四章与Day 02未开始，详见[进度记录](PROGRESS.md)。

## 数据引用

Reyes-Ortiz et al. (2013). *Human Activity Recognition Using Smartphones*. UCI Machine Learning Repository. [DOI: 10.24432/C54S4K](https://doi.org/10.24432/C54S4K)。

[官方数据页](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones) · [来源、校验信息与已知限制](reports/day01_data_20261026_run02/download_provenance.json)
