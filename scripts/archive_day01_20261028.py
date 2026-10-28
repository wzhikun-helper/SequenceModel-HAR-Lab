"""Archive confirmed Day 01 records. Stop Git sync if no repository/remote exists."""
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'reports/day01_archive_20261028_run01'
NOTES = ROOT / 'learning_notes/day01'
SNAPSHOT = ROOT / 'logs/day01_archive_20261028_teacher_snapshot.json'


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def safe(path):
    path.relative_to(ROOT)
    for component in [path, *path.parents]:
        if component.exists() and (component.is_symlink() or (getattr(component.lstat(), 'st_file_attributes', 0) & 1024)):
            raise ValueError('Linked output path: ' + str(component))
        if component == ROOT:
            break


def write(path, text):
    safe(path)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text.rstrip() + '\n')


def jwrite(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2))


def git(*args):
    result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {'command': ['git', *args], 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def main():
    for path in [ARCHIVE, NOTES]:
        safe(path)
        if path.exists():
            raise FileExistsError('Refusing to overwrite archive/notes: ' + str(path))
    if (ROOT / 'PROGRESS.md').exists():
        raise FileExistsError('Existing progress file requires inspection')
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    newest = data['turns'][0]
    teacher = next(item['text'] for item in newest['items'] if item['type'] == 'agentMessage')
    match = re.search(r':::writing\{variant="document" id="68421"\}\s*\n(.*?)\n:::', teacher, re.S)
    if not match:
        raise ValueError('Final teacher note block not found; do not invent it')
    final_notes = match.group(1)
    assert final_notes.startswith('# 第四次学习规划｜Day 01 学习笔记')
    assert '最终验收：12/12通过。' in final_notes
    ARCHIVE.mkdir(parents=True, exist_ok=False)
    NOTES.mkdir(parents=True, exist_ok=False)
    original_readme = (ROOT / 'README.md').read_bytes()
    write_readme_backup = ARCHIVE / 'README.before.md'
    with write_readme_backup.open('xb') as stream:
        stream.write(original_readme)
    with (ARCHIVE / 'gitignore.before.txt').open('xb') as stream:
        stream.write((ROOT / '.gitignore').read_bytes())
    prior_files = [ROOT / 'README.md', ROOT / '.gitignore']
    prior_files += [p for base in ['scripts', 'reports'] for p in (ROOT / base).rglob('*')
                    if p.is_file() and ARCHIVE not in p.parents]
    baseline = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(prior_files)}
    jwrite(ARCHIVE / 'existing_files_before.json', baseline)
    initial_git = [git('rev-parse', '--show-toplevel'), git('status', '--short', '--branch'), git('remote', '-v')]
    # This project was observed without a repository. Never initialize or guess a remote.
    if initial_git[0]['exit_code'] == 0:
        raise RuntimeError('Git repository appeared; inspect it before continuing this specific archive run')
    jwrite(ARCHIVE / 'git_before.json', initial_git)
    write(NOTES / '2026-10-28_teacher_final_notes.md', final_notes)

    transcript = ['# Day 01 可读取原始教学记录', '',
                  '来源聊天：' + data['thread']['title'],
                  '聊天 ID：`' + data['thread']['id'] + '`。只读检索，未向该聊天发送消息。',
                  '2026-10-28 通过应用 read_thread 取得 5 轮可访问记录；接口返回 hasMore=false、nextCursor=null。',
                  '这只表示当前接口没有提供更多记录，不能据此推断早期教学没有发生。',
                  '以下用户/教师正文按原文保留；学生错字和教师旧草稿保留。最终验收与最终笔记以最新一轮为准。',
                  '原聊天中的 UI 占位符、辅助图片搜索标记是历史文本，不是新执行操作；附件内容未随聊天接口返回。', '']
    for turn in reversed(data['turns']):
        date = dt.datetime.fromtimestamp(turn['startedAt'], dt.timezone(dt.timedelta(hours=8))).isoformat()
        transcript += ['## 教学轮次 `' + turn['id'] + '`', '', '时间：' + date, '']
        for item in turn['items']:
            if item['type'] == 'userMessage':
                content = '\n'.join(c['text'] for c in item.get('content', []) if c.get('type') == 'text')
                transcript += ['### 学生原始消息', '', content, '']
            elif item['type'] == 'agentMessage':
                transcript += ['### 教师原始消息', '', item['text'], '']
    write(NOTES / 'source_transcript.md', '\n'.join(transcript))

    qa = '''# Day 01 原规划问题 1—12：回答、批改与证据完整性

归档日期：2026-10-28。最终验收：教师确认 **12/12 通过**；本聊天用户也明确确认。

验收通过和原始记录齐全是两件事。当前能取得的 5 轮教学原文见 [原始教学记录](source_transcript.md)。题号映射依据教师的“第三章3.3最终理解检查”表，而不是把 3.2 节另外三道读图题冒充原规划第1—3题。

## 十二题总表

| 原题号 | 教师核对表所列知识点（不是缺失原题的重建） | 学生原答及过程证据 | 最终验收 |
| --- | --- | --- | --- |
| 1 | 监督分类的输入、标签、输出 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 2 | 128个时间点与9个通道 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 3 | 时间顺序为什么重要 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 4 | 没有照片为什么能识别活动 | 已取到题目、学生原答和批改 | 通过 |
| 5 | 六分类与连续数值预测的区别 | 已取到题目、学生原答及术语纠正 | 通过，需规范术语 |
| 6 | 原始窗口与561维统计特征 | 原题全文、学生原答、逐题批改与补学原文缺失；最终笔记只提供理解变化摘要 | 教师总体验收通过 |
| 7 | 训练、验证、测试集职责 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 8 | 为什么按受试者划分 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 9 | 相似、重叠窗口造成的问题 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 10 | 标准化的作用 | 已取到计算题、原答、批改、补讲、复测原答和最终批改 | 最终通过 |
| 11 | 为什么只用训练集拟合标准化参数 | 原题全文、学生原答、逐题批改与补学记录缺失 | 教师总体验收通过 |
| 12 | Shuffle与重新划分的区别 | 已取到教师本次验收问句、学生原答和批改；原规划文档本体未提供 | 通过 |

## 问题4

可取到的题目原文：UCI HAR模型没有看到人的照片，只输入九路加速度和角速度信号。为什么它仍然可能识别出步行、坐下等活动？

学生实际回答（保留原文）：

> 因为从九路加速度和角速度信号中提取到独属于步行、坐下等活动的特征，分类出这些任务

教师批改：通过。但“独属于某种活动的特征”表述过强，不一定有每类别完全独有的单一特征，应综合多个通道。详细教师原文在教学轮次 `75fbf4c3-8abd-4351-b144-46e97aff2220`。未取得该题另行复测的学生原答，不添加不存在的复测。

## 问题5

题目原文：如果使用同样的手机传感器数据，任务A是判断“步行还是上楼”，任务B是预测“行走速度是多少m/s”。两种任务在预测目标上有什么区别？

学生实际回答：

> 任务A是分类任务，B是预测任务

教师判定：通过核心判断，需要规范术语。教师补讲：A预测离散类别，B是回归，预测连续数值；分类与回归都属于预测，不能将分类与预测对立。补讲是教师解释，不是学生补答。原文同轮次 `75fbf4c3-8abd-4351-b144-46e97aff2220`。

## 问题10：初答、补学和最终复测

题目原文：某一传感器通道原来的均值是10、标准差是2。如果一个数值是14，标准化后是多少？这种转换可能怎样帮助模型训练？

学生初答：

> 2，消除尺度太大导致的误差

教师首次批改：计算正确，作用解释需补充，部分通过。补讲指出标准化调整输入尺度，可能改善优化，不能直接等同于消除预测误差或保证准确率提高。

教师最后补充题原文：

> 假设我们有两个传感器通道：
>
> - 通道A的数据通常在0～1之间。
> - 通道B的数据通常在1000～2000之间。
>
> 为什么适当的标准化可能帮助模型训练？标准化是不是意味着模型的预测误差一定会下降？

学生复测实际回答：

> 防止尺度过大给优化带来困难。不是的

教师最终批改：两部分均正确，问题10通过，不需要继续补考；据此确认正式理解题12/12通过。初答及补讲见 `75fbf4c3-8abd-4351-b144-46e97aff2220`，复测及最终结论见 `615e1c1e-4a56-4c5d-81e7-13b6dcd96bac`。

## 问题12

可取到的教师验收问句：已固定训练集6037个窗口、验证集1315个窗口、测试集2947个窗口；训练时设置 `shuffle=True`，是否会把训练样本重新分配到验证/测试集，与重新划分三个集合有什么区别？这是可访问教师验收问句的摘要，不声称是原规划逐字题面。完整问句保留在原始教学记录的 3.2 节教师消息末尾。

学生实际回答（错字不改）：

> 我认为不会，他只是训练集打乱顺序不涉及验证机和测试集

教师批改：完全正确，只改变训练样本读取顺序，不改变集合归属，无需补考。原文见 `5fde8c99-1d8e-43bd-8504-ccfcdaac2bc2`。教师题面中“训练CNN”的措辞属于假设示例，不是实际训练记录。

## 补充问答：3.2节真实信号理解（独立编号）

以下“问题1—3”是第3.2节的局部编号，**不映射为原规划正式题1—3**。来源：`f9938abd-09b9-4765-85fe-28d3bc50d2ba`。

1. 横纵轴与九条曲线的含义。学生原答：“横轴0到2.56秒，纵轴是9个特征。九条曲线代表9个特征维度，每个维度0到2.56秒”。教师判定通过但纠正：纵轴是各路信号的测量值，九条曲线是九路独立信号，不是纵轴九个数。
2. 步行与站立加速度曲线差别及分类作用。学生原答：“站立接近平缓，步行起伏大。特征区别很大”。教师判定通过，并补充可利用幅度、变化速度、时间模式和通道关系。
3. 能否从各一个窗口推广到全部样本。学生原答：“不能因为站立的body_gyro_x先起伏后平缓，不能说每个时刻所有步行样本的加速度变化都大于站立样本”。教师判定通过，同时纠正 body_gyro_x 是角速度，不能当加速度证据。

教师宣布3.2节本轮通过。没有把教师修正后的语句替换成学生原答。

## 最终状态及缺失项

- 第三章3.1—3.3、正式题1—12：最终验收通过。
- 数据实践：教师依据Codex执行摘要验收通过。
- 原题1、2、3、6、7、8、9、11的完整原始问答及早期补学过程：当前访问范围内缺失。没有用最终笔记或教师参考答案补造学生作答。
- 教师最终笔记中关于原始窗口、反向传播等理解变化是教师确认的总结，不能据此恢复缺失的逐字对话。
- 原规划文档全文未提供；本表题号由教师原有核对表确定。
- 第四章未开始、Day 02未开始。正式宣布Day 01整体结束仍待教师检查本次归档与同步结果。
'''
    write(NOTES / 'questions_01_12.md', qa)
    evidence = {
        'data_audit': 'reports/day01_data_20261026_run02/day01_data_audit.md',
        'execution_index': 'reports/day01_data_20261026_run02/execution_log.md',
        'download_provenance': 'reports/day01_data_20261026_run02/download_provenance.json',
        'archive_integrity': 'reports/day01_data_20261026_run02/archive_integrity.json',
        'independent_verification': 'reports/day01_data_20261026_run02/independent_verification.json',
        'split_metadata': 'data/processed/day01_data_20261026_run02_audit02/splits/split_metadata.json',
        'sample_manifest': 'data/processed/day01_data_20261026_run02_audit02/splits/sample_manifest.csv',
        'scaler': 'data/processed/day01_data_20261026_run02_audit02/scaler_train_only.json',
        'walking_png': 'outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.png',
        'walking_pdf': 'outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.pdf',
        'standing_png': 'outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.png',
        'standing_pdf': 'outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.pdf',
    }
    linked = {name: {'path': relative, 'exists': (ROOT / relative).is_file(),
                     'bytes': (ROOT / relative).stat().st_size, 'sha256': sha(ROOT / relative)}
              for name, relative in evidence.items()}
    jwrite(ARCHIVE / 'linked_evidence.json', linked)
    split = json.loads((ROOT / evidence['split_metadata']).read_text(encoding='utf-8'))
    scaler = json.loads((ROOT / evidence['scaler']).read_text(encoding='utf-8'))
    assert split['splits']['validation']['subjects'] == [1, 3, 5, 6]
    assert scaler['fit_windows'] == 6037 and scaler['fit_subject_ids'] == split['splits']['train']['subjects']
    historical = json.loads((ROOT / 'reports/day01_data_20261026_run02/delivery_artifact_manifest.json').read_text(encoding='utf-8'))
    drift = [name for name, info in historical.items() if not (ROOT / name).is_file() or sha(ROOT / name) != info['sha256']]
    assert not drift, drift
    jwrite(ARCHIVE / 'historical_delivery_manifest_check.json',
           {'entries': len(historical), 'mismatches': drift, 'status': 'PASS',
            'scope': 'Hash verification only; no data reprocessing, scaler fitting or model execution.'})
    link_lines = ['# Day 01 工程证据与使用说明', '',
                  '本次只关联既有结果并核对路径/哈希，不重新执行数据实验或训练。', '',
                  '| 证据 | 本地文件链接（相对项目根目录） |', '| --- | --- |']
    for name, relative in evidence.items():
        link_lines.append(f'| {name} | [{relative}](../../{relative}) |')
    link_lines += ['', '## 划分与标准化说明', '',
                   '验证集为官方训练受试者ID升序前4人：1、3、5、6。训练17人/6037窗，验证4人/1315窗，测试9人/2947窗，官方测试受试者与行顺序保持不变。',
                   '每通道以最终训练集6037×128=772736个值拟合float64均值和总体标准差（ddof=0），统一用于三集合，转换结果另存float32。完整参数仍在上表原路径；本次未重新拟合。',
                   '数据布局N×128×9；通道顺序body_acc_xyz、body_gyro_xyz、total_acc_xyz，原标签1—6。归档没有更改这些约定。', '',
                   '## 真实信号图', '',
                   'WALKING：受试者7、官方训练第1397行；STANDING：受试者7、官方训练第1316行。每图一个实测窗口，仅支持样本观察，不推广为总体结论。', '',
                   '![WALKING 九路信号](../../' + evidence['walking_png'] + ')', '',
                   '![STANDING 九路信号](../../' + evidence['standing_png'] + ')', '',
                   '## 同步边界', '',
                   '`data/`、`outputs/`、`logs/`继续被原.gitignore排除。这些证据链接在本机有效；未来仅同步文档时，GitHub上不会含原数据/数组/图文件，部分链接无法在线打开。这是本次保持忽略规则的明确限制，不声称已同步这些产物。',
                   '历史记录中的官方校验值未提供、首次网络权限失败、首次序列化失败和原版绘图门禁缺失等限制仍以数据审计报告为准，本次不将它们改写成通过。']
    write(NOTES / 'engineering_evidence.md', '\n'.join(link_lines))
    write(NOTES / 'README.md', '''# Day 01 学习归档

归档日期：2026-10-28。知识与数据实践验收通过；GitHub同步阻塞；第四章未开始。

- [教师确认的最终学习笔记](2026-10-28_teacher_final_notes.md)：保留九节原文。该原文由教师聊天取得，并由用户在本归档会话中再次提供确认。
- [原题1—12证据索引与缺失记录](questions_01_12.md)：区分学生原答、教师解释、补学和复测。
- [当前可取得的5轮原始教学记录](source_transcript.md)：保留旧草稿及后来的正式更正；以最新验收为准。
- [工程证据、标准化说明与真实图链接](engineering_evidence.md)。

最终笔记原文中的“待Codex写入本地仓库”等句子记录的是教师签发时状态，本次原文保留，当前实际状态以项目PROGRESS.md及归档报告为准：本地已写入学习目录，但项目尚无Git仓库，也未推送。没有将“教师验收12/12通过”解释成“12题原始对话已全部取回”。
''')
    progress = '''# 第四次学习规划进度

更新日期：2026-10-28，Asia/Shanghai。

| 项目 | 当前状态 | 依据 |
| --- | --- | --- |
| Day 01 第三章3.1—3.3知识理解 | 通过 | 教师最终原文及用户确认 |
| 原规划正式理解题1—12 | 12/12通过 | 教师最新问题10复测后总体验收 |
| Day 01数据实践 | 通过 | 教师依据Codex摘要验收；既有审计与独立复核 |
| 教师最终笔记本地归档 | 已完成 | learning_notes/day01/ |
| 原始问答归档完整性 | 部分可恢复 | 已有原题4、5、10、12；其余8题原答/过程缺失，未编造 |
| Git/GitHub同步 | 阻塞、未提交、未推送 | 当前无本地Git仓库、无remote，未验证认证/推送权限 |
| Day 01整体收尾 | 待教师复核归档与同步结果 | 不自行宣布整体结束 |
| 第四章 | 未开始 | 本次不开展任何模型训练 |
| Day 02 | 未开始 | 等待教师决定下一阶段 |

## 时间记录

- 2026-10-26：完成启动检查及UCI HAR数据实践；数据实践成功产物ID为day01_data_20261026_run02_audit02，失败现场保留。
- 2026-10-28：按教师与用户确认归档第三章12/12通过的最终笔记、可取回的教学原文、问答缺失索引和工程证据；完成本地变更审查。同步因无仓库/remote停止。

当前只记录已有学习成果；没有执行CNN、GRU、Transformer、Mamba训练或Day 02任务。
'''
    write(ROOT / 'PROGRESS.md', progress)
    updated_readme = '''# SequenceModel-HAR-Lab

《第四次学习规划》Day 01：UCI HAR监督式活动分类、真实九路时序信号、人员划分与预处理。

截至2026-10-28，教师确认第三章3.1—3.3及12道正式理解题全部通过，数据实践验收通过。最终笔记已本地归档；GitHub同步尚未完成。**第四章未开始，Day 02未开始。**

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

`data/`、`models/`、`outputs/`、`logs/`仍被忽略，数据集、标准化数组、模型权重、认证文件不作为提交内容。图表及数据链接指向本机被忽略文件，未来文档同步后不会自动在线可见。

## 环境与下一阶段

既有启动检查记录：Python 3.9.13、PyTorch 2.0.1+cpu，系统识别RTX 3060 Laptop 6GB；当时PyTorch无法使用CUDA，本次未重新安装或切换环境。尚未开展CNN、GRU、Transformer、Mamba训练。

目前项目没有Git仓库或remote，无法执行提交、推送及远程哈希核验。需要用户提供/配置目标GitHub仓库与可用授权后，重新核查同步条件；不擅自创建公开仓库。第四章及Day 02等待教师后续决定。

## 启动历史

- [原始启动检查报告](reports/day01_startup_check.md)
- [更新前README原文备份](reports/day01_archive_20261028_run01/README.before.md)

启动检查脚本仍为scripts/check_day01.ps1。旧报告及日志保留其原时间和状态，不将旧记录改写为当前结果。
'''
    # Only README is intentionally changed; original bytes are preserved above.
    assert (ROOT / 'README.md').read_bytes() == original_readme
    safe(ROOT / 'README.md')
    with (ROOT / 'README.md').open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(updated_readme)
    diff = git('diff', '--no-index', '--', str(write_readme_backup), str(ROOT / 'README.md'))
    write(ARCHIVE / 'README.diff', diff['stdout'] + diff['stderr'])
    assert diff['exit_code'] == 1
    final_git = [git('status', '--short', '--branch'), git('remote', '-v')]
    config = {}
    for key in ['user.name', 'user.email', 'credential.helper']:
        value = git('config', '--get', key)
        config[key + '_configured'] = bool(value['stdout'].strip())
    jwrite(ARCHIVE / 'git_sync_status.json', {
        'status': 'BLOCKED', 'reason': 'NO_LOCAL_GIT_REPOSITORY_AND_NO_REMOTE',
        'repository_exists': False, 'remote_url': None, 'local_commit': None, 'remote_commit': None,
        'authentication_verified': False, 'push_permission_verified': False,
        'github_cli_available': shutil.which('gh') is not None, 'git_config_presence_only': config,
        'git_add': 'NOT_RUN', 'git_commit': 'NOT_RUN', 'git_push': 'NOT_RUN',
        'remote_hash_verification': 'NOT_RUN', 'commands': final_git,
        'note': 'Credential helper presence does not establish login or write permission. No credential contents read.'})
    preserved = [name for name, expected in baseline.items() if name != 'README.md' and sha(ROOT / name) != expected]
    assert not preserved, preserved
    assert sha(ROOT / '.gitignore') == sha(ARCHIVE / 'gitignore.before.txt')
    assert all(sha(ROOT / item['path']) == item['sha256'] for item in linked.values())
    # Review only plausible documentation/code commit candidates; never scan credentials/raw datasets.
    candidates = [p for p in ROOT.rglob('*') if p.is_file() and
                  p.relative_to(ROOT).parts[0] not in {'data', 'models', 'outputs', 'logs', '.git', '.aws', '.ssh', '.codex', '.agents'}]
    patterns = {
        'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'github_token': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})'),
        'aws_access_key': re.compile(r'AKIA[A-Z0-9]{16}'),
        'credential_url': re.compile(r'https?://[^\s/]+:[^\s/@]+@'),
    }
    findings = []
    inventory = []
    forbidden = {'.zip', '.pt', '.pth', '.ckpt', '.npz', '.npy', '.pem', '.key', '.p12', '.pfx'}
    for path in candidates:
        relative = path.relative_to(ROOT).as_posix()
        inventory.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': sha(path)})
        if path.suffix.lower() in forbidden or path.name.startswith('.env'):
            findings.append({'path': relative, 'kind': 'forbidden_candidate_type'})
        if path.stat().st_size > 5 * 1024 * 1024:
            findings.append({'path': relative, 'kind': 'candidate_larger_than_5MiB'})
        if path.suffix.lower() in {'.py', '.ps1', '.md', '.json', '.txt', '.csv', '.diff'} or path.name == '.gitignore':
            content = path.read_text(encoding='utf-8', errors='replace')
            for label, pattern in patterns.items():
                if pattern.search(content):
                    findings.append({'path': relative, 'kind': label})
    assert not findings, findings
    jwrite(ARCHIVE / 'candidate_file_review.json', {'status': 'PASS', 'not_a_staged_file_list': True,
           'scope': 'Current documentation/code candidates, excluding ignored data/models/outputs/logs and credential directories; targeted token/key patterns and file sizes, not a complete secret detector.',
           'findings': findings, 'files': inventory})
    write(ARCHIVE / 'archive_report.md', '''# Day 01正式归档与GitHub同步报告

日期：2026-10-28（Asia/Shanghai）。项目：D:\\SequenceModel-HAR-Lab。

## 实际结果

- 已新增learning_notes/day01/，保存教师确认的九节最终学习笔记、原题1—12证据索引、可访问5轮教学原文、工程证据关联与归档说明。
- 第三章3.1—3.3、12/12理解题、数据实践验收通过。来源为教师最新正式结论，用户在本聊天再次确认。
- 更新README.md，新建PROGRESS.md；第四章未开始、Day 02未开始。尚未自行宣布Day 01整体结束，等待教师复核本归档与同步结果。
- 旧README按原字节保存为README.before.md；.gitignore未改，原文保存为gitignore.before.txt；旧报告、数据、参数和图文件未改。
- 历史交付清单48项哈希复核通过，工程证据链接存在且哈希已保存。只核对既有文件，不重新做数据实验、标准化拟合或训练。

## 问答记录完整性

已取得原题4、5、10、12的学生原答与教师批改；问题10含初答、补讲、复测和最终通过；另保留3.2节三个局部读图问答，不混作正式题1—3。原题1、2、3、6、7、8、9、11的题面全文、学生原答、逐题批改和补学原文在当前接口中缺失。教师12/12总体验收不因此改成未通过，但原始记录完整性只能标为部分恢复。没有编造缺失对话。

## Git与安全检查

实际运行git rev-parse、git status、git remote，均确认当前不是Git仓库。工作区git diff不适用；对更新前后README实际执行git diff --no-index并保存README.diff（退出1表示存在预期内容差异）。无分支、无HEAD、无remote。

Git有效身份和凭据助手配置存在；PATH无gh。未读取凭据值；未证明GitHub登录、推送权限或网络可用。凭据助手存在不等于认证成功。

原.gitignore继续排除data/models/checkpoints/outputs/runs/logs、权重/二进制数据、虚拟环境、常见密钥和认证文件。候选文档/代码文件做了大小、危险文件类型和特定令牌/私钥模式检查，结果见candidate_file_review.json；这是有范围的检查，不声称能检测一切敏感信息。日志原始聊天快照置于被忽略logs目录，附件临时路径不进入学习笔记。

## 同步阻塞与未执行项

**BLOCKED：当前没有本地Git仓库，也没有配置GitHub remote。** 按用户第7项要求，未初始化仓库、未猜测远程地址、未创建公开仓库，停止同步。

| 项目 | 实际结果 |
| --- | --- |
| remote地址 | 无 |
| 本地提交哈希 | 无（尚无仓库/提交） |
| git add | 未执行 |
| git commit | 未执行 |
| git push | 未执行 |
| 远程与本地提交哈希比较 | 未执行，无可比较提交 |
| 登录与目标仓库写权限 | 未验证 |

需要用户提供/配置目标GitHub仓库地址，并建立本项目仓库、提供可用认证后，才可重新审查、提交与推送。没有通过任意已有其他项目仓库代替本项目。

## 新增或修改文件

- 修改：README.md（原文备份保留）。
- 新增：PROGRESS.md。
- 新增：learning_notes/day01/README.md、2026-10-28_teacher_final_notes.md、questions_01_12.md、source_transcript.md、engineering_evidence.md。
- 新增：scripts/archive_day01_20261028.py（只做本次归档，不训练或推送）。
- 新增：reports/day01_archive_20261028_run01/ 内的本报告、README原文、忽略规则备份、README差异、Git检查、既有文件哈希基线、工程证据哈希、历史交付复核、候选文件审查和最终校验清单。
- 新增本地日志：logs/day01_archive_20261028_teacher_snapshot.json、day01_archive_20261028_execution.log；两者不作为提交候选。

未来仅同步文档时，数据、数组和原图继续被忽略，相应链接只在本机有效。尚未进行任何模型训练或Day 02工作。
''')
    new_paths = [p for p in NOTES.rglob('*') if p.is_file()] + [ROOT / 'README.md', ROOT / 'PROGRESS.md']
    new_paths += [p for p in ARCHIVE.rglob('*') if p.is_file()]
    jwrite(ARCHIVE / 'archive_delivery_manifest.json', {
        p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(new_paths)})
    print('Local archive complete. Third chapter PASS; fourth chapter/Day 02 NOT STARTED.')
    print('Original records preserved; README previous bytes backed up.')
    print('Recovered official questions: 4,5,10,12. Missing original records: 1,2,3,6,7,8,9,11.')
    print('GitHub sync BLOCKED: no local Git repository and no remote. add/commit/push NOT RUN.')
    print('Report: reports/day01_archive_20261028_run01/archive_report.md')


if __name__ == '__main__':
    main()
