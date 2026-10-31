# 第一轮整改：Day 01独立复现、自动测试与证据索引

日期：2026-10-31，Asia/Shanghai。**真实数据完整复现PASS；本地25个轻量测试PASS。GitHub轻量CI由对应提交的Actions另行核验，不以本地结果冒充远程结果。**

## 执行前检查及复用范围

main工作区干净，已执行`git pull --ff-only origin main`，返回Already up to date。基线提交：`127eeaaadbf31bfa96d4cc9e9455ef79670f5baa`。已读取README、复现指南、数据协议、PROGRESS、现有审计/验证/绘图脚本、CI及问答索引。

官方下载/校验、全量窗口审计、固定人员划分、训练集标准化、绘图和独立逐值复核已有实现，继续复用。本轮只提取共享契约并补充合成反例测试、真实复现及运行比较，不另造数据流程。

## A. 独立环境中的真实数据完整复现

- 新venv：`.venv/day01_repro_20261031_run01/`，Python3.9.13；不继承系统site packages，禁用用户级包，未安装PyTorch。模块加载路径均核实位于新venv。
- 按requirements-data.txt从官方PyPI安装NumPy1.24.4、Matplotlib3.7.5、Pillow9.5.0，完整传递依赖与pip/setuptools版本另存。
- 新运行ID：`day01_repro_20261031_run01`；新产物ID：`day01_repro_20261031_run01_audit02`。
- 官方ZIP重新下载61,005,872字节，外层/内层SHA-256与旧运行一致，ZIP全部成员CRC通过。
- 实际读取训练7352、测试2947个窗口；九路信号每窗口128点。最终训练6037、验证1315、测试2947，人员与类别分布遵循原协议。
- 绘图生成两活动PNG/PDF/SVG六个文件；独立验证重新读取原始行、标准化参数和NPZ全部字段，通过。

[实际环境](environment.json) · [全部解析包版本](requirements-resolved.txt) · [逐步命令和实际退出码/耗时](commands.json) · [机器可读总结与源代码SHA-256](reproduction_result.json)

[本轮官方下载记录](../day01_repro_20261031_run01/download_provenance.json) · [真实审计结果](../day01_repro_20261031_run01/audit02/audit_results.json) · [独立逐值验证](../day01_repro_20261031_run01/independent_verification.json)

### 实际执行命令

均在项目根目录运行。记录器使用shell=False启动进程，保存开始/结束时间、退出码、perf_counter耗时和原始输出。本机日志位于被忽略的`logs/remediation_round1_20261031_run01/`，公开只提交经审查的运行元数据，不提交stdout/stderr原日志。

| 步骤 | 实际子进程命令 | 退出码 | 耗时（秒） |
| --- | --- | ---: | ---: |
| 00_venv | `python -m venv .venv\day01_repro_20261031_run01` | 0 | 13.690 |
| 01_dependencies | `.venv\day01_repro_20261031_run01\Scripts\python.exe -m pip install --disable-pip-version-check --index-url https://pypi.org/simple -r requirements-data.txt` | 0 | 36.036 |
| 02_lightweight | `.venv\day01_repro_20261031_run01\Scripts\python.exe -I -B -m unittest discover -s tests -v` | 0 | 0.233 |
| 03_environment | `.venv\day01_repro_20261031_run01\Scripts\python.exe -B logs\remediation_round1_20261031_run01\environment.py` | 0 | 1.360 |
| 04_freeze | `.venv\day01_repro_20261031_run01\Scripts\python.exe -m pip freeze --all` | 0 | 1.782 |
| 05_download | `.venv\day01_repro_20261031_run01\Scripts\python.exe -B -u scripts\day01_download_uci.py day01_repro_20261031_run01` | 0 | 9.901 |
| 06_audit | `.venv\day01_repro_20261031_run01\Scripts\python.exe -B -u scripts\day01_audit_uci.py day01_repro_20261031_run01 audit02` | 0 | 5.790 |
| 07_figures | `.venv\day01_repro_20261031_run01\Scripts\python.exe -B -u scripts\fig01_day01_signals.py day01_repro_20261031_run01_audit02` | 0 | 5.708 |
| 08_verify | `.venv\day01_repro_20261031_run01\Scripts\python.exe -B -u scripts\verify_day01_data.py day01_repro_20261031_run01 day01_repro_20261031_run01_audit02` | 0 | 3.268 |
| 09_compare | `.venv\day01_repro_20261031_run01\Scripts\python.exe -B -u scripts\compare_day01_runs.py day01_data_20261026_run02 day01_repro_20261031_run01 reports\remediation_round1_20261031\comparison` | 0 | 2.342 |
| 10_stdlib_only | `.venv\day01_repro_20261031_run01\Scripts\python.exe -I -S -B -m unittest discover -s tests -v` | 0 | 0.203 |

