"""Read-only checks for public entry points; standard library only.

Historical transcripts/reports intentionally retain execution-machine paths.
This checks curated entry pages, their assets, and published metadata, not those archives.
"""
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import subprocess
from statistics import mean
from urllib.parse import unquote, urlsplit

from har_contracts import validate_scaler_provenance

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    'README.md', 'README.en.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
    'PROGRESS.md', 'docs/README.md', 'docs/data_protocol.md',
    'docs/reproducing_day01.md', 'docs/day01/README.md',
    'docs/verification.md',
    'learning_notes/day01/README.md', 'scripts/README.md', 'reports/README.md',
    'learning_notes/day01/evidence_index.md', 'reports/remediation_round1_20261031/README.md',
    'docs/day02_cnn.md', 'learning_notes/day02/README.md',
    'reports/day02_cnn_20261111_run01/README.md',
    'reports/cnn_baseline_seed42_20261119_run01/README.md',
    'reports/cnn_baseline_seed42_20261119_run01/execution_report.md',
    'reports/cnn_baseline_seed42_20261119_run01/reproducibility.md',
    'learning_notes/day02/2026-11-19_cnn_baseline_a.md',
    'reports/gru_baseline_preflight_20261121/audit_report.md',
    'reports/gru_baseline_seed42_20261121_run01/README.md',
    'reports/gru_baseline_seed42_20261121_run01/execution_report.md',
    'reports/gru_baseline_seed42_20261121_run01/cnn_gru_comparison.md',
    'reports/gru_baseline_seed42_20261121_run01/reproducibility.md',
    'learning_notes/day02/2026-11-21_gru_baseline_b.md',
    'reports/transformer_preflight_20261122/audit_report.md',
    'reports/transformer_baseline_seed42_20261122_run01/README.md',
    'reports/transformer_baseline_seed42_20261122_run01/execution_report.md',
    'reports/transformer_baseline_seed42_20261122_run01/three_model_comparison.md',
    'reports/transformer_baseline_seed42_20261122_run01/reproducibility.md',
    'learning_notes/day02/2026-11-22_transformer_baseline_c.md',
    'reports/cnn_ablation_audit_20261122/README.md',
    'reports/cnn_ablation_20261122/README.md',
    'learning_notes/chapter05_cnn_ablation.md',
    'reports/mamba_l0_20261122/README.md',
    'learning_notes/mamba_baseline_d.md',
    '.agents/skills/uci-har-experiment-workflow/SKILL.md',
    'learning_notes/chapter06_lesson01.md',
    'reports/chapter06_lesson01_research_draft/README.md',
    'docs/experiment_registry.md',
    'docs/repository_audit_20261123.md',
    'docs/project_organization_references.md',
    'docs/fourth_plan_archive_errata.md',
    'docs/gru_task03_protocol.md',
    'reports/gru_multiseed_task03_20261123/README.md',
    'reports/fourth_plan_final_archive_20261123/README.md',
    'reports/repository_organization_20261123/acceptance.md',
]
SKILL = '.agents/skills/uci-har-experiment-workflow/SKILL.md'
REGISTRY = 'docs/experiment_registry.md'
PROTECTED_DIRS = {
    'data', 'models', 'outputs', 'runs', 'logs', 'checkpoints', '.aws', '.ssh',
    '.codex', '.agents', '.venv', 'venv', 'env', '__pycache__', '.pytest_cache',
}
PROTECTED_SUFFIXES = {
    '.pt', '.pth', '.ckpt', '.npy', '.npz', '.onnx', '.h5', '.hdf5', '.pkl',
    '.pickle', '.joblib', '.log', '.pyc', '.pyo', '.pem', '.key', '.p12', '.pfx', '.token',
}
SOURCE_LINK = re.compile(r'\[[^\]]+\]\(([^)]+)\)')


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            if not attrs.get('alt'):
                self.errors.append('image is missing alt text')
            if attrs.get('src'):
                self.links.append(attrs['src'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def check_tracked_files(errors):
    raw = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT)
    for name in raw.decode('utf-8').split('\0'):
        if not name or name == SKILL:
            continue
        path = Path(name.lower())
        forbidden = (
            PROTECTED_DIRS.intersection(path.parts[:-1])
            or path.suffix in PROTECTED_SUFFIXES
            or path.name in {'.env', '.git-credentials', '.netrc', '_netrc'}
            or (path.name.startswith('.env.') and path.name != '.env.example')
        )
        require(not forbidden, 'unexpected tracked local artifact: ' + name, errors)
        if path.suffix == '.json' and (ROOT / name).is_file():
            try:
                json.loads((ROOT / name).read_text(encoding='utf-8-sig'))
            except (ValueError, UnicodeError) as exc:
                errors.append(f'{name}: invalid JSON: {exc}')


def markdown_rows(path):
    return [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in path.read_text(encoding='utf-8').splitlines() if line.startswith('|')]


def check_registry(errors):
    registry = ROOT / REGISTRY
    rows = markdown_rows(registry)
    runs = [row for row in rows if len(row) > 1 and row[1].startswith(chr(96))]
    baselines = {'CNN A', 'GRU B', 'Transformer C', 'Mamba D'}
    expected = {(model, 42) for model in baselines}
    expected.update((f'CNN 消融 {group}', seed) for group in 'ABC' for seed in (42, 43, 44)
                    if (group, seed) != ('A', 42))
    expected.update(('GRU Task03', seed) for seed in (42, 43, 44))
    metrics = {}
    parameters = {}
    for row in runs:
        if len(row) != 13 or not row[2].isdigit() or not all(SOURCE_LINK.fullmatch(cell) for cell in row[3:12]):
            errors.append('invalid registry evidence row: ' + str(row[:3]))
            continue
        key = (row[0], int(row[2]))
        require(key not in metrics, f'duplicate registry entry: {key}', errors)
        require(row[12] in {'PASS', 'PARTIAL'}, f'invalid registry evidence status: {key}', errors)
        source = registry.parent / SOURCE_LINK.fullmatch(row[6])[1]
        try:
            record = json.loads(source.read_text(encoding='utf-8'))
            require(record['n'] == 2947, f'unexpected test window count: {key}', errors)
            if key[0] in baselines:
                summary = source.with_name('model_summary.json')
                count = json.loads(summary.read_text(encoding='utf-8'))['actual_parameters']
                parameters[key[0]] = f'{count:,}'
            metrics[key] = record
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f'{key}: unreadable metrics: {exc}')
    require(set(metrics) == expected and len({row[1] for row in runs}) == 15,
            'registry run coverage or unique Run IDs changed', errors)
    if set(metrics) != expected:
        return

    def pct(value):
        return f'{100 * value:.4f}'

    def values(record):
        return pct(record['accuracy']) + '%', pct(record['macro_f1']) + '%', f"{record['loss']:.6f}"

    ablation = []
    for group in 'ABC':
        scores = [metrics['CNN A' if (group, seed) == ('A', 42) else f'CNN 消融 {group}', seed]['macro_f1']
                  for seed in (42, 43, 44)]
        ablation.append(tuple(map(pct, scores + [mean(scores)])))
    gru = [metrics['GRU Task03', seed] for seed in (42, 43, 44)]
    gru_values = [values(r) for r in gru]
    gru_values.append(values({metric: mean(r[metric] for r in gru)
                              for metric in ('accuracy', 'macro_f1', 'loss')}))

    for name in ('README.md', 'README.en.md', REGISTRY):
        table_rows = markdown_rows(ROOT / name)
        for model in baselines:
            value = (*values(metrics[model, 42]), parameters[model])
            require(any(row[0] == model and row[1:5] == value for row in table_rows),
                    f'{name}: baseline metrics differ for {model}', errors)
        for group, value in zip('ABC', ablation):
            require(any(row[0].split()[0] == group and row[1:5] == value
                        for row in table_rows if row[0]), f'{name}: ablation metrics differ for {group}', errors)
        for label, value in zip(('42', '43', '44', 'mean'), gru_values):
            require(any(row[0].lower().replace('均值', 'mean') == label and row[1:4] == value
                        for row in table_rows), f'{name}: Task03 metrics differ for {label}', errors)



