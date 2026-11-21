# CNN Baseline A配置审计｜GRU实施前

2026-11-21，状态：**PASS，可按共同实验条件执行GRU**。本报告在新增GRU模型/训练代码和正式训练之前生成；只读核验原始实验，没有重跑CNN或加载其Checkpoint。

| 项目 | 从执行证据恢复的CNN实际设置 | 证据 |
| --- | --- | --- |
| 数据来源 | UCI官方HAR、既有day01_data_20261026_run02_audit02；原压缩包SHA c00b803081a5c797cd5e4b83700a9810b38d53d9d84e01917e090e1fdbc81031 | [CNN审计](../cnn_baseline_seed42_20261119_run01/data_audit.json)、Day 01来源报告 |
| 人员与数量 | train6037/17人，val1315/4人，test2947/9人；验证ID1,3,5,6，三组不交叉 | [数据协议](../../docs/data_protocol.md)、划分元数据与保存参数哈希一致 |
| 标准化 | 最终训练6037窗口按N/time拟合，float64、ddof0；三组共用，float32输出 | [参数](../../docs/day01/standardization_train_only.json)，当前文件哈希匹配CNN审计 |
| 标签 | 磁盘官方1–6，内存减1为0–5；固定六类顺序 | [加载器](../../scripts/train_cnn_baseline_a.py#L81)、har_lab.cnn.targets_from_official |
| 随机性 | Python/NumPy/PyTorch=42，loader独立Generator=42；2线程、确定性算法 | [seed_all](../../scripts/train_cnn_baseline_a.py#L71)、[loader](../../scripts/train_cnn_baseline_a.py#L88) |
| Batch/DataLoader | 64；train shuffle=True，val/test False；drop_last=False；workers0，pin_memory=False，persistent_workers=False | 实际源码+PyTorch2.0.1接口默认值；日志每轮6037样本/95批 |
| Adam全参数 | lr=.001，betas=(.9,.999)，eps=1e-8，weight_decay=0，amsgrad=False，maximize=False，foreach=None，capturable=False，differentiable=False，fused=None | [实际构造](../../scripts/train_cnn_baseline_a.py#L182)；同版本构造器和defaults实测 |
| Loss | CrossEntropy，weight=None，ignore_index=-100，label_smoothing=0；训练mean，评价sum后/N | [训练](../../scripts/train_cnn_baseline_a.py#L189)、[评价](../../scripts/train_cnn_baseline_a.py#L94)及同版本函数签名 |
| scheduler/裁剪/AMP | 均无；float32；zero_grad默认set_to_none=True | 实际执行源码没有scheduler、clip_grad、autocast/GradScaler；独立Python入口未改默认dtype |
| 最大轮数/实际 | max30，实际15，95批/轮 | [config](../cnn_baseline_seed42_20261119_run01/config.json)、原stdout逐轮与CSV逐字段完全一致 |
| 选模 | val Macro-F1严格更高；完全相同才比较更低val Loss；两者同则保留早期 | [共享improves](../../scripts/cnn_metrics.py)、train调用 |
| Early Stopping | 每次改善清0，连续8轮无改善停止 | [循环](../../scripts/train_cnn_baseline_a.py#L266)；实际Epoch7最佳，15停止 |
| 最终测试 | 结束后strict重载最佳；验证probe及完整验证复核后，只测试一次；eval/no_grad | [重载及test](../../scripts/train_cnn_baseline_a.py#L267)，旧测试指标仅读取 |
| 环境 | Python3.9.13，torch2.0.1+cpu，numpy1.24.4，Windows10 build26200，CPU，FP32 | [环境](../cnn_baseline_seed42_20261119_run01/environment.json)与当前逐字段一致 |

## 一致性与恢复方式

实际执行配置SHA与执行时provenance一致；原stdout大小/SHA匹配公开清单，15个Epoch与CSV逐字段一致。最佳权重按字节哈希匹配；没有反序列化或重新评价CNN。原训练源码发布前仅去掉一个行尾空格，已用本地执行快照和SHA、Python AST相等性恢复真实执行代码。全量保存数据与原始29文件哈希仍匹配CNN审计，故可直接复用，禁止新划分或拟合。

隐含参数不是经验猜测：调用未显式传入的Adam选项、Loss默认值、DataLoader选项和zero_grad参数由已经确认的实际PyTorch2.0.1实现恢复，并与当前同版本签名/defaults核对；CNN未保存optimizer状态，本审计不声称从权重文件读出优化器参数。配置、源码和执行记录没有影响训练的冲突。

## GRU配置差异计划

共同配置原样复用：seed42、batch64、同Adam全参数、FP32 CPU/2线程、CE、无scheduler/裁剪/AMP、max30、patience8、同选模/loader、固定数据/参数/标签。只换为单层单向GRU(input9,hidden64,batch_first=True)+Linear64→6；默认bias=True、dropout=0，h0隐式全零，用h_n[-1]分类。输入布局从CNN的[B,9,128]改为GRU的[B,128,9]，是接口差异，不改保存数组。

新要求仅增补记录train accuracy、epoch秒数、runtime实际optimizer参数、best/last权重，不改变更新或选模。预检查集成在训练入口、使用一次性测试模型；正式模型、optimizer及loader都重新设种子初始化。沿用独立loader Generator=42使两种模型训练样本顺序可匹配；模型不同导致随机初始化和计算图不同，不声称随机数消耗或权重完全相同。

## 限制与未解决项

关键训练配置可以恢复，无阻止训练的缺失项。旧环境未记录CPU序列号/型号，不能独立证实硬件指纹，只能确认同一工作机记录的平台、解释器、CPU设备和版本一致；旧CNN没有单独推理耗时记录，不补造，比较表标未测。单种子差异不是普遍优越性证据。

[机器审计证据与冻结哈希](audit_evidence.json)。后续不得修改CNN模型、脚本、历史报告、日志、Checkpoint和.gitignore。
