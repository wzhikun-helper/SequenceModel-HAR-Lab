"""Independently verify saved predictions, and compare Seed42 test records."""
import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


HISTORICAL = [
    ('CNN A', 'cnn_baseline_seed42_20261119_run01'),
    ('GRU B', 'gru_baseline_seed42_20261121_run01'),
    ('Transformer C', 'transformer_baseline_seed42_20261122_run01'),
]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def check_predictions(data, report, recorded):
    with (report / 'test_predictions.csv').open(newline='') as source:
        rows = list(csv.DictReader(source))
    with np.load(data / 'test_standardized.npz', allow_pickle=False) as official:
        labels = (official['y'] - 1).tolist()
        indices = official['official_row_1based'].tolist()
    if not len(rows) == len(labels) == 2947:
        raise ValueError('Incomplete saved predictions')
    confusion = [[0] * 6 for _ in range(6)]
    losses = []
    for row, index, truth in zip(rows, indices, labels):
        scores = [float(row[f'logit_{i}']) for i in range(6)]
        pred = max(range(6), key=scores.__getitem__)
        if not all(map(math.isfinite, scores)) or (int(row['official_test_row_1based']),
                int(row['true_label_0based']), int(row['pred_label_0based'])) != (index, truth, pred):
            raise ValueError(f'Invalid saved prediction at official row {index}')
        confusion[truth][pred] += 1
        top = scores[pred]
        losses.append((top - scores[truth]) + math.log(math.fsum(math.exp(x - top) for x in scores)))

    tp = [confusion[i][i] for i in range(6)]
    support = [sum(row) for row in confusion]
    predicted = [sum(col) for col in zip(*confusion)]
    precision = [a / b if b else 0.0 for a, b in zip(tp, predicted)]
    recall = [a / b if b else 0.0 for a, b in zip(tp, support)]
    f1 = [2 * a / (b + c) if b + c else 0.0 for a, b, c in zip(tp, support, predicted)]
    metrics = dict(accuracy=sum(tp) / len(rows), macro_f1=math.fsum(f1) / 6,
                   loss=math.fsum(losses) / len(rows), precision=precision, recall=recall,
                   f1=f1, support=support, confusion_matrix=confusion)
    for key in ('accuracy', 'macro_f1', 'loss', 'precision', 'recall', 'f1'):
        atol = 1e-6 if key == 'loss' else 1e-14
        np.testing.assert_allclose(metrics[key], recorded[key], rtol=0, atol=atol)
    for key in ('support', 'confusion_matrix'):
        if metrics[key] != recorded[key]:
            raise ValueError(f'Independent {key} disagrees')
    save_json(report / 'independent_verification.json', dict(
        status='PASS', rows=len(rows), model_passes=0, recomputed=metrics,
        loss_abs_difference=abs(metrics['loss'] - recorded['loss'])))


def plot_results(records, activities, figures):
    names = list(records)
    style = {'color': '#243e69'}
    x = np.arange(len(names))
    fig, panels = plt.subplots(1, 3, figsize=(13.5, 3.7), constrained_layout=True)
    for axis, key, title in zip(panels, ('accuracy', 'macro_f1', 'parameters'),
                                ('Test Accuracy', 'Test Macro-F1', 'Trainable parameters')):
        values = [records[name][key] for name in names]
        bars = axis.bar(x, values, color=['#456892'] * 3 + ['#bc6229'])
        axis.set_title(title, **style)
        axis.set_xticks(x, names, rotation=15)
        labels = [f'{v:.2%}' for v in values] if key != 'parameters' else [f'{v:,}' for v in values]
        axis.bar_label(bars, labels=labels, padding=2)
        axis.set_ylim(0, 1.13 if key != 'parameters' else max(values) * 1.17)
        if key != 'parameters':
            axis.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    fig.savefig(figures / 'performance_parameters.png', dpi=180)
    plt.close(fig)

    colors = ['#456892', '#587448', '#716188', '#bc6229']
    fig, panels = plt.subplots(1, 3, figsize=(15, 5.2), sharey=True, constrained_layout=True)
    for axis, key in zip(panels, ('precision', 'recall', 'f1')):
        y = np.arange(6)
        for j, (name, color) in enumerate(zip(names, colors)):
            axis.barh(y + (j - 1.5) * .18, records[name][key], height=.16, label=name, color=color)
        axis.set_title(key.upper() if key == 'f1' else key.title())
        axis.set_yticks(y, [a.replace('_', ' ') for a in activities])
        axis.set_xlim(0, 1.04)
        axis.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))
    panels[0].invert_yaxis()
    panels[-1].legend(loc='lower right')
    fig.savefig(figures / 'class_metrics.png', dpi=180)
    plt.close(fig)

    abbr = ['Walk', 'Up', 'Down', 'Sit', 'Stand', 'Lay']
    fig, panels = plt.subplots(2, 2, figsize=(9, 8), constrained_layout=True)
    for axis, name in zip(panels.flat, names):
        cm = np.array(records[name]['confusion_matrix'])
        normalized = cm / cm.sum(axis=1, keepdims=True)
        image = axis.imshow(normalized, vmin=0, vmax=1, cmap='Blues')
        for i, j in np.ndindex(cm.shape):
            axis.text(j, i, str(cm[i, j]), ha='center', va='center',
                      color='white' if normalized[i, j] > .55 else '#19273c')
        axis.set_title(name)
        axis.set_xticks(range(6), abbr)
        axis.set_yticks(range(6), abbr)
        axis.set_xlabel('Predicted activity')
        axis.set_ylabel('True activity')
    fig.colorbar(image, ax=panels, label='Fraction within true class')
    fig.savefig(figures / 'confusion_matrices.png', dpi=180)
    plt.close(fig)