def check_task03_report_guards(errors):
    path = ROOT / 'scripts/report_gru_task03.py'
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except (OSError, SyntaxError) as exc:
        errors.append('Task03 report guard check could not parse script: ' + str(exc))
        return
    asserts = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    require(not asserts, 'Task03 report verification must use explicit checks, not optimizable assert statements', errors)


def main():
    errors = []
    link_count = 0
    for name in PAGES:
        page = ROOT / name
        if not page.is_file():
            errors.append('missing entry page: ' + name)
            continue
        text = page.read_text(encoding='utf-8')
        require(text.count('```') % 2 == 0, name + ': unclosed code fence', errors)
        require(text.count('<details>') == text.count('</details>'), name + ': unclosed details block', errors)
        visible = re.sub(r'```.*?```', '', text, flags=re.S)
        html = HTMLLinks()
        html.feed(visible)
        errors.extend(name + ': ' + error for error in html.errors)
        links = re.findall(r'!?\[[^\]\n]*\]\(([^\s)]+)\)', visible) + html.links
        for target in links:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (page.parent / unquote(parsed.path)).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(name + ': link escapes repository: ' + target)
                continue
            require(resolved.exists(), name + ': missing local target: ' + target, errors)
            link_count += 1
    for script in sorted((ROOT / 'scripts').glob('*.py')):
        try:
            ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
        except SyntaxError as exc:
            errors.append(script.name + ': ' + str(exc))

    check_tracked_files(errors)
    check_registry(errors)
    check_task03_report_guards(errors)

    meta = json.loads((ROOT / 'docs/day01/split_metadata.json').read_text(encoding='utf-8'))
    scaler = json.loads((ROOT / 'docs/day01/standardization_train_only.json').read_text(encoding='utf-8'))
    splits = meta['splits']
    try:
        validate_scaler_provenance(scaler, meta)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append('published data contract: ' + str(exc))
    require(splits['validation']['subjects'] == [1, 3, 5, 6], 'validation metadata changed', errors)
    for name, expected in [('train', 6037), ('validation', 1315), ('test', 2947)]:
        require(splits[name]['n_windows'] == expected, name + ': window count mismatch', errors)
        require(sum(splits[name]['class_counts'].values()) == expected, name + ': class counts mismatch', errors)

    assets = json.loads((ROOT / 'docs/day01/asset_provenance.json').read_text(encoding='utf-8'))
    for asset in assets:
        path = ROOT / asset['documentation_copy']
        content = path.read_bytes()
        require(hashlib.sha256(content).hexdigest() == asset['sha256'],
                path.name + ': published asset hash mismatch', errors)
        require(len(content) == asset['bytes'], path.name + ': asset size mismatch', errors)
        if path.suffix == '.png':
            require(content[:8] == b'\x89PNG\r\n\x1a\n', path.name + ': invalid PNG signature', errors)
            require(struct.unpack('>II', content[16:24]) == (2460, 3450), path.name + ': PNG dimensions changed', errors)
    if errors:
        for error in errors:
            print('FAIL:', error)
        raise SystemExit(1)
    print(f'PASS: {len(PAGES)} public entry pages, {link_count} local references, Python syntax and published metadata/assets.')
    print('Scope: offline documentation checks; no raw data, preprocessing, model training or external-link requests.')


if __name__ == '__main__':
    main()
