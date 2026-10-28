# Day 01 工程证据与使用说明

本次只关联既有结果并核对路径/哈希，不重新执行数据实验或训练。

| 证据 | 本地文件链接（相对项目根目录） |
| --- | --- |
| data_audit | [reports/day01_data_20261026_run02/day01_data_audit.md](../../reports/day01_data_20261026_run02/day01_data_audit.md) |
| execution_index | [reports/day01_data_20261026_run02/execution_log.md](../../reports/day01_data_20261026_run02/execution_log.md) |
| download_provenance | [reports/day01_data_20261026_run02/download_provenance.json](../../reports/day01_data_20261026_run02/download_provenance.json) |
| archive_integrity | [reports/day01_data_20261026_run02/archive_integrity.json](../../reports/day01_data_20261026_run02/archive_integrity.json) |
| independent_verification | [reports/day01_data_20261026_run02/independent_verification.json](../../reports/day01_data_20261026_run02/independent_verification.json) |
| split_metadata | [data/processed/day01_data_20261026_run02_audit02/splits/split_metadata.json](../../data/processed/day01_data_20261026_run02_audit02/splits/split_metadata.json) |
| sample_manifest | [data/processed/day01_data_20261026_run02_audit02/splits/sample_manifest.csv](../../data/processed/day01_data_20261026_run02_audit02/splits/sample_manifest.csv) |
| scaler | [data/processed/day01_data_20261026_run02_audit02/scaler_train_only.json](../../data/processed/day01_data_20261026_run02_audit02/scaler_train_only.json) |
| walking_png | [outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.png](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.png) |
| walking_pdf | [outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.pdf](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.pdf) |
| standing_png | [outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.png](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.png) |
| standing_pdf | [outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.pdf](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.pdf) |

## 划分与标准化说明

验证集为官方训练受试者ID升序前4人：1、3、5、6。训练17人/6037窗，验证4人/1315窗，测试9人/2947窗，官方测试受试者与行顺序保持不变。
每通道以最终训练集6037×128=772736个值拟合float64均值和总体标准差（ddof=0），统一用于三集合，转换结果另存float32。完整参数仍在上表原路径；本次未重新拟合。
数据布局N×128×9；通道顺序body_acc_xyz、body_gyro_xyz、total_acc_xyz，原标签1—6。归档没有更改这些约定。

## 真实信号图

WALKING：受试者7、官方训练第1397行；STANDING：受试者7、官方训练第1316行。每图一个实测窗口，仅支持样本观察，不推广为总体结论。

![WALKING 九路信号](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.png)

![STANDING 九路信号](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.png)

## 可追踪文档副本

选定WALKING/STANDING图和划分/标准化元数据可在线查看的副本见[Day 01文档证据](../../docs/day01/README.md)。原文件保留本地，副本已核对来源与哈希。

## 同步边界

`data/`、`outputs/`、`logs/`继续被原.gitignore排除。上述原始证据链接在本机有效；GitHub不含原始数据/数组和原outputs目录。docs/day01只提供明确选定的两张图及小型元数据副本，其余本机路径不会自动在线可见。
历史记录中的官方校验值未提供、首次网络权限失败、首次序列化失败和原版绘图门禁缺失等限制仍以数据审计报告为准，本次不将它们改写成通过。
