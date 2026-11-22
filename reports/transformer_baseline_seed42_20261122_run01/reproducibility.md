# Transformer C复现

实际解释器E:/pythonenv/python39/python.exe，Python3.9.13 / torch2.0.1+cpu / numpy1.24.4，CPU FP32/2线程；没有安装或升级依赖。绘图用既有Matplotlib3.7.5、Pillow9.5.0。依赖快照沿用requirements-cnn.txt和requirements-data.txt，不是完整锁文件。

前提为已有指定Day 01有效产物和基线证据，且[审计机器证据](../transformer_preflight_20261122/audit_evidence.json)中的科学冻结文件、数据/配置SHA及环境匹配。新clone不含原始数据、数组、权重或stdout，不能假称直接clone即可完整运行。入口只读校验现有文件，不自动下载/预处理。当前导航不属于科学冻结范围，可更新README而不破坏旧实验保护；不应通过修改科学哈希来绕过真实差异。

项目根目录、具备上述依赖的Python，使用全新Run ID：

```powershell
python -B -m unittest discover -s tests_torch -v
python -B -u scripts/train_transformer_baseline.py transformer_baseline_seed42_new_run
python -B scripts/verify_transformer_baseline.py transformer_baseline_seed42_new_run
python -B scripts/fig04_transformer_baseline.py transformer_baseline_seed42_new_run
python -I -S -B -m unittest discover -s tests -v
python -B scripts/check_public_docs.py
```

新报告和权重目录独占创建，失败非0并保留failure.json/现场，禁止同名覆盖。两个真实Batch检查后丢弃模型和optimizer，重置随机状态，正式模型初始state哈希必须匹配原Seed42初始状态。配置在检查前保存，无命令行调参。

正式训练复用已有loader、optimizer、seed_all、evaluate、标签/契约、improves；固定sin/cos buffer，标准Post-Norm单层Encoder，不额外缩放输入或添加CLS/最终Norm。最大30、无改善8次停；best/last严格回放核验后只测试一次。Checkpoint不含optimizer状态，不支持中断恢复。独立验证只读预测/权重buffer，不额外模型推理。

PNG/PDF发布，SVG位于本地outputs/figures/<run>/。plot入口不覆盖已有目录。代码/配置/输入SHA及命令日志证明本次实际运行；不保证跨硬件/版本逐位相同，计时边界不同不作严格速度排名。初始审计辅助脚本编码启动问题另保留失败记录，正式训练正常直接启动。
