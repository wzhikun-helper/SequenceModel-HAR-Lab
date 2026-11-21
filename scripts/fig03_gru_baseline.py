"""GRU plots from saved CSV; public PNG/PDF, editable SVG retained locally."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from day01_figure_style import paper_style, save

ROOT = Path(__file__).resolve().parents[1]


def main(run, revision=None):
    report = ROOT / 'reports' / run
    result = json.loads((report / 'training_result.json').read_text(encoding='utf-8'))
    if result['status'] != 'PASS':
        raise RuntimeError('Training has not passed')
    if revision is not None and not revision.replace('_', '').isalnum():
        raise ValueError('Unsafe figure revision ID')
    output = ROOT / 'outputs/figures' / (run + '_' + revision if revision else run)
    output.mkdir(parents=True, exist_ok=False)
    with (report / 'training_history.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    with (report / 'confusion_matrix.csv').open(encoding='utf-8', newline='') as stream:
        cmrows = list(csv.reader(stream))
    matrix = np.array([[int(x) for x in row[1:]] for row in cmrows[1:]])
    contracts = dict(training_curves=dict(claim='One observed run, validation-selected epoch marked on all panels',
                    source='training_history.csv', hero='Training and validation cross-entropy',
                    support='Validation Macro-F1 and validation accuracy'),
                    confusion_matrix=dict(claim='Best-checkpoint official test error distribution',
                    source='confusion_matrix.csv', hero='True-vs-predicted window counts'))
    (output / 'figure_contracts.json').write_text(json.dumps(contracts, indent=2), encoding='utf-8')
    colors = paper_style()
    epochs = [int(row['epoch']) for row in rows]
    best = result['best_epoch']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = []

    def export(fig, name):
        for path in save(fig, output / name):
            entry = dict(local_path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                         sha256=sha(path), source_csv=contracts[name]['source'],
                         source_sha256=sha(report / contracts[name]['source']))
            if path.suffix in ['.png', '.pdf']:
                target = report / path.name
                if target.exists():
                    raise FileExistsError(target)
                shutil.copyfile(path, target)
                assert sha(target) == sha(path)
                entry['public_path'] = target.relative_to(ROOT).as_posix()
            else:
                entry['public_path'] = None
                entry['scope'] = 'Editable SVG retained in ignored local outputs; PNG/PDF published'
            if path.suffix == '.png':
                with Image.open(path) as image:
                    image.load()
                    entry.update(pixels=list(image.size), dpi=list(image.info['dpi']))
            manifest.append(entry)
        plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(7, 7.8), sharex=True,
                             gridspec_kw={'height_ratios': [2, 1, 1]})
    axes[0].plot(epochs, [float(r['training_loss']) for r in rows], color=colors[0],
                 marker='o', markersize=3, label='Training')
    axes[0].plot(epochs, [float(r['validation_loss']) for r in rows], color=colors[1],
                 marker='s', markersize=3, linestyle='--', label='Validation')
    axes[0].set(title='GRU Baseline B: observed training trajectory', ylabel='Mean cross-entropy (unitless)', ylim=(0, None))
    axes[0].legend(frameon=False)
    axes[1].plot(epochs, [float(r['validation_macro_f1']) for r in rows], color=colors[0], marker='o', markersize=3)
    axes[1].set(ylabel='Val Macro-F1 (unitless)', ylim=(0, 1.02))
    axes[2].plot(epochs, [float(r['validation_accuracy']) for r in rows], color=colors[1],
                 marker='s', markersize=3, linestyle='--')
    axes[2].set(ylabel='Val accuracy (unitless)', xlabel='Epoch', ylim=(0, 1.02), xlim=(1, epochs[-1]))
    for ax in axes:
        ax.axvline(best, color='0.4', linestyle=':', linewidth=.9)
        ax.grid(axis='y', alpha=.18)
    axes[0].text(.04, .86, 'Validation-selected epoch ' + str(best), transform=axes[0].transAxes,
                 ha='left', va='top', fontsize=8)
    fig.text(.5, .012, 'Train N=6037 / 17 subjects; val N=1315 / 4 subjects | seed 42 | single run; no CI',
              ha='center', fontsize=7)
    fig.tight_layout(rect=(0, .035, 1, 1))
    export(fig, 'training_curves')
    labels = ['Walking', 'Walking\nupstairs', 'Walking\ndownstairs', 'Sitting', 'Standing', 'Laying']
    fig, ax = plt.subplots(figsize=(6.7, 5.5))
    image = ax.imshow(matrix, cmap='Blues', vmin=0, vmax=int(matrix.max()))
    for i in range(6):
        for j in range(6):
            ax.text(j, i, str(matrix[i, j]), ha='center', va='center', fontsize=9,
                     color='white' if matrix[i, j] > matrix.max() * .55 else '0.15')
    ax.set(xticks=range(6), yticks=range(6), xticklabels=labels, yticklabels=labels,
           xlabel='Predicted activity', ylabel='True activity', title='GRU Baseline B: official test confusion matrix')
    ax.tick_params(axis='both', which='both', length=0)
    fig.colorbar(image, ax=ax, shrink=.85, label='Window count')
    fig.text(.5, .015, 'N=2947 windows / 9 held-out subjects | seed 42 | descriptive counts; no CI', ha='center', fontsize=7)
    fig.tight_layout(rect=(0, .05, 1, 1))
    export(fig, 'confusion_matrix')
    with (report / 'figure_manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
    print('FIGURES PASS: PNG/PDF published; editable SVG retained locally; CSV source hashes recorded')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
