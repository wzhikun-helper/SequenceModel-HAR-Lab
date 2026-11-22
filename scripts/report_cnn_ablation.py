"""Aggregate the nine frozen results and render the required research plots."""
import csv
import itertools
from statistics import mean, stdev

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from audit_cnn_ablation import AUDIT, OLD, ROOT, SUITE
from day01_figure_style import paper_style, save
from train_cnn_ablation import save_csv
from train_cnn_baseline_a import read, sha, write
from verify_cnn_ablation import rows

GROUPS = 'ABC'
SEEDS = [42, 43, 44]
LOGS = ROOT / 'logs/cnn_ablation_20261122'


def collect():
    summary, history, categories, matrices, commands = [], {}, [], {}, []
    audit = read(AUDIT / 'evidence.json')
    for seed, group in itertools.product(SEEDS, GROUPS):
        assert read(SUITE / f'independent_seed{seed}.json')['status'] == 'PASS'
        reused = (seed, group) == (42, 'A')
        folder = OLD if reused else SUITE / f'cnn_ablation_{group}_seed{seed}_20261122_run01'
        timing = audit['historical_command'] if reused else read(LOGS / (folder.name + '.json'))
        result, test = (read(folder / name) for name in ['training_result.json', 'test_metrics.json'])
        assert result['status'] == 'PASS' and timing['exit_code'] == 0
        summary.append(dict(seed=seed, group=group, reused=reused, accuracy=test['accuracy'],
                            macro_f1=test['macro_f1'], loss=test['loss'], parameters=27270 if reused else result['parameters'],
                            best=result['best_epoch'], epochs=result['epochs_completed'],
                            wall_seconds=timing['elapsed_seconds'], loop_seconds=result.get('epoch_loop_seconds'),
                            run=folder.relative_to(ROOT).as_posix()))
        history[group, seed] = rows(folder, 'training_history.csv')
        matrices[group, seed] = np.array(test['confusion_matrix'])
        categories.extend([seed, group, name, test['precision'][i], test['recall'][i],
                           test['f1'][i], test['support'][i]] for i, name in enumerate(test['activity_names']))
        commands.append(dict(timing, reused=reused))
    return summary, history, categories, matrices, commands


