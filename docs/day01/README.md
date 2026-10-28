# Day 01 可在GitHub查看的工程证据

这里只保存两张代表性实验图和小型划分/标准化元数据，不包含原始数据集、窗口数组或模型权重。所有副本与原文件SHA-256一致，见[副本来源清单](asset_provenance.json)。原文件未修改。

## 数据与划分

UCI HAR官方数据实践：每窗口128个采样点×9通道，50 Hz，采集窗口2.56秒；采样点时间0—2.54秒。原始标签1—6保留。

| 集合 | 受试者人数 | 窗口数 |
| --- | ---: | ---: |
| 最终训练 | 17 | 6037 |
| 验证 | 4 | 1315 |
| 官方测试 | 9 | 2947 |

验证受试者是官方训练ID升序前4人：1、3、5、6。三个集合受试者两两不重叠，官方测试划分保持不变。完整人员ID和类别计数见[划分元数据](split_metadata.json)。逐窗口清单和标准化数组保留本地，不上传。

每通道仅用最终训练集6037×128个值拟合float64均值和总体标准差（ddof=0），同一参数用于训练、验证、测试，转换结果另存float32。参数见[训练集标准化参数](standardization_train_only.json)。本次只复制既有参数，未重新拟合。

## WALKING：受试者7，官方训练第1397行

![WALKING九路真实信号](walking_nine_channels.png)

## STANDING：受试者7，官方训练第1316行

![STANDING九路真实信号](standing_nine_channels.png)

每图只有一个指定的最终训练窗口；九路信号保留g或rad/s物理单位，对应通道使用相同纵轴范围。图只用于样本观察，不据此推断所有活动样本的普遍差异，也不表示模型性能。

来源：[UCI Human Activity Recognition Using Smartphones](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones)，Reyes-Ortiz等，DOI 10.24432/C54S4K。图由本项目既有绘图脚本生成。

完整历史说明见[数据审计报告](../../reports/day01_data_20261026_run02/day01_data_audit.md)及[独立复核记录](../../reports/day01_data_20261026_run02/independent_verification.json)。历史审计内指向data/outputs/logs的路径只在本机有效，本页提供了选定代表性图的可追踪副本。