def main(project, data, run_dir):
    report, figures = run_dir / 'reports', run_dir / 'figures'
    mamba = read(report / 'test_metrics.json')
    check_predictions(data, report, mamba)
    historical = read(project / 'reports/mamba_l0_20261122/project_audit.json')['baselines']
    records = {}
    for (name, folder), audit in zip(HISTORICAL, historical):
        original = read(project / 'reports' / folder / 'test_metrics.json')
        if folder != audit['run'] or any(original[k] != audit[k] for k in ('accuracy', 'macro_f1', 'loss')):
            raise ValueError(f'Historical record differs for {name}')
        records[name] = dict(original, parameters=audit['parameters'], best_epoch=audit['best_epoch'],
                             epochs_completed=audit['epochs'], compute='CPU', source=folder)
    records['Mamba D'] = dict(mamba, compute='GPU')
    save_json(report / 'four_model_comparison.json', records)
    plot_results(records, mamba['activity_names'], figures)

    cm = np.array(mamba['confusion_matrix'])
    q = records['GRU B']
    detail = [
        '# UCI HAR Seed42 四模型对照', '',
        '| 模型 | Accuracy | Macro-F1 | Loss | 参数量 | 最佳 Epoch | 实际 Epoch | 设备 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |',
    ]
    for name, v in records.items():
        detail.append(f'| {name} | {v["accuracy"]:.4%} | {v["macro_f1"]:.4%} | {v["loss"]:.6f} | '
                      f'{v["parameters"]:,} | {v["best_epoch"]} | {v["epochs_completed"]} | {v["compute"]} |')
    detail += ['', '## Mamba D 逐类结果', '',
               '| 活动 | Precision | Recall | F1 | 样本数 |',
               '| --- | ---: | ---: | ---: | ---: |']
    for name, p, r, f, n in zip(mamba['activity_names'], mamba['precision'], mamba['recall'],
                               mamba['f1'], mamba['support']):
        detail.append(f'| {name} | {p:.4%} | {r:.4%} | {f:.4%} | {n} |')
    detail += [
        '', '## 错误分布', '',
        f'- SITTING → STANDING 为 {cm[3, 4]} / 491，STANDING → SITTING 为 {cm[4, 3]} / 532。',
        f'- WALKING → UPSTAIRS / DOWNSTAIRS 为 {cm[0, 1]} / {cm[0, 2]}；'
        f'UPSTAIRS → WALKING / DOWNSTAIRS 为 {cm[1, 0]} / {cm[1, 2]}；'
        f'DOWNSTAIRS → WALKING / UPSTAIRS 为 {cm[2, 0]} / {cm[2, 1]}。',
        f'- LAYING 正确 {cm[5, 5]} / 537，其他类误报 LAYING {cm[:5, 5].sum()} 次。',
        f'- 此次 Mamba D 的 Macro-F1 相对历史 GRU B 的差值为 '
        f'{(mamba["macro_f1"] - q["macro_f1"]) * 100:+.4f} 个百分点。',
        '', '四模型沿用同一官方测试集、受试者划分、训练集标准化和选模规则。'
        '历史三组来自 CPU，本次 Mamba 来自 GPU，训练耗时的横向比较缺少共同设备条件。'
        '模型参数量不同，Seed42 单次实验不足以推断模型家族在其他种子或受试者划分上的表现。'
        '混淆矩阵仅描述预测结果，误判机制尚未检验。', '',
        '[性能与参数量](../figures/performance_parameters.png) · '
        '[逐类指标](../figures/class_metrics.png) · [混淆矩阵](../figures/confusion_matrices.png)', '',
    ]
    with (report / 'four_model_comparison.md').open('x', encoding='utf-8') as stream:
        stream.write('\n'.join(detail))
    print('PASS: saved logits and predictions verified; four-model comparison written', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('data', type=Path)
    parser.add_argument('run_dir', type=Path)
    args = parser.parse_args()
    main(args.project, args.data, args.run_dir)