def plot(summary, history, matrices, pairs):
    paper_style()
    colors = ['#0072B2', '#D55E00', '#009E73']
    output = ROOT / 'outputs/figures/cnn_ablation_20261122'
    output.mkdir(parents=True, exist_ok=False)
    artifacts = []

    def export(fig, name, sources):
        for path in save(fig, output / name):
            item = dict(local=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size,
                        sources={p.relative_to(ROOT).as_posix(): sha(p) for p in sources})
            if path.suffix == '.png':
                public = SUITE / path.name
                with public.open('xb') as stream:
                    stream.write(path.read_bytes())
                with Image.open(public) as png:
                    png.load()
                    item.update(public=public.name, pixels=list(png.size), dpi=list(png.info['dpi']))
            artifacts.append(item)
        plt.close(fig)

    summary_csv = SUITE / 'results.csv'
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    for index, group in enumerate(GROUPS):
        values = [row['macro_f1']*100 for row in summary if row['group'] == group]
        ax.scatter([index-.12, index, index+.12], values, color=colors[index], zorder=3)
        ax.errorbar(index+.24, mean(values), yerr=stdev(values), fmt='D', color='0.2', capsize=4)
    ax.set(xticks=range(3), xticklabels=['A  CNN', 'B  CNN + SE', 'C  CNN + MLP'],
           ylabel='Test Macro-F1 (%)', title='Single fixed subject split')
    ax.grid(axis='y', alpha=.2)
    fig.text(.5,.02,'Dots: seeds 42, 43, 44 (left to right). Diamonds: mean +/- sample SD. Test N=2947.',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.06,1,1))
    export(fig,'macro_f1_comparison',[summary_csv])

    fig, ax = plt.subplots(figsize=(6.5,3.6))
    ax.plot(SEEDS,[row[1] for row in pairs],'o-',color=colors[0],label='SE - CNN')
    ax.plot(SEEDS,[row[2] for row in pairs],'s--',color=colors[1],label='SE - MLP')
    ax.axhline(0,color='0.35',linewidth=.8)
    ax.set(xticks=SEEDS,xlabel='Training seed',ylabel='Macro-F1 difference (percentage points)',
           title='Paired test differences')
    ax.legend(frameon=False)
    ax.grid(axis='y',alpha=.2)
    fig.text(.5,.02,'Three paired seeds, one fixed split, 2947 test windows.',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.06,1,1))
    export(fig,'paired_differences',[SUITE/'paired.csv'])

    fig, axes = plt.subplots(3,1,figsize=(7,7.6),sharex=True)
    for ax, seed in zip(axes,SEEDS):
        for index,group in enumerate(GROUPS):
            curve = history[group,seed]
            epochs = [int(item['epoch']) for item in curve]
            for key,style in [('training_loss','-'),('validation_loss','--')]:
                ax.plot(epochs,[float(item[key]) for item in curve],style,color=colors[index],
                        label=group+' '+key.split('_')[0])
        ax.set_title(f'Seed {seed}',loc='left')
        ax.set_ylabel('Cross-entropy')
        ax.grid(axis='y',alpha=.18)
    axes[0].legend(frameon=False,ncol=3,fontsize=7)
    axes[-1].set_xlabel('Epoch')
    fig.text(.5,.012,'Train N=6037; validation N=1315. Solid: training. Dashed: validation.',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.035,1,1))
    export(fig,'loss_curves',[ROOT/item['run']/'training_history.csv' for item in summary])

    fig, axes = plt.subplots(3,3,figsize=(8,8),sharex=True,sharey=True,layout='constrained')
    for i, seed in enumerate(SEEDS):
        for j, group in enumerate(GROUPS):
            ax = axes[i,j]
            matrix = matrices[group,seed]
            image = ax.imshow(matrix,cmap='Blues',vmin=0,vmax=max(m.max() for m in matrices.values()))
            ax.set(title=f'{group} / seed {seed}',xticks=range(6),yticks=range(6),
                   xticklabels=range(1,7),yticklabels=range(1,7))
            for y,x in itertools.product(range(6),repeat=2):
                ax.text(x,y,str(matrix[y,x]),ha='center',va='center',fontsize=7,
                        color='white' if matrix[y,x]>300 else 'black')
    fig.colorbar(image,ax=axes,shrink=.7,label='Window count')
    fig.supxlabel('Predicted official label')
    fig.supylabel('True official label')
    fig.suptitle('Official test confusion matrices (N=2947 per run)')
    export(fig,'confusion_matrices',[ROOT/item['run']/'confusion_matrix.csv' for item in summary])

    fig, ax = plt.subplots(figsize=(6,3.5))
    values = [next(row['parameters'] for row in summary if row['group']==group) for group in GROUPS]
    bars = ax.bar(list(GROUPS), values,color=colors)
    ax.bar_label(bars,labels=[f'{value:,}' for value in values],padding=4)
    ax.set(ylim=(0,37000),xlabel='Model group',ylabel='Trainable parameters',title='Equal capacity for SE and residual MLP')
    fig.tight_layout()
    export(fig,'parameter_counts',[summary_csv])
    write(SUITE/'figure_manifest.json',artifacts)


def main():
    summary, history, categories, matrices, commands = collect()
    save_csv(SUITE/'results.csv',list(summary[0]),[list(row.values()) for row in summary])
    save_csv(SUITE/'per_class.csv',['seed','group','activity','precision','recall','f1','support'],categories)
    lookup = {(row['group'],row['seed']): row['macro_f1'] for row in summary}
    pairs = [[seed, (lookup['B',seed]-lookup['A',seed])*100,
              (lookup['B',seed]-lookup['C',seed])*100] for seed in SEEDS]
    save_csv(SUITE/'paired.csv',['seed','B_minus_A_percentage_points','B_minus_C_percentage_points'],pairs)
    stats = {}
    for group in GROUPS:
        values = [lookup[group,seed] for seed in SEEDS]
        stats[group] = dict(mean=mean(values),sample_sd=stdev(values))
    stats['paired'] = pairs
    write(SUITE/'statistics.json',stats)
    plot(summary, history, matrices, pairs)
    write(SUITE/'run_commands.json',commands)
    print('Nine runs, paired statistics and five figures archived.')


if __name__ == '__main__':
    main()
