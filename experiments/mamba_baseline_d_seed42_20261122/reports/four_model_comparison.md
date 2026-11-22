# UCI HAR Seed42 四模型对照

| 模型 | Accuracy | Macro-F1 | Loss | 参数量 | 最佳 Epoch | 实际 Epoch | 设备 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CNN A | 89.7523% | 89.8202% | 0.290570 | 27,270 | 7 | 15 | CPU |
| GRU B | 91.8222% | 91.9444% | 0.255319 | 14,790 | 23 | 30 | CPU |
| Transformer C | 88.0896% | 88.0326% | 0.425905 | 34,502 | 7 | 15 | CPU |
| Mamba D | 88.7004% | 88.8610% | 0.379041 | 33,670 | 3 | 11 | GPU |

## Mamba D 逐类结果

| 活动 | Precision | Recall | F1 | 样本数 |
| --- | ---: | ---: | ---: | ---: |
| WALKING | 94.7257% | 90.5242% | 92.5773% | 496 |
| WALKING_UPSTAIRS | 86.9231% | 95.9660% | 91.2210% | 471 |
| WALKING_DOWNSTAIRS | 93.5185% | 96.1905% | 94.8357% | 420 |
| SITTING | 77.0297% | 79.2261% | 78.1124% | 491 |
| STANDING | 81.0277% | 77.0677% | 78.9981% | 532 |
| LAYING | 100.0000% | 94.9721% | 97.4212% | 537 |

## 错误分布

- SITTING → STANDING 为 96 / 491，STANDING → SITTING 为 116 / 532。
- WALKING → UPSTAIRS / DOWNSTAIRS 为 23 / 24；UPSTAIRS → WALKING / DOWNSTAIRS 为 15 / 4；DOWNSTAIRS → WALKING / UPSTAIRS 为 3 / 13。
- LAYING 正确 510 / 537，其他类误报 LAYING 0 次。
- 此次 Mamba D 的 Macro-F1 相对历史 GRU B 的差值为 -3.0835 个百分点。

四模型沿用同一官方测试集、受试者划分、训练集标准化和选模规则。历史三组来自 CPU，本次 Mamba 来自 GPU，训练耗时的横向比较缺少共同设备条件。模型参数量不同，Seed42 单次实验不足以推断模型家族在其他种子或受试者划分上的表现。混淆矩阵仅描述预测结果，误判机制尚未检验。

[性能与参数量](../figures/performance_parameters.png) · [逐类指标](../figures/class_metrics.png) · [混淆矩阵](../figures/confusion_matrices.png)
