# Day 02 CNN最小工程｜2026-11-11

工程自检：**通过**；教师对Lesson 01–02理论的通过结论已归档，工程结果待教师审阅。本轮没有训练循环、优化器或性能评价。

## 前置与数据来源

开始时main工作区干净，HEAD为`f07610850eaaf29a1ddcca4d15486604e5384bdc`；`git pull --ff-only origin main`实际返回Already up to date。第一次在沙箱内拉取因`.git/FETCH_HEAD`写入权限失败，随后在授权Git权限下成功；没有认证失败或改动远程地址。

读取了现有README、Day 01协议、复现指南、既有审计与验证脚本；src中无已有CNN实现。原规划全文未取得，结构依据本轮用户任务及[取回的教师教学原文](../../learning_notes/day02/source_transcript.md)，没有声称检查过缺失全文。

复用[Day 01独立复现通过的产物](../day01_repro_20261031_run01/independent_verification.json)：训练6037、验证1315、测试2947。当前29个原始文件哈希匹配，并再次逐值检查全部最终训练窗口与原始信号、保存的均值/标准差一致；未重新拟合或划分。38个输入文件前后哈希相同，包括三集合数组、划分及参数。

训练集中每个官方标签取首个窗口，保存索引依次为81、135、110、28、0、54，均为受试者7；官方训练行1397、1451、1426、1344、1316、1370。输入使用标准化float32信号。标签1–6仅在内存减1给交叉熵使用。

## 实测张量与参数

| 阶段 | 实测形状 | 参数公式 | 实际参数 |
| --- | --- | --- | ---: |
| 保存窗口批次 | [6,128,9] | — | 0 |
| permute后输入 | [6,9,128] | — | 0 |
| Conv1 + ReLU | [6,64,128] | 64×(9×3+1) | 1,792 |
| Conv2 + ReLU | [6,128,128] | 128×(64×3+1) | 24,704 |
| 全局平均池化 | [6,128,1] | — | 0 |
| Flatten | [6,128] | — | 0 |
| Linear输出logits | [6,6] | 6×(128+1) | 774 |
| 总计 | — | 1,792+24,704+774 | **27,270** |

卷积K=3、S=1、P=1、D=1、bias=True；两层后各ReLU。池化对每通道独立沿时间求平均。没有softmax、BatchNorm、Dropout或额外带参数模块。完整逐层hook结果和计算/实测对照见[result.json](result.json)。

## 损失、梯度与重载

- CPU，Python 3.9.13、PyTorch 2.0.1+cpu、NumPy 1.24.4；CUDA build为null、CUDA不可用。固定seed=20261111、1线程、确定性算法。
- 六个真实训练窗口一次前向，CrossEntropyLoss = **1.7899104356765747**。
- 一次反向，6个参数张量都有梯度且全部有限；每个张量至少一个非零元素。部分元素可为0，不声称每个元素非零。逐层L2范数、最大绝对值及非零数见机器结果。
- optimizer步骤=0，state_dict逐项与初始状态相同。保存的是未训练权重，不是已训练checkpoint。
- 本地checkpoint为`checkpoints/day02_cnn_20261111_run01/untrained_state_dict.pt`，110,999 bytes，SHA-256：`ffe43b7146318eac7425a6323d367885b9c6de9266d0e4f9df5aed9663a37967`。
- restricted weights-only加载、strict匹配成功。eval/no_grad同输入前后输出完全相同，最大绝对差 **0.0**；重载权重也逐项等于初始值。

## 运行与归档证据

[commands.json](commands.json)保存实际命令、起止时间、耗时、退出码与本地日志路径；[changed_files.json](changed_files.json)列出本次版本管理文件。[复现指南](../../docs/day02_cnn.md)说明环境与新ID要求。

实际执行命令的解释器为`E:/pythonenv/python39/python.exe`：

```powershell
python -B -m unittest discover -s tests_torch -v
python -B -u scripts/day02_cnn_smoke.py day02_cnn_20261111_run01
python -I -S -B -m unittest discover -s tests -v
python -B scripts/check_public_docs.py
```

PyTorch测试4项通过、真实样本执行退出0；标准库测试与文档检查的实际状态以命令记录为准。原始stdout和命令记录器仅本地保存于`logs/day02_cnn_20261111_run01/`，不提交；checkpoint及data仍受.gitignore保护。result.json仅含审计数值、ID与哈希，不包含原始窗口或权重。

提交使用显式文件列表，完成diff、忽略规则及敏感模式检查后推送指定origin/main。包含本报告的commit可从GitHub本文件历史确认；推送后的完整SHA、远端核验及Git状态写入本地`logs/day02_cnn_20261111_run01/sync_receipt.json`并在最终交付返回，避免在提交内嵌入其自身SHA。

## 限制与待验收

原规划全文仍未取得；可读取的5轮Lesson 01–02教学原文已归档，不声称包含更早课程。PyTorch发出TypedStorage弃用警告，退出码0，无NaN/Inf或运行失败。本次仅验证单一CPU环境；未验证CUDA或跨版本一致性。单批损失不代表准确率、泛化能力或收敛；未运行任何正式模型训练或消融。工程结果提交给教师决定下一步。