### 与旧有效运行的逐项对比

对照为`day01_data_20261026_run02_audit02`。使用实际文件与数组比较，不以静态清单代替。

| 对比项 | 实际结果 |
| --- | --- |
| 官方外层/内层ZIP SHA-256 | 一致 |
| 样本划分CSV字节、划分元数据及类别计数 | 一致 |
| 标准化参数完整元数据 | 一致；均值和标准差最大绝对差均为0 |
| 三集合NPZ全部字段 | dtype/形状/数值一致，X最大绝对差0；容器SHA-256也一致 |
| WALKING、STANDING PNG | 像素一致 |
| SVG | 字节不同，生成时间不同；路径几何和文本一致 |
| PDF | 字节不同，CreationDate不同；不声称PDF逐字节一致 |

[完整比较及日期](comparison/comparison.json)。29个旧原始数据文件、旧处理/图形产物以及旧的成功/失败报告均通过哈希保护检查；源代码按整改允许演进，执行时源码哈希与基线commit分别保存。

## B. 轻量自动化测试

新增标准库模块`har_contracts.py`，将既有形状、九通道顺序、官方标签、固定验证人员选择、三集合不交叉、标准化来源约束抽为共享函数。真实审计、磁盘验证与公开文档检查都调用同一模块。

25个unittest用例包含正确输入和错误反例：128×9布局/窗口数、通道交换或重复、0基或非法标签、人员交叉/缺失、拟合人员混入验证/测试、错误清单哈希、错误归约轴/ddof/精度、非有限或零标准差等。在新venv中使用`-I -S -B`实际通过，禁用site packages后无需NumPy、数据集或GPU。既有CI仅新增同一轻量测试步骤，保留只读权限及禁止目录检查。

轻量测试验证合成行为及声明来源，不能证明真实参数一定按声明拟合；A中的磁盘逐值验证提供数值证据。首页和[两层验证说明](../../docs/verification.md)将两个结论分开。

### 修正的复现阻断

旧验证脚本要求项目没有`.git`，与现已初始化仓库矛盾。该条件在执行前审查中发现，没有伪造一次运行失败；现改查git ls-files中禁止目录未被追踪，真实复现通过了新检查。划分与标准化算法不变。

额外验证支持`--verification-id`，向新路径写报告，不覆盖历史输出。下载时的已有文件基线检查仍保留；后续正常修改README后重验旧运行可能失败，不能静默重写旧基线。

## C. 归档完整性

[证据类型索引](../../learning_notes/day01/evidence_index.md)逐题标明逐字学生原文、教师摘要/批改摘要和缺失项。原题4、5、10、12可定位原答；1、2、3、6、7、8、9、11原始对话仍缺失，本轮没有取得新对话，不补造答案。原问答索引、原始教学文本和教师12/12通过的最终笔记均保持原字节。

## 中间失败、范围与限制

首次失败的文档检查、完成报告后的成功复验及最终25个测试的实际命令/退出码/耗时另存[补充检查记录](additional_checks.json)。失败记录未覆盖。

- 第一次报告生成错误地将允许更新的reports/README.md导航列入历史不可变集合，因此断言中止；修正为保护所有日期化历史报告，允许当前导航更新。未修改历史报告来绕过检查。
- 随后第一次文档检查因本报告尚未生成而退出1，保留11_docs的失败命令和日志；完成报告后使用新步骤名重验，不覆盖失败记录。数据复现各步骤未失败。
- 官方发布哈希/HTTP长度独立比对仍缺对应值；PDF/SVG字节差异不隐藏；未做跨操作系统/跨Python版本复现。完整环境是同一Windows机器上的独立venv。
- 原始数据、窗口数组、权重、密钥、venv及本地运行日志不提交。实际命令、环境、退出码和耗时是经过审查的研究元数据，与原始stdout/stderr日志分开保存。
- 原版绘图技能门禁缺失的历史限制不改写为通过；本轮图表核验沿用既有独立检查并增加旧/新像素及几何对比。

## 修改范围

本轮逐文件清单见[changed_files.json](changed_files.json)，不将本地数据、窗口数组、venv或stdout/stderr日志列为提交产物。

代码：共享契约、合成测试、运行比较；审计/验证/文档检查调用共享函数。CI：只扩展既有轻量工作流。文档：首页、英文概览、复现指南、协议来源、进度、脚本/报告导航及更新记录。证据：本轮来源/审计/独立验证元数据、环境与命令快照、比较结果和问答类型索引。

未开始第四章或Day02，未训练任何模型，未开展消融，未改人员划分或标准化协议。最终提交与远程SHA核验另存本地日志，避免报告自引用其自身commit。
