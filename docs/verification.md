# 两层验证：轻量CI与真实数据复现

这两种结果独立记录。CI通过不代表重新下载、处理或完整验证了UCI HAR数据。

| 验证层 | 实际执行内容 | 不覆盖的范围 |
| --- | --- | --- |
| 轻量CI | 公开文档链接、图片/元数据校验、源码语法，以及25个合成契约单元测试 | 不下载数据、不拟合真实参数、不验证真实数组、不训练模型 |
| 独立环境完整复现 | 新venv安装文档依赖、新ID官方下载、真实数据审计/标准化、绘图、逐值复核、与旧结果比较 | 不等于跨Python版本/跨操作系统复现，也不是模型性能实验 |

## 轻量测试

```sh
python -B scripts/check_public_docs.py
python -I -S -B -m unittest discover -s tests -v
```

第二条命令禁用用户与系统site packages，仅用标准库；不需要NumPy、PyTorch、数据文件或GPU。CI沿用[既有工作流](../.github/workflows/docs.yml)，保持只读权限和禁止目录追踪检查。

[共享契约](../scripts/har_contracts.py)被真实审计、磁盘验证和文档检查共同调用；[合成测试](../tests/test_har_contracts.py)包含正确输入与错误反例：

- 形状只能是正数窗口数×128时间点×9通道，窗口数与标签/清单一致。
- 通道顺序为body_acc_xyz、body_gyro_xyz、total_acc_xyz，不能交换或重复。
- 标签保留官方1—6和名称，拒绝0基、未知、非整数及错误映射。
- 受试者按固定排序规则选择，三集合不能交叉或为空。
- 标准化声明的拟合人员、窗口数、归约轴、总体标准差、参数精度及清单哈希必须对应最终训练集；拒绝混入验证/测试人员、零方差与非有限参数。

这些测试核查行为和声明的来源约束，不能单凭元数据证明真实数值确实来自训练集；数值证据由完整复现中的独立逐值核验提供。

## 2026-10-31 独立环境完整复现

已在新的`.venv/day01_repro_20261031_run01/`环境中执行；`include-system-site-packages=false`，用户级包被禁用，未安装PyTorch。Python 3.9.13，NumPy 1.24.4，Matplotlib 3.7.5，Pillow 9.5.0；直接依赖来自[文档版本清单](../requirements-data.txt)，传递依赖的实际解析结果另行保存。

新运行ID：`day01_repro_20261031_run01`；处理产物ID：`day01_repro_20261031_run01_audit02`。

下载、真实审计、绘图、独立逐值验证均退出0。与原有效运行比较：官方ZIP及内层ZIP哈希、样本清单、划分/标准化元数据一致，三集合NPZ所有字段逐值相同；两张PNG像素相同。PDF/SVG字节不同，生成时间不同；SVG路径几何与文本相同，未声称矢量文件逐字节相同。

[第一轮整改报告](../reports/remediation_round1_20261031/README.md) · [逐项对比结果](../reports/remediation_round1_20261031/comparison/comparison.json)

## 复现过程中的验证器修正

旧验证脚本要求`.git`不存在，会在已初始化仓库中误失败。现改成检查数据、输出、权重与日志目录未被Git追踪；这是执行环境检查修正，数据协议不变。

可使用新的验证ID保存额外的验证报告，不覆盖之前结果：

```powershell
python -B scripts/verify_day01_data.py <Run> <Artifacts> --verification-id review01
```

验证脚本仍会检查下载时记录的工作区文件基线；这项“运行期间未改动”检查有时间边界。后续README等正常演进后重验旧运行，可能因基线变化失败，不能直接改写旧基线。额外验证ID只解决报告路径冲突，不豁免基线检查。
