# 脚本索引

从项目根目录运行；完整命令和输出约定见[复现指南](../docs/reproducing_day01.md)。

## 数据流程

| 顺序 | 脚本 | 作用 |
| ---: | --- | --- |
| 1 | [day01_download_uci.py](day01_download_uci.py) | 官方下载、SHA-256、ZIP CRC与安全解压 |
| 2 | [day01_audit_uci.py](day01_audit_uci.py) | 信号/标签核验、受试者划分、训练集标准化、样本导出 |
| 3 | [fig01_day01_signals.py](fig01_day01_signals.py) | 读取实际窗口CSV，导出PNG/PDF/SVG |
| 4 | [verify_day01_data.py](verify_day01_data.py) | 从磁盘独立检查划分、参数和全部保存值 |

[day01_figure_style.py](day01_figure_style.py) 是绘图辅助模块，不是独立实验入口。[check_day01.ps1](check_day01.ps1) 是历史Windows环境检查脚本，其检查范围比数据流程依赖更广。

## 文档检查

```powershell
python -B scripts/check_public_docs.py
```

仅检查公开入口的本地链接、图片、元数据一致性和Python源码语法，不访问网络、不导入实验脚本、不读取原始数据、不写文件。

## 共享契约与轻量测试

[har_contracts.py](har_contracts.py)定义真实审计、磁盘验证和公开文档共用的形状、通道、人员、标签与标准化来源约束；仅使用标准库。

```sh
python -I -S -B -m unittest discover -s tests -v
```

合成测试不代表真实数据复现。[两层验证的范围与最新证据](../docs/verification.md)。

[compare_day01_runs.py](compare_day01_runs.py)读取两个已完成的真实运行，比较压缩包、划分、参数、三集合数组与图形，向全新报告目录写结果；不修改两个输入运行。

## 历史归档工具

[archive_day01_20261028.py](archive_day01_20261028.py) 与 [prepare_day01_git_sync.py](prepare_day01_git_sync.py) 保留当日归档操作，使用固定日期、快照及独占输出目录，不属于可反复执行的通用数据API。阅读历史实现即可，不要为重新运行它们而删除已有成果。
