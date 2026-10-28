"""Prepare reviewed Day 01 documentation assets without changing original data."""
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / 'logs/day01_github_sync_20261028_run01'
DOCS = ROOT / 'docs/day01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for path in [LOG, DOCS]:
        for parent in [path, *path.parents]:
            if parent.exists() and (parent.is_symlink() or getattr(parent.lstat(), 'st_file_attributes', 0) & 1024):
                raise ValueError('Linked output rejected')
            if parent == ROOT:
                break
        if path.exists():
            raise FileExistsError('Refusing to overwrite: ' + str(path))
    LOG.mkdir(parents=True)
    DOCS.mkdir(parents=True)
    changes = ['README.md', 'PROGRESS.md', '.gitignore', 'learning_notes/day01/README.md',
               'learning_notes/day01/engineering_evidence.md']
    baseline = {}
    for name in changes:
        source = ROOT / name
        target = LOG / 'before' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(source.read_bytes())
        baseline[name] = sha(source)
    copies = {
        'walking_nine_channels.png': 'outputs/figures/day01_data_20261026_run02_audit02/fig01_walking_nine_channels.png',
        'standing_nine_channels.png': 'outputs/figures/day01_data_20261026_run02_audit02/fig01_standing_nine_channels.png',
        'split_metadata.json': 'data/processed/day01_data_20261026_run02_audit02/splits/split_metadata.json',
        'standardization_train_only.json': 'data/processed/day01_data_20261026_run02_audit02/scaler_train_only.json',
    }
    copy_manifest = []
    for name, relative in copies.items():
        source, target = ROOT / relative, DOCS / name
        if source.stat().st_size > 1024 * 1024:
            raise ValueError('Documentation asset exceeds 1 MiB')
        if source.suffix == '.png':
            with Image.open(source) as im:
                assert im.size == (2460, 3450)
                assert min(im.info['dpi']) > 299
                im.verify()
        before = sha(source)
        with target.open('xb') as stream:
            stream.write(source.read_bytes())
        assert sha(source) == sha(target) == before
        copy_manifest.append({'source': relative, 'documentation_copy': target.relative_to(ROOT).as_posix(),
                              'bytes': target.stat().st_size, 'sha256': before})
    with (DOCS / 'asset_provenance.json').open('x', encoding='utf-8') as stream:
        json.dump(copy_manifest, stream, ensure_ascii=False, indent=2)
    with (LOG / 'before_hashes.json').open('x', encoding='utf-8') as stream:
        json.dump(baseline, stream, ensure_ascii=False, indent=2)
    (DOCS / 'README.md').write_text('''# Day 01 可在GitHub查看的工程证据

这里只保存两张代表性实验图和小型划分/标准化元数据，不包含原始数据集、窗口数组或模型权重。所有副本与原文件SHA-256一致，见[副本来源清单](asset_provenance.json)。原文件未修改。

## 数据与划分

UCI HAR官方数据实践：每窗口128个采样点×9通道，50 Hz，采集窗口2.56秒；采样点时间0—2.54秒。原始标签1—6保留。

| 集合 | 受试者人数 | 窗口数 |
| --- | ---: | ---: |
| 最终训练 | 17 | 6037 |
| 验证 | 4 | 1315 |
| 官方测试 | 9 | 2947 |

验证受试者是官方训练ID升序前4人：1、3、5、6。三个集合受试者两两不重叠，官方测试划分保持不变。完整人员ID和类别计数见[划分元数据](split_metadata.json)。逐窗口清单和标准化数组保留本地，不上传。

每通道仅用最终训练集6037×128个值拟合float64均值和总体标准差（ddof=0），同一参数用于训练、验证、测试，转换结果另存float32。参数见[训练集标准化参数](standardization_train_only.json)。本次只复制既有参数，未重新拟合。

## WALKING：受试者7，官方训练第1397行

![WALKING九路真实信号](walking_nine_channels.png)

## STANDING：受试者7，官方训练第1316行

![STANDING九路真实信号](standing_nine_channels.png)

每图只有一个指定的最终训练窗口；九路信号保留g或rad/s物理单位，对应通道使用相同纵轴范围。图只用于样本观察，不据此推断所有活动样本的普遍差异，也不表示模型性能。

来源：[UCI Human Activity Recognition Using Smartphones](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones)，Reyes-Ortiz等，DOI 10.24432/C54S4K。图由本项目既有绘图脚本生成。

完整历史说明见[数据审计报告](../../reports/day01_data_20261026_run02/day01_data_audit.md)及[独立复核记录](../../reports/day01_data_20261026_run02/independent_verification.json)。历史审计内指向data/outputs/logs的路径只在本机有效，本页提供了选定代表性图的可追踪副本。
''', encoding='utf-8')
    readme = ROOT / 'README.md'
    text = readme.read_text(encoding='utf-8')
    text = text.replace('最终笔记已本地归档；GitHub同步尚未完成。', '最终笔记已本地归档；本项目使用下列GitHub仓库进行版本同步。')
    text = text.replace('`data/`、`models/`、`outputs/`、`logs/`仍被忽略，数据集、标准化数组、模型权重、认证文件不作为提交内容。图表及数据链接指向本机被忽略文件，未来文档同步后不会自动在线可见。',
                        '`data/`、`models/`、`outputs/`、`logs/`仍被忽略，数据集、标准化数组、模型权重、认证文件不作为提交内容。两张代表性真实图及小型划分/标准化元数据的可追踪副本见[Day 01文档证据](docs/day01/README.md)，原数据及原图保持不变；其他指向被忽略目录的历史链接仅在本机有效。')
    text = text.replace('目前项目没有Git仓库或remote，无法执行提交、推送及远程哈希核验。需要用户提供/配置目标GitHub仓库与可用授权后，重新核查同步条件；不擅自创建公开仓库。第四章及Day 02等待教师后续决定。',
                        '用户指定远程仓库：[wzhikun-helper/SequenceModel-HAR-Lab](https://github.com/wzhikun-helper/SequenceModel-HAR-Lab)，主分支`main`。同步结果以远程分支提交与本地同步报告核验为准；本地运行报告保存在被忽略的`logs/day01_github_sync_20261028_run01/`。历史归档报告描述其当时的阻塞状态。第四章及Day 02等待教师后续决定。')
    readme.write_text(text, encoding='utf-8')
    progress = ROOT / 'PROGRESS.md'
    text = progress.read_text(encoding='utf-8').replace('| Git/GitHub同步 | 阻塞、未提交、未推送 | 当前无本地Git仓库、无remote，未验证认证/推送权限 |',
          '| Git/GitHub同步 | 已配置用户指定origin/main；实际推送结果以核验报告为准 | https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git；本地报告logs/day01_github_sync_20261028_run01/ |')
    text += '\n- 2026-10-28（同步阶段）：用户提供目标HTTPS地址，初始化main并配置origin；复制两张已检查的真实PNG及小型元数据至docs/day01，不改原始产物。提交和推送结果单独保存并核验，不提前记录为成功。\n'
    progress.write_text(text, encoding='utf-8')
    note_index = ROOT / 'learning_notes/day01/README.md'
    text = note_index.read_text(encoding='utf-8').replace('GitHub同步阻塞', 'GitHub目标已配置，结果见同步报告')
    text = text.replace('本地已写入学习目录，但项目尚无Git仓库，也未推送。', '本地已写入学习目录，后续Git初始化与同步状态以项目PROGRESS.md及最新同步报告为准。')
    note_index.write_text(text, encoding='utf-8')
    evidence = ROOT / 'learning_notes/day01/engineering_evidence.md'
    text = evidence.read_text(encoding='utf-8')
    text = text.replace('## 同步边界', '## 可追踪文档副本\n\n选定WALKING/STANDING图和划分/标准化元数据可在线查看的副本见[Day 01文档证据](../../docs/day01/README.md)。原文件保留本地，副本已核对来源与哈希。\n\n## 同步边界')
    text = text.replace('这些证据链接在本机有效；未来仅同步文档时，GitHub上不会含原数据/数组/图文件，部分链接无法在线打开。这是本次保持忽略规则的明确限制，不声称已同步这些产物。',
                        '上述原始证据链接在本机有效；GitHub不含原始数据/数组和原outputs目录。docs/day01只提供明确选定的两张图及小型元数据副本，其余本机路径不会自动在线可见。')
    evidence.write_text(text, encoding='utf-8')
    ignore = ROOT / '.gitignore'
    with ignore.open('a', encoding='utf-8') as stream:
        stream.write('\n# Local agent state and additional authentication files\n/.codex/\n/.agents/\n.git-credentials\n.netrc\n_netrc\n*.token\n')
    print('Prepared documentation assets and metadata; original files hash-identical.')
    print('Target: https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git; branch main')


if __name__ == '__main__':
    main()
