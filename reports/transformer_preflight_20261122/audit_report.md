# Transformer C实施前只读审计｜2026-11-22

状态：PASS。main工作区干净，HEAD为d2fbdfc5d9f07fd3a382de7a5ad45235c73b6020，origin为指定HTTPS仓库，无既有未追踪文件。未移动/删除/覆盖任何文件。

核对了[CNN配置和报告](../cnn_baseline_seed42_20261119_run01/execution_report.md)、[GRU配置和报告](../gru_baseline_seed42_20261121_run01/execution_report.md)、实际模型/入口、日志、指标与选模函数、忽略规则。配置SHA与执行provenance一致；实际源码哈希、旧stdout及旧Checkpoint字节哈希通过。CNN曾有的源码行尾格式变化与执行快照AST一致，属于已解释的历史记录，不改写旧源码或结果。本轮没有反序列化或重新评价旧模型。

| 核对项目 | 实际一致条件 |
| --- | --- |
| 数据 | day01_data_20261026_run02_audit02，三集合6037/1315/2947，17/4/9人 |
| 人员 | val=1,3,5,6；test=2,4,9,10,12,13,18,20,24；三组不交叉 |
| 输入与标签 | float32 [N,128,9]，九通道顺序固定；磁盘int64标签1–6，内存复用映射0–5 |
| 标准化 | 固定最终训练集拟合的已存参数，float64/ddof0，保存float32；数据/参数/划分哈希一致 |
| 软件与设备 | Python3.9.13、torch2.0.1+cpu、numpy1.24.4，CPU FP32、2线程；当前平台/解释器匹配旧CNN |
| 优化 | Adam .001、betas .9/.999、eps1e-8、weight_decay0；其余Adam运行选项与GRU记录一致 |
| 训练 | seed42、batch64、max30、patience8、drop_last=False；95批含21样本尾批 |
| Loader | 独立Generator42；train shuffle，val/test顺序；workers0、pin/persistent False |
| 评价/选模 | 复用CrossEntropy、固定六类Macro-F1、zero_division0、混淆行真值；val F1严格更高，完全同值才比较更低Loss |
| 禁止项 | 无AMP、裁剪、scheduler、类别权重或增强；不重划分或重拟合 |

当前NPZ实际形状、标签、人员和有限值检查通过，字节哈希与CNN/GRU执行时输入完全相同，既有29个原始文件哈希也通过，因此不重复下载或预处理。[数据协议](../../docs/data_protocol.md)。

模型计划严格按本轮任务：Linear9→64，固定正弦位置编码[1,128,64]，单层Encoder(d64,h4,FF128,ReLU,p0,batch_first,Post-Norm)，时间均值，Linear64→6。LayerNorm eps为标准1e-5，无最终额外Norm、CLS token或输入缩放。预期参数34502，将实测核对。2真实Batch检查包含Adam更新及Checkpoint重载，之后完整重新初始化正式对象。

无阻止训练的未知差异。历史CPU型号/序列号未记录，不能独立验证硬件指纹；只确认记录中的CPU设备、软件平台与版本匹配。三模型仍只有Seed42，历史计时边界不同，不能宣称严格速度排名或统计显著性。

[机器证据、配置SHA及冻结哈希](audit_evidence.json)。冻结科学证据用于训练入口，完整Git前后快照用于归档检查；可更新当前README/进度导航，不放宽旧实验保护。
