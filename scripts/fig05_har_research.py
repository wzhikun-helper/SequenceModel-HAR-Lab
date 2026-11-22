"""Plot archived UCI HAR model comparisons and within-seed ablation differences."""
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from day01_figure_style import paper_style, save


def read(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def plot(output):
    blue, orange = paper_style()
    models = read(output / 'baselines.csv')
    pairs = read(output / 'paired.csv')
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.25, 2.55), layout='constrained')
    values = [float(row['macro_f1']) * 100 for row in models]
    positions = list(range(len(models)))
    left.scatter(values, positions, marker='o', color=blue, zorder=3)
    left.set_yticks(positions, [row['model'] for row in models])
    left.invert_yaxis()
    left.set_xlim(min(values)-0.5, max(values)+1)
    for y, value in zip(positions, values):
        left.annotate(f'{value:.2f}', (value, y), xytext=(5, 0), textcoords='offset points', va='center', fontsize=8)
    left.set_xlabel('Test Macro-F1 (%)')
    left.set_title('a  Model comparison (Seed 42)', loc='left', fontweight='bold')
    left.grid(axis='x', color='0.88')

    x = list(range(len(pairs)))
    right.axhline(0, color='0.55', linewidth=0.8)
    right.scatter([i-.12 for i in x], [float(r['B_minus_A_percentage_points']) for r in pairs],
                  color=blue, marker='o', label='SE - baseline')
    right.scatter([i+.12 for i in x], [float(r['B_minus_C_percentage_points']) for r in pairs],
                  color=orange, marker='^', label='SE - residual MLP')
    right.set_ylim(-1.6, 3.6)
    right.set_xticks(x, [r['seed'] for r in pairs])
    right.set_ylabel('Test Macro-F1 difference (pp)')
    right.set_xlabel('Seed')
    right.set_title('b  Paired CNN ablation', loc='left', fontweight='bold')
    right.legend(loc='upper right', frameon=False, fontsize=8)
    right.text(0.02, 0.03, 'n = 3 pairs; 2,947 test windows per run', transform=right.transAxes, fontsize=7.5)
    paths = save(fig, output / 'results_figure')
    plt.close(fig)
    return paths
