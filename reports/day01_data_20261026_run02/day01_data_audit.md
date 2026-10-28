# RadarVisionLLM 第四次学习规划：Day 01 数据实践审计

执行日期：2026-10-26（Asia/Shanghai）。项目根目录：`D:\SequenceModel-HAR-Lab`。

**最终数据实践已完成，独立磁盘复核 PASS；未训练模型。** 当前有效产物 ID 为 `day01_data_20261026_run02_audit02`。早期失败产物仅保留作日志，不得用于后续训练。

## 1. 来源、下载与完整性

- 官方数据页：[UCI Human Activity Recognition Using Smartphones，数据集 240](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones)。DOI：10.24432/C54S4K。
- 下载链接由该官方页面的 Download 链接取得：[UCI 官方 ZIP](https://archive.ics.uci.edu/static/public/240/human%2Bactivity%2Brecognition%2Busing%2Bsmartphones.zip)。没有使用第三方镜像。
- 成功下载时间：11:18:16–11:18:30；HTTP 200；最终主机仍为 `archive.ics.uci.edu`。
- 外层文件：`human_activity_recognition_using_smartphones.zip`，**61,005,872 字节**。
- 外层 SHA-256：`c00b803081a5c797cd5e4b83700a9810b38d53d9d84e01917e090e1fdbc81031`。
- 内层官方文件：`UCI HAR Dataset.zip`，**60,999,314 字节**。
- 内层 SHA-256：`2045e435c955214b38145fb5fa00776c72814f01b203fec405152dac7d5bfeb0`。
- 两层 ZIP 的全部成员均通过 `ZipFile.testzip()` CRC 检查；解压前拒绝路径穿越、链接及重复文件名。解压成员的大小、CRC32、SHA-256 保存于 `archive_integrity.json`。
- **校验边界**：响应未提供 Content-Length、ETag、Last-Modified；所查官方页面未提供发布者 SHA-256。没有完成 HTTP 长度独立比对或官方发布哈希比对。上述 SHA-256 是本地计算结果，ZIP CRC 用于压缩包内部完整性检查，不能冒充发布者签名或哈希。

原始下载与解压均位于 `data/raw/day01_data_20261026_run02/`。数据集根目录：

`data/raw/day01_data_20261026_run02/extracted/UCI HAR Dataset/`

官方压缩包和原始文本保持不变，29 个数据集原始文件的执行前后 SHA-256 一致。此前的启动报告、`.gitignore`、README、启动检查脚本也保持原哈希。

## 2. 真实文件与形状核验

| 官方集合 | 窗口数 | 受试者数 | 九路信号堆叠形状 | 官方工程特征矩阵 |
| --- | ---: | ---: | --- | --- |
| train | 7,352 | 21 | `(7352, 128, 9)` | `(7352, 561)` |
| test | 2,947 | 9 | `(2947, 128, 9)` | `(2947, 561)` |

共 10,299 个窗口、30 位受试者。实际读取了全部 18 个 Inertial Signals 文件，以及两组 y、subject、X、features 和 activity_labels。每路文件的每行均为 128 个数，行数与所属集合的标签、受试者数目一致；九路信号及 561 维工程特征均为有限值，无 NaN/Inf。

通道顺序固定为：

1. `body_acc_x`、`body_acc_y`、`body_acc_z`，单位 g。
2. `body_gyro_x`、`body_gyro_y`、`body_gyro_z`，单位 rad/s。
3. `total_acc_x`、`total_acc_y`、`total_acc_z`，单位 g。

模型输入尚未使用；保存的数据布局为 **窗口 × 时间 × 通道（N×128×9）**。这里的“原始信号”指官方已滤波、去重力/分窗后的物理单位信号，不是连续的未处理传感器记录。官方 561 维工程特征与九路时间序列是不同输入，本次没有把二者混用。

官方采样率为 50 Hz，窗口含 128 个点，覆盖的采集时长为 2.56 秒、官方相邻窗口重叠 50%。图中采样点时间为 `np.arange(128)/50`，首末点 0、2.54 秒，横轴显示到 2.56 秒。没有拼接相邻窗口或伪造时间戳。

## 3. 固定受试者划分

规则在读取类别分布前固定：**将官方训练受试者 ID 升序排序，取前 4 人作验证集，其余作最终训练集，官方测试集全部保留。** 无随机选择，不依赖标签、图形或未来性能；因此不需要随机种子。

| 集合 | 受试者 ID | 人数 | 窗口数 |
| --- | --- | ---: | ---: |
| 最终训练 | 7, 8, 11, 14, 15, 16, 17, 19, 21, 22, 23, 25, 26, 27, 28, 29, 30 | 17 | 6,037 |
| 验证 | 1, 3, 5, 6 | 4 | 1,315 |
| 官方测试 | 2, 4, 9, 10, 12, 13, 18, 20, 24 | 9 | 2,947 |

| 标签 ID | 官方活动名称 | 最终训练 | 验证 | 测试 |
| ---: | --- | ---: | ---: | ---: |
| 1 | WALKING | 960 | 266 | 496 |
| 2 | WALKING_UPSTAIRS | 863 | 210 | 471 |
| 3 | WALKING_DOWNSTAIRS | 793 | 193 | 420 |
| 4 | SITTING | 1,088 | 198 | 491 |
| 5 | STANDING | 1,147 | 227 | 532 |
| 6 | LAYING | 1,186 | 221 | 537 |
| 合计 | 六类均存在 | 6,037 | 1,315 | 2,947 |

三个集合受试者两两交集为空，合计覆盖全部 30 人。窗口标识由 `official_split:official_row_1based` 构成，10,299 个唯一标识恰好覆盖所有官方行；官方测试行顺序、标签、受试者均逐条保留。精确相同的九路完整窗口在集合内部、集合之间均未发现；这不代表相邻重叠窗口统计独立。没有删除、打乱或跨集合拆分同一受试者的窗口。

逐样本映射保存在 `sample_manifest.csv`，其中包含最终 split、最终 0 基索引、官方 split、官方 1 基行号、受试者和标签。原始标签 **1–6 保留**，未自动改为 0–5。

划分清单 SHA-256：`6f7828b88bd8f0cefdb022f61304f55ffe75615566d3e70a22110d170bb369a4`。

## 4. 仅最终训练集拟合标准化

为后续统一数值尺度，另存标准化副本，原始文件不改。按每通道在最终训练集的“窗口、时间”两个轴上拟合均值和总体标准差（ddof=0）。每通道拟合 **6,037×128 = 772,736** 个值；验证和测试数据未参与参数拟合。

| 通道 | 训练均值（约值） | 训练标准差（约值） |
| --- | ---: | ---: |
| body_acc_x | -0.000544759266 | 0.191601907179 |
| body_acc_y | -0.000330957890 | 0.118790100642 |
| body_acc_z | -0.000284925274 | 0.109349776211 |
| body_gyro_x | 0.001011756694 | 0.403883978993 |
| body_gyro_y | -0.000667131114 | 0.378739769276 |
| body_gyro_z | -0.000137701931 | 0.257701016581 |
| total_acc_x | 0.797673347184 | 0.415847696888 |
| total_acc_y | 0.030837841742 | 0.376744924080 |
| total_acc_z | 0.092792462482 | 0.381225148062 |

完整精度参数保存在 `scaler_train_only.json`。使用 float64 计算参数，三集合统一应用 `z=(x-mean)/std` 后另存 float32；无逐窗口标准化，无验证/测试重新拟合，无裁剪。没有零方差通道；如有则脚本失败而不静默替换。官方重叠窗口按每个保留窗口/采样点等权统计，没有额外去重加权。

磁盘独立复核重新按通道读取原始文本，以不同归约方式计算训练统计量；与保存值的最大均值误差 `2.7644553313166398e-14`，最大标准差误差 `1.659783421814609e-14`。三个 NPZ 中的所有标准化值与原始行加保存参数的 float32 结果逐值完全一致。

NPZ 字段：`X`、`y`、`subject`、`official_row_1based`、`channels`；使用 `allow_pickle=False` 成功重新读取。训练标准化数据最大绝对通道均值约 `8.08e-11`，标准差与 1 的最大偏差小于 `2.50e-10`；验证、测试不要求零均值/单位方差。

## 5. 两种活动的九路真实信号图

固定展示 WALKING（标签 1）和 STANDING（标签 5）。各取最终训练集中该活动的第一个官方行，不按波形好看程度选择。两图均为受试者 7：WALKING 为官方 train 第 1397 行，STANDING 为第 1316 行。

![WALKING 九路信号](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.png)

Fig. 1. 该 WALKING 窗口在九个通道上呈现可见的时间变化；图形仅描述这一观测窗口，不推断总体活动差异。每路独立面板保留物理单位，与 STANDING 对应通道使用相同纵轴范围。n=1 窗口，不适用总体置信区间。

![STANDING 九路信号](../../outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.png)

Fig. 2. 该 STANDING 窗口的多数加速度通道在相同纵轴尺度下比所选 WALKING 窗口变化更小，陀螺仪也保留了初段变化；没有逐窗口缩放或平滑来改变观测幅度。这是两个指定样本的展示，不是活动分类性能或统计显著性结论。

每图输出 PNG（2460×3450，约 300 dpi）、PDF、可编辑文本 SVG；源窗口 CSV 已逐通道逐点与原始文件比对。已经直接查看两张 PNG，确认九路通道、活动名称、受试者、时间轴、单位及脚注清晰，无文字截断。每个面板只有一条实测曲线并直接标注通道，灰度下无需依靠颜色区分通道。

图表质量边界：Icarus 技能目录缺少其引用的 `scripts/critique.py`、样式辅助脚本，当前 Python 也无 `paperfig`，故该技能原版机械门禁**未运行**。本项目使用独立本地样式、三格式导出及产物核验；不声称原版门禁通过或达到期刊投稿验收。九个等大面板是本次逐通道检查的需要；单窗口不虚构 CI。

## 6. 已执行阶段与失败记录

| 阶段 | 最终状态 | 证据 |
| --- | --- | --- |
| 读取启动报告与忽略规则 | 完成 | 已有文件哈希基线、前后复核 |
| 官方下载 | 完成，首次权限失败后成功重试 | run01/run02 provenance 与下载日志 |
| 压缩包完整性与解压 | 完成；官方发布哈希/HTTP 长度比对未运行 | `archive_integrity.json`、`download_provenance.json` |
| 全部官方文件和 18 路信号检查 | 完成 | `audit02/channel_file_audit.csv`、`audit_results.json` |
| 固定受试者划分 | 完成 | `splits/` 与类别分布 CSV |
| 训练集参数拟合及三集合转换 | 完成，首次序列化失败已修复 | `scaler_train_only.json`、三份 NPZ、独立复核 |
| 两活动九路图 | 完成 | 两活动 × PNG/PDF/SVG、图表清单、源 CSV |
| 独立磁盘复核 | PASS | `independent_verification.json`、验证日志 |
| 模型训练/推理、Git 初始化/提交/推送 | 未运行（任务明确不要求） | 无模型文件、无 `.git`，执行脚本无此类操作 |

失败和限制全部保留：

1. 网页工具访问官方 ZIP 时报告 `Content length is too large: 4194305+`，未作为本地下载使用；随后通过 Python 直接访问同一官方地址。
2. run01 于 11:18:04–11:18:05 被网络权限拒绝：`URLError` 内含 `WinError 10013`。工具权限审核允许后，run02 使用相同官方 URL 成功，没有更换数据来源。
3. 第一次数据审计完成 schema 与划分后，在写标准化参数时发生 `TypeError: Object of type int64 is not JSON serializable`。旧 `data/processed/day01_data_20261026_run02/` 内的 `scaler_train_only.json` 为**不完整失败产物**，不可使用。已将 ID 显式转换为 Python int，并改为先序列化成功再新建 JSON；在全新 `_audit02` 目录完成重跑。未删除或覆盖失败现场。
4. 发布者 SHA-256、HTTP Content-Length 比对及 Icarus 原版门禁未完成，原因见前文；它们不是“已通过”的检查。

## 7. 有效交付路径（均相对项目根目录）

| 类型 | 相对路径 |
| --- | --- |
| 本报告 | `reports/day01_data_20261026_run02/day01_data_audit.md` |
| 操作日志索引 | `reports/day01_data_20261026_run02/execution_log.md` |
| 下载来源及两层校验 | `reports/day01_data_20261026_run02/download_provenance.json`、`archive_integrity.json` |
| 最终数据审计 | `reports/day01_data_20261026_run02/audit02/` |
| 独立复核 | `reports/day01_data_20261026_run02/independent_verification.json` |
| 总体及逐人类别分布 | `reports/day01_data_20261026_run02/audit02/class_distribution.csv`、`subject_class_distribution.csv` |
| 划分清单 | `data/processed/day01_data_20261026_run02_audit02/splits/sample_manifest.csv` |
| 划分规则与人员 | `data/processed/day01_data_20261026_run02_audit02/splits/split_metadata.json` |
| 标准化完整参数 | `data/processed/day01_data_20261026_run02_audit02/scaler_train_only.json` |
| 标准化数组 | `data/processed/day01_data_20261026_run02_audit02/{train,validation,test}_standardized.npz`（三个实际文件） |
| 两个绘图源窗口与定位信息 | `data/processed/day01_data_20261026_run02_audit02/examples/` |
| 图与图表清单 | `outputs/figures/day01_data_20261026_run02_audit02/` |
| 原始执行日志 | `logs/day01_data_20261026_run01_download.log`、`day01_data_20261026_run02_download.log`、`day01_data_20261026_run02_audit.log`、`day01_data_20261026_run02_audit02_audit.log`、`day01_data_20261026_run02_audit02_figures.log`、`day01_data_20261026_run02_audit02_verification.log` |
| 新增执行脚本 | `scripts/day01_download_uci.py`、`day01_audit_uci.py`、`day01_figure_style.py`、`fig01_day01_signals.py`、`verify_day01_data.py` |

`data/`、`outputs/`、`logs/` 与常见权重已被原有 `.gitignore` 排除；本次未改忽略规则，没有 Git 仓库，因此没有暂存、提交或上传。模型目录未新增权重。当前代码只做下载、审计、划分、标准化和绘图。

## 8. 下一步待教学验收

数据侧没有阻塞 Day 01 交付的问题。请 ChatGPT 核对本报告、划分规则与两张图后决定下一任务；本次不进入模型阶段。后续若使用 PyTorch 的 CrossEntropyLoss，需要在未来数据加载环节显式决定如何把原始标签 1–6 映射为 0–5，当前未擅自转换。当前 PyTorch 仍是 CPU 构建，与此次数据读取、标准化和绘图无关。

来源元数据附记：官方当前页面声明 CC BY 4.0，原压缩包旧版 README 的许可文字不同；二者均保留，本次仅用于用户指定的学习实践，未再发布数据。
