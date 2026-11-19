# Baseline A复现说明

实际Python3.9.13、PyTorch2.0.1+cpu、NumPy1.24.4、Matplotlib3.7.5、Pillow9.5.0。解释器E:/pythonenv/python39/python.exe，本次未安装或升级包。根目录requirements-cnn.txt和requirements-data.txt是直接依赖快照，不是完整锁文件。[环境](environment.json)、[执行源码及配置哈希](source_provenance.json)。

必须已有day01_data_20261026_run02_audit02有效产物、对应Day 01报告和原始文件。入口固定使用该来源，不自动下载。fresh clone不含数据或权重；若新机器的数据运行ID不同，需显式核对来源路径，不能声称即插即用。

在项目根目录、带依赖的Python环境，用新的未存在Run ID逐条执行并检查退出码：

```powershell
python -B -m unittest discover -s tests_torch -v
python -B -u scripts/train_cnn_baseline_a.py audit cnn_baseline_seed42_new_run
python -B -u scripts/train_cnn_baseline_a.py preflight cnn_baseline_seed42_new_run
python -B -u scripts/train_cnn_baseline_a.py train cnn_baseline_seed42_new_run
python -B scripts/verify_cnn_baseline_a.py cnn_baseline_seed42_new_run
python -B scripts/fig02_cnn_baseline_a.py cnn_baseline_seed42_new_run
```

audit只读校验所有保存值/人员/标签，新建config和环境。preflight测试独立模型；train重置RNG和模型/优化器，执行批准配置及验证选模。失败非0并保留failure_<stage>.json和现场；不清理旧目录，同名输出拒绝覆盖。完整stdout本轮由logs下独立命令记录器保存。

最多30轮，8轮无改善停止；Macro-F1完全相同才按Loss打破平局。训练全量含尾批，无scheduler、类别权重、增强。最终测试只在最佳权重重载后执行一次。独立验证仅读预测复算。每次改善单独新建权重文件；无Adam状态，不支持中途恢复。确定性配置只验证本次CPU，不保证跨硬件/版本逐位相同。图表从已保存CSV生成，现有输出不覆盖。
