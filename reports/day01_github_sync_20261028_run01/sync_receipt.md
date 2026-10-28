# Day 01 GitHub同步回执

日期：2026-10-28，Asia/Shanghai。

用户指定HTTPS地址：`https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git`。本地分支`main`，remote为`origin`。未创建其他仓库，未更改用户指定地址，未使用强制推送。

## 已完成的首批推送

- 首批成果提交：`fb64f6710a83df49b1d7a98fffbe6602cb4d7971`。
- 提交说明：`Archive Day 01 learning notes and verified UCI HAR evidence`。
- 首批提交包含61个文件，实际暂存blob共1,362,807字节。
- `git push -u origin main`退出0，成功建立远程main并设置跟踪关系。
- 随后`git ls-remote origin refs/heads/main`返回与上述本地HEAD相同的完整哈希。
- 首批核验时`git status --short --branch`为`## main...origin/main`，无工作区修改。

本回执及进度更新作为后续收尾提交，不声称它们自身已包含在上述首批提交中。收尾提交的最终SHA、远程SHA、完整文件清单及工作区状态保存在本地被忽略的`logs/day01_github_sync_20261028_run01/sync_report.json`与`sync_report.md`，避免报告自引用其自身提交哈希。

## 提交范围与保护

提交范围：学习笔记、可恢复教学原文、问题1—12证据索引、工程代码、README/进度、历史审计材料，以及docs/day01中的两张代表性PNG、划分元数据和训练集标准化参数。

原始数据集、标准化数组、模型权重、认证文件和本地日志没有被追踪。`.gitignore`保留原规则并补充本地代理配置和常见认证文件；实际暂存blob做了文件路径、类型、大小和特定令牌/私钥模式检查，未发现匹配。该检查有明确范围，不声称能检测所有秘密。所有禁止目录的git ls-files结果为空，忽略规则探针通过。

WALKING图676,076字节，STANDING图403,786字节，均为2460×3450、约300 dpi，副本与原图SHA-256一致。两图只对应最终训练受试者7的单个窗口，不是总体性能证据。原始数据、参数和原图未修改。在线图与小型元数据见[文档证据](../../docs/day01/README.md)。

历史README.diff含统一差异格式的空白上下文行。未改动该历史文件，仅在.gitattributes对该文件排除blank-at-eol检查；最终git diff --cached --check通过。

## 实际遇到的问题

1. 普通沙箱网络无法连接代理；通过工具权限审核后，同一指定仓库的读取及推送成功，未关闭TLS校验或更换来源。
2. 普通沙箱写Git索引时报index.lock权限拒绝；经工具权限审核后暂存成功。
3. 一次.gitattributes暂存的自动权限审核超时，操作未执行；按工具允许重试一次后成功。没有把超时误报为认证失败。

使用已有凭据机制完成推送，未读取或打印凭据内容。仓库可见性未查询或修改。没有训练CNN、GRU、Transformer、Mamba，也未进入Day 02。

## 尚未解决的历史记录缺口

原题1、2、3、6、7、8、9、11的原始学生回答和逐题批改过程仍缺失，已在学习笔记明确记录，没有编造。教师12/12通过结论保留。Day 01整体结课仍交由教师复核归档与同步结果。
