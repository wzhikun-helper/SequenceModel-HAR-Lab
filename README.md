# SequenceModel-HAR-Lab

《第四次学习规划》Day 01：UCI HAR监督式活动分类、真实九路时序信号、人员划分与预处理。

截至2026-10-28，教师确认第三章3.1—3.3及12道正式理解题全部通过，数据实践验收通过。最终笔记已本地归档；本项目使用下列GitHub仓库进行版本同步。**第四章未开始，Day 02未开始。**

## 学习与进度

- [Day 01学习归档](learning_notes/day01/README.md)
- [教师确认的最终笔记](learning_notes/day01/2026-10-28_teacher_final_notes.md)
- [原题1—12学生原答、教师批改与缺失索引](learning_notes/day01/questions_01_12.md)
- [可读取的原始教学记录](learning_notes/day01/source_transcript.md)
- [进度记录](PROGRESS.md)

教师已确认12/12通过，但现可读取的原始对话仅覆盖原题4、5、10、12及3.2节局部读图问答。其余8题的原答/批改过程缺失，未用参考答案补造。

## 已完成的数据实践

- [实际数据审计报告](reports/day01_data_20261026_run02/day01_data_audit.md)
- [独立复核结果](reports/day01_data_20261026_run02/independent_verification.json)
- [人员划分、标准化参数和真实信号图关联](learning_notes/day01/engineering_evidence.md)
- [数据执行日志索引](reports/day01_data_20261026_run02/execution_log.md)
- [Day 01正式归档与同步检查报告](reports/day01_archive_20261028_run01/archive_report.md)

真实窗口形状128×9；最终训练17人/6037窗，验证4人/1315窗，官方测试9人/2947窗。验证受试者为1、3、5、6，三集合受试者互不重叠。标准化只用最终训练集拟合。有效数据产物位于data/processed/day01_data_20261026_run02_audit02/；不要使用保留的首次失败目录。

`data/`、`models/`、`outputs/`、`logs/`仍被忽略，数据集、标准化数组、模型权重、认证文件不作为提交内容。两张代表性真实图及小型划分/标准化元数据的可追踪副本见[Day 01文档证据](docs/day01/README.md)，原数据及原图保持不变；其他指向被忽略目录的历史链接仅在本机有效。

## 环境与下一阶段

既有启动检查记录：Python 3.9.13、PyTorch 2.0.1+cpu，系统识别RTX 3060 Laptop 6GB；当时PyTorch无法使用CUDA，本次未重新安装或切换环境。尚未开展CNN、GRU、Transformer、Mamba训练。

用户指定远程仓库：[wzhikun-helper/SequenceModel-HAR-Lab](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab)，主分支`main`。同步结果以远程分支提交与本地同步报告核验为准；本地运行报告保存在被忽略的`logs/day01_github_sync_20261028_run01/`。历史归档报告描述其当时的阻塞状态。第四章及Day 02等待教师后续决定。

## 启动历史

- [原始启动检查报告](reports/day01_startup_check.md)
- [更新前README原文备份](reports/day01_archive_20261028_run01/README.before.md)

启动检查脚本仍为scripts/check_day01.ps1。旧报告及日志保留其原时间和状态，不将旧记录改写为当前结果。
