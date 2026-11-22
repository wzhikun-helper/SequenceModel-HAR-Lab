# 第六章 Lesson 01 · 项目 Skill 调用与研究报告初稿

**交付**　[中文 PDF](report.pdf) · [LaTeX 源文件](report.tex) · [结果图 PNG](results_figure.png) / [PDF](results_figure.pdf) / [SVG](results_figure.svg) · [学习记录](../../learning_notes/chapter06_lesson01.md)

## 实际调用

本轮用户指定的报告任务原文如下。

> 根据已归档的四模型Seed42实验与CNN三种子消融，生成中文科研报告初稿，并核实所有表格和图表与实际实验数据一致。

在当前 Codex 会话中，先显式读取新建的 [SKILL.md](../../.agents/skills/uci-har-experiment-workflow/SKILL.md)，再按其汇总步骤执行[报告构建](../../scripts/build_har_research_report.py)。构建命令调用[绘图脚本](../../scripts/fig05_har_research.py)，并使用[仓库图表样式](../../scripts/day01_figure_style.py)。这是一次实际的报告调用。尚未单独验证新会话的自动发现，也未按原规划通过 Skill 发起一次正式训练。所有历史模型训练和测试均为既有运行。

## 输入与核验

开始时本地 `main` 为 `a94ca6d58f6eede9cb08a6f4989a8dfbcbcb14c8`，工作区干净。远程 `main` 为 `982db1f050074549916fe0509339c5b57f5c22db`，本地已快进到该提交。仓库当时没有已跟踪的 AGENTS.md 或项目 Skill。CNN、GRU、Transformer、CNN 消融均有现成训练、核验和绘图入口。Mamba 代码、环境、数据和结果整理在 [Linux 实验归档](../../experiments/mamba_baseline_d_seed42_20261122/README.md)。

通过现有 SSH 配置尝试只读访问用户给出的服务器项目，两个入口分别因认证拒绝与连接关闭未进入远端目录。服务器当前工作树和文件无法独立核查。Mamba 数据来源为上述 Git 提交中的归档代码、训练与测试记录及服务器记录的哈希。本地逐文件重算三份标准化 NPZ 和 scaler 的 SHA-256，四项均匹配服务器归档所记录的观察值与历史值。

| 内容 | 证据 |
| --- | --- |
| 四模型 Seed42 | [基线 CSV](baselines.csv)与[归档四模型 JSON](../../experiments/mamba_baseline_d_seed42_20261122/reports/four_model_comparison.json)交叉核对 |
| CNN A/B/C × Seed42/43/44 | [九组 CSV](ablation.csv)核对各运行指标和训练结果，A42 与基线共用同一个归档 |
| 同种子差值与组间汇总 | [配对 CSV](paired.csv)与[统计源](../../reports/cnn_ablation_20261122/statistics.json)核对，使用样本标准差 |
| 数据与来源 | [输入清单](input_manifest.json)记录 39 份输入的工作区文件 SHA-256、四项冻结数据哈希和起始提交。跨平台比较文本哈希时应考虑 Git 的换行符转换 |

共核对 12 个不同历史运行。各矩阵的类顺序、真实类别计数和总数一致，逐类指标、Accuracy 和 Macro-F1 均可由矩阵复核，允许绝对差小于或等于 `1e-12`。Loss 保留原存档值。制表和作图从同一批经核对的记录生成。图 a 用点位与数值呈现四模型 Seed42 Macro-F1，图 b 标明零线和三个真实配对，两个符号可在灰度下区分。三个配对点是完整观察值，未绘制置信区间。

## 命令和检查

执行环境为 Windows、PowerShell、Python 3.9.13、Matplotlib 3.7.5、MiKTeX 26.5 XeTeX 和 Poppler。生成报告无需加载模型或读取原始信号。

| 命令 | 退出码和结果 |
| --- | --- |
| `git ls-remote origin refs/heads/main`、`git pull --ff-only origin main` | 开放 GitHub 网络后各为 0，本地快进到 Mamba 归档提交 |
| `python -X utf8 -B <skill-creator>/scripts/quick_validate.py .agents/skills/uci-har-experiment-workflow` | 0，首次默认系统编码报 GBK 解码错误，显式 UTF-8 后通过 |
| `python -B scripts/build_har_research_report.py --output reports/chapter06_lesson01_research_draft` | 0，读取 39 份归档输入，生成 CSV、表格片段、LaTeX 与三种图形格式 |
| `xelatex -disable-installer -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex` | 最终连续两次退出 0 |
| `pdfinfo report.pdf`、`pdftotext -enc UTF-8 -layout report.pdf <文本路径>`、`pdftoppm -r 115 -png report.pdf <预览前缀>` | 成功读取 A4 两页，提取文本和渲染均退出 0 |
| `python -B -m unittest discover -s tests`、`python -B -m unittest discover -s tests_torch` | 各退出 0，25 项与 16 项通过 |
| `python -B scripts/check_public_docs.py`、`git diff --check` | 各退出 0 |

首轮编译因 MiKTeX 字体名称解析失败退出 1，改为使用 Windows Unicode 字体文件路径。第二轮因输入片段后放置表格底线退出 1，底线改由表格片段输出。编译成功后发现长文件名造成溢出、尾句跨到第三页，将复现说明移至第一页并缩短，随后重新编译和渲染。逐页目检两张最终 A4 页面，确认中文显示、表列和图例可读，表格及图无裁切，引用和页码完整。最终日志无箱体溢出、缺字或引用未定义。

最后从 PDF 文本逐行核对 4 行基线、9 行消融及 3 行汇总，全部匹配；再次重算 39 项归档与 4 项冻结数据的 SHA-256，全部匹配。本机 Icarus Skill 目录缺少独立的 `critique.py`，图的数值、标签、样本范围、导出格式及排版由上述实际核对与目检覆盖。

本目录的最终发布 SHA 以 Git 中引入本目录的提交为准，可用 `git log --diff-filter=A --format=%H -- reports/chapter06_lesson01_research_draft/report.pdf` 核对。

## 复现

从仓库根目录运行以下命令。需要 Python 和 Matplotlib，以及带 CTEX、Booktabs、Graphicx 的 XeLaTeX。Windows 使用模板指定的系统字体文件，其他平台需安装 Fandol。使用新目录。

```powershell
python -B scripts/build_har_research_report.py --output reports/har_research_replay
Set-Location reports/har_research_replay
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error report.tex
pdftoppm -r 115 -png report.pdf preview
```

比较 CSV 数值与来源清单。PDF 元数据可能含编译时间，环境也会影响字体和排版。逐页确认图表与正文清晰、引用已解析。GitHub 发布保留报告和小型汇总工件，编译中间文件与原始日志位于本地忽略目录。
