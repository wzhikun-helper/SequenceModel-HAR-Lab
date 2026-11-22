"""Build a Chinese research draft from archived metrics, without model execution."""
import argparse
import csv
import hashlib
import itertools
import json
import math
import shutil
import subprocess
from pathlib import Path
from statistics import mean, stdev

from fig05_har_research import plot

ROOT = Path(__file__).resolve().parents[1]
MAMBA = Path('experiments/mamba_baseline_d_seed42_20261122')
ABLATION = Path('reports/cnn_ablation_20261122')
BASELINES = [
    ('CNN A', Path('reports/cnn_baseline_seed42_20261119_run01'), 'CPU'),
    ('GRU B', Path('reports/gru_baseline_seed42_20261121_run01'), 'CPU'),
    ('Transformer C', Path('reports/transformer_baseline_seed42_20261122_run01'), 'CPU'),
    ('Mamba D', MAMBA / 'reports', 'RTX 3090'),
]
METRICS = ('accuracy', 'macro_f1', 'loss')
CLASSES = ['WALKING', 'WALKING_UPSTAIRS', 'WALKING_DOWNSTAIRS', 'SITTING', 'STANDING', 'LAYING']
SUPPORT = [496, 471, 420, 491, 532, 537]


def require(condition, description):
    if not condition:
        raise ValueError(description)


def close(a, b):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)


class Archive:
    def __init__(self):
        self.sources = {}

    def read(self, path):
        path = Path(path)
        source = (ROOT / path).resolve()
        require(source == ROOT / path, f'Unexpected archive path: {path}')
        content = source.read_bytes()
        self.sources[path.as_posix()] = hashlib.sha256(content).hexdigest()
        return content.decode('utf-8-sig')

    def json(self, path):
        return json.loads(self.read(path))

    def csv(self, path):
        return list(csv.DictReader(self.read(path).splitlines()))

    def run(self, directory):
        test = self.json(directory / 'test_metrics.json')
        result = self.json(directory / 'training_result.json')
        cm = test['confusion_matrix']
        require(test['activity_names'] == CLASSES and test['support'] == SUPPORT and test['n'] == sum(SUPPORT),
                f'Class contract mismatch: {directory}')
        require(len(cm) == 6 and all(len(row) == 6 and all(type(n) is int and n >= 0 for n in row) for row in cm)
                and [sum(row) for row in cm] == SUPPORT, f'Invalid confusion matrix: {directory}')
        diag = [cm[i][i] for i in range(6)]
        predicted = [sum(col) for col in zip(*cm)]
        for key, numerator, denominator in [
            ('precision', diag, predicted), ('recall', diag, SUPPORT),
            ('f1', [2 * n for n in diag], [a + b for a, b in zip(SUPPORT, predicted)]),
        ]:
            require(len(test[key]) == 6 and all(close(v, n / d if d else 0)
                    for v, n, d in zip(test[key], numerator, denominator)), f'{key}: {directory}')
        require(close(test['accuracy'], sum(diag) / sum(SUPPORT))
                and close(test['macro_f1'], mean(test['f1']))
                and math.isfinite(test['loss']) and test['loss'] >= 0, f'Test metrics: {directory}')
        require(result['status'] == 'PASS' and 1 <= result['best_epoch'] <= result['epochs_completed'] <= 30,
                f'Training status: {directory}')
        return test, result


