# GRU Baseline B复现与边界

实际使用原CNN解释器E:/pythonenv/python39/python.exe，Python3.9.13、torch2.0.1+cpu、numpy1.24.4；Matplotlib3.7.5、Pillow9.5.0用于图表，没有安装/升级包。数据固定为Day 01已验证的day01_data_20261026_run02_audit02，不自动下载、划分或拟合。

先完成[配置审计](../gru_baseline_preflight_20261121/audit_report.md)。训练入口要求audit_evidence.json中的CNN config、冻结哈希及环境匹配；新clone不含原数据、Checkpoint和stdout，不能声称无这些证据也可直接运行审计。审计文档和机器证据保留在仓库，缺少本地证据时应报告，不能跳过检查。原始任务要求先审计，因此本轮审计生成器保留在本地logs，不作为无条件下载/安装入口。

在项目根目录，使用带上述依赖的Python，新运行ID：

```powershell
python -B -m unittest discover -s tests_torch -v
python -B -u scripts/train_gru_baseline.py gru_baseline_seed42_new_run
python -B scripts/verify_gru_baseline.py gru_baseline_seed42_new_run
python -B scripts/fig03_gru_baseline.py gru_baseline_seed42_new_run
python -I -S -B -m unittest discover -s tests -v
python -B scripts/check_public_docs.py
```

入口将必要预检查集成到正式流程，一次性模型后重新初始化所有RNG、模型、optimizer和loader。检查失败非0并保留failure.json及现场；所有运行目录/文件独占创建，不覆盖同名运行。每次改善另存epoch权重，best别名和last也独占保存。配置不接受隐式命令行调参；共同设置直接复制已审计CNN配置。

CPU FP32和2线程按原CNN条件，未使用AMP、梯度裁剪、scheduler或类别权重。确定性设置不保证跨硬件/版本逐位一致。统计训练准确率和计时不改变更新；进程计时与旧CNN范围不同，不能据此计算严格速度比。单独推理没有计时。

结束后仅best一次测试。独立验证读保存预测，不重复模型测试。图表读取CSV，公开PNG/PDF，可编辑SVG保存至本地outputs/figures/<run>/；同名输出拒绝覆盖。权重不含optimizer状态，不支持中断恢复。源与配置SHA及冻结输入见source_provenance.json。