def collect(archive):
    comparison = archive.json(MAMBA / 'reports/four_model_comparison.json')
    models = []
    for name, folder, device in BASELINES:
        test, result = archive.run(folder)
        summary = archive.json(folder / 'model_summary.json')
        config = archive.json(MAMBA / 'configs/seed42.json' if name == 'Mamba D' else folder / 'config.json')
        require(config['seed'] == 42, f'{name}: baseline seed')
        model = dict(model=name, device=device, **{k: test[k] for k in METRICS},
                     parameters=summary['actual_parameters'], best=result['best_epoch'], epochs=result['epochs_completed'])
        record = comparison[name]
        require(all(close(record[k], test[k]) for k in METRICS)
                and all(record[k] == test[k] for k in ('confusion_matrix', 'activity_names', 'checkpoint_sha256'))
                and record['parameters'] == model['parameters'] and record['best_epoch'] == model['best']
                and record['epochs_completed'] == model['epochs'], f'Four-model comparison mismatch: {name}')
        models.append(model)

    rows = archive.csv(ABLATION / 'results.csv')
    pairs = archive.csv(ABLATION / 'paired.csv')
    stats = archive.json(ABLATION / 'statistics.json')
    expected = list(itertools.product((42, 43, 44), 'ABC'))
    require([(int(r['seed']), r['group']) for r in rows] == expected, 'Unexpected ablation design/order')
    groups = {key: [] for key in 'ABC'}
    for row, (seed, group) in zip(rows, expected):
        folder = BASELINES[0][1] if (seed, group) == (42, 'A') else ABLATION / f'cnn_ablation_{group}_seed{seed}_20261122_run01'
        require(row['run'] == folder.as_posix(), f'Run source: {seed}/{group}')
        test, result = archive.run(folder)
        require(all(close(row[k], test[k]) for k in METRICS)
                and int(row['best']) == result['best_epoch'] and int(row['epochs']) == result['epochs_completed']
                and int(row['parameters']) == (models[0]['parameters'] if folder == BASELINES[0][1] else result['parameters']),
                f'Ablation result mismatch: {seed}/{group}')
        groups[group].append(test['macro_f1'])
    require(len(pairs) == len(stats['paired']) == 3, 'Missing paired results')
    for key, values in groups.items():
        require(close(stats[key]['mean'], mean(values)) and close(stats[key]['sample_sd'], stdev(values)),
                f'Ablation summary mismatch: {key}')
    for i, (pair, saved) in enumerate(zip(pairs, stats['paired'])):
        ba, bc = [100 * (groups['B'][i] - groups[key][i]) for key in 'AC']
        require(int(pair['seed']) == saved[0] == 42 + i and close(ba, saved[1]) and close(bc, saved[2])
                and close(ba, pair['B_minus_A_percentage_points']) and close(bc, pair['B_minus_C_percentage_points']),
                f'Paired difference mismatch: {i}')
    data = archive.json(MAMBA / 'reports/data_hashes.json')
    require(len(data['observed']) == 4 and data['observed'] == data['historical']
            and data['byte_matches'] == dict.fromkeys(data['observed'], True), 'Archived frozen data mismatch')
    archive.read('docs/data_protocol.md')
    split = archive.json('docs/day01/split_metadata.json')['splits']
    require([split[k]['n_windows'] for k in ('train', 'validation', 'test')] == [6037, 1315, 2947]
            and sum(len(split[k]['subjects']) for k in split) == len({s for k in split for s in split[k]['subjects']}) == 30,
            'Published split mismatch')
    return models, rows, pairs, stats, data['observed']


def write_csv(path, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, rows[0])
        writer.writeheader()
        writer.writerows(rows)


def tex_tables(output, models, rows, stats):
    end = ' ' + chr(92) * 2
    baseline = [' & '.join([r['model'], *(f'{r[k]:.6f}' if k == 'loss' else f'{100*r[k]:.4f}' for k in METRICS),
                            f"{r['parameters']:,}", f"{r['best']}/{r['epochs']}", r['device']]) + end for r in models]
    runs = [' & '.join([r['seed'], r['group'], *(f'{100*float(r[k]):.4f}' for k in METRICS[:2]),
                        f"{float(r['loss']):.6f}", f"{r['best']}/{r['epochs']}"]) + end for r in rows]
    summaries = [f"{group} & {100*stats[group]['mean']:.4f} & {100*stats[group]['sample_sd']:.4f}" + end for group in 'ABC']
    for name, lines in [('baseline_rows', baseline), ('ablation_rows', runs), ('summary_rows', summaries)]:
        (output / f'{name}.tex').write_text('\n'.join(lines + [r'\bottomrule']) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.absolute()
    require(output.parent.resolve() == ROOT / 'reports', 'Use a fresh direct child of reports/')
    output.mkdir(exist_ok=False)
    archive = Archive()
    models, rows, pairs, stats, hashes = collect(archive)
    write_csv(output / 'baselines.csv', models)
    write_csv(output / 'ablation.csv', rows)
    write_csv(output / 'paired.csv', pairs)
    tex_tables(output, models, rows, stats)
    shutil.copyfile(ROOT / 'scripts/templates/har_research_report.tex', output / 'report.tex')
    outputs = plot(output)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    evidence = dict(base_commit=head, archive_sha256=archive.sources, frozen_archive_sha256=hashes,
                    plot_files=[p.name for p in outputs], test_windows=sum(SUPPORT), runs_checked=12)
    (output / 'input_manifest.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: 12 distinct runs, 3 paired seeds, {len(archive.sources)} archived sources; outputs in {output.name}')


if __name__ == '__main__':
    main()
