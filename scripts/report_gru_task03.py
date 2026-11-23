"""Verify stored Task 03 output and build the three-seed comparison."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
from statistics import mean, stdev

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import yaml


SEEDS = (42, 43, 44)
LABELS = ('WALKING','WALKING_UPSTAIRS','WALKING_DOWNSTAIRS','SITTING','STANDING','LAYING')
SHORT = ('Walk','Up','Down','Sit','Stand','Lay')


def read(path):
    return json.loads(path.read_text())


def save(path, document):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(document,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_test(predictions, expected_rows, expected_y):
    cm = np.zeros((6,6),dtype=np.int64)
    losses=[]
    with predictions.open(newline='') as f:
        rows=list(csv.DictReader(f))
    require(len(rows)==len(expected_rows)==len(expected_y)==2947, 'Prediction row count differs from the frozen official test set')
    for row,index,truth in zip(rows,expected_rows,expected_y):
        scores=[float(row[f'logit_{i}']) for i in range(6)]
        require(all(map(math.isfinite,scores)), 'Nonfinite logit in saved predictions')
        top=max(range(6),key=scores.__getitem__)
        require((int(row['official_row_1based']),int(row['true_label_0based']),
                int(row['pred_label_0based']))==(index,truth,top), 'Saved prediction row, label, or argmax differs')
        cm[truth,top]+=1
        losses.append(scores[top]-scores[truth]+math.log(math.fsum(math.exp(x-scores[top]) for x in scores)))
    diagonal=cm.diagonal()
    support=cm.sum(1)
    predicted=cm.sum(0)
    precision=np.divide(diagonal,predicted,out=np.zeros(6),where=predicted!=0)
    recall=diagonal/support
    f1=2*diagonal/(support+predicted)
    return dict(accuracy=float(diagonal.sum()/len(rows)),macro_f1=float(f1.mean()),
                loss=math.fsum(losses)/len(rows),f1=f1.tolist(),precision=precision.tolist(),
                recall=recall.tolist(),support=support.tolist(),confusion_matrix=cm.tolist())


def draw_matrix(ax, values, seed):
    cm=np.array(values)
    fractions=cm/cm.sum(1,keepdims=True)
    image=ax.imshow(fractions,vmin=0,vmax=1,cmap='Blues')
    for i,j in np.ndindex(cm.shape):
        ax.text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=8,
                color='white' if fractions[i,j]>.55 else '#173556')
    ax.set(title=f'Seed {seed}',xlabel='Predicted activity',ylabel='True activity',
           xticks=range(6),yticks=range(6),xticklabels=SHORT,yticklabels=SHORT)
    return image


def plot(records, out):
    fig,axes=plt.subplots(1,3,figsize=(12,3.9),layout='constrained')
    for ax,(seed,record) in zip(axes,records.items()):
        im=draw_matrix(ax,record['test']['confusion_matrix'],seed)
    fig.colorbar(im,ax=axes,label='Fraction of true class',shrink=.8)
    fig.savefig(out/'confusion_matrices.png',dpi=165)
    plt.close(fig)

    fig,axes=plt.subplots(2,2,figsize=(10,6.4),layout='constrained')
    for ax,(key,title) in zip(axes.flat,[('training_loss','Training loss'),
            ('validation_loss','Validation loss'),('validation_accuracy','Validation accuracy'),
            ('validation_macro_f1','Validation Macro-F1')]):
        for seed,record in records.items():
            hist=record['history']
            line,=ax.plot([int(r['epoch']) for r in hist],[float(r[key]) for r in hist],label=f'Seed {seed}')
            best=record['result']['best_epoch']
            ax.scatter(best,float(hist[best-1][key]),s=15,color=line.get_color(),zorder=3)
        if key in ('validation_accuracy','validation_macro_f1'):
            ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.set(title=title,xlabel='Epoch')
        ax.grid(alpha=.2)
    axes[0,0].legend()
    fig.savefig(out/'training_curves.png',dpi=165)
    plt.close(fig)

    fig,axes=plt.subplots(1,3,sharey=True,figsize=(13,4.5),layout='constrained')
    y=np.arange(6)
    for ax,key in zip(axes,('precision','recall','f1')):
        for i,(seed,record) in enumerate(records.items()):
            ax.barh(y+(i-1)*.23,record['test'][key],height=.2,label=f'Seed {seed}')
        ax.set(title=key.upper() if key=='f1' else key.title(),xlim=(0,1.04),
               yticks=y,yticklabels=[n.replace('_',' ').title() for n in LABELS])
        ax.xaxis.set_major_formatter(PercentFormatter(1))
    axes[0].invert_yaxis()
    axes[-1].legend()
    fig.savefig(out/'class_metrics.png',dpi=165)
    plt.close(fig)


def main(runs,data,out):
    out.mkdir(parents=True)
    with np.load(data/'test_standardized.npz',allow_pickle=False) as frozen:
        ids=frozen['official_row_1based'].tolist()
        truths=(frozen['y']-1).tolist()
    configs=[]
    records={}
    for seed in SEEDS:
        local=runs/f'seed{seed}'
        result=read(local/'training_result.json')
        test=read(local/'test_metrics.json')
        with (local/'training_history.csv').open(newline='') as f:
            history=list(csv.DictReader(f))
        cfg=yaml.safe_load((local/'config.yaml').read_text())
        require(cfg.pop('seed')==seed, f'Seed mismatch in seed{seed} config')
        configs.append(cfg)
        require(result['status']=='PASS' and result['strict_reloads_equal'], f'Seed {seed} run or checkpoint reload did not pass')
        require(result['test_model_evaluation_passes']==test['test_model_evaluation_passes']==1, f'Seed {seed} test evaluation count is not exactly one')
        require(test['test_artifact_sha256']==sha(data/'test_standardized.npz'), f'Seed {seed} frozen test artifact hash differs')
        require(test['selection_used_test'] is False and result['order_sha256']==[r['order_sha256'] for r in history], f'Seed {seed} test-selection flag or sampler history differs')
        best=max(history,key=lambda r:(float(r['validation_macro_f1']),-float(r['validation_loss'])))
        require(int(best['epoch'])==test['best_epoch']==result['best_epoch'], f'Seed {seed} selected epoch differs from validation history')
        require(len(history)==result['epochs_completed'] and len(set(result['order_sha256']))==len(history), f'Seed {seed} epoch or sampler history is incomplete')
        require(sha(local/'best.pt')==result['best_sha256'] and sha(local/'last.pt')==result['last_sha256'], f'Seed {seed} checkpoint hash differs')
        require((local/'training.log').read_text().rstrip().endswith('Exit code 0'), f'Seed {seed} training log does not record exit code 0')
        independent=compute_test(local/'test_predictions.csv',ids,truths)
        for key in ('accuracy','macro_f1','precision','recall','f1','loss'):
            np.testing.assert_allclose(independent[key],test[key],atol=1e-6 if key=='loss' else 1e-14,rtol=0)
        require(independent['confusion_matrix']==test['confusion_matrix'], f'Seed {seed} confusion matrix differs from independent recomputation')
        save(local/'independent_verification.json',dict(status='PASS',inference_passes=0,recomputed=independent))
        fig,ax=plt.subplots(figsize=(5.2,4.5),layout='constrained')
        fig.colorbar(draw_matrix(ax,test['confusion_matrix'],seed),ax=ax,label='Fraction of true class')
        fig.savefig(local/'confusion_matrix.png',dpi=165)
        plt.close(fig)
        files=sorted(p for p in local.iterdir() if p.is_file())
        with (local/'SHA256SUMS').open('x') as manifest:
            for path in files:
                manifest.write(f'{sha(path)}  {path.name}\n')
        public=out/f'seed{seed}'
        public.mkdir()
        for name in ('config.yaml','training_history.csv','training_result.json','test_metrics.json',
                     'classification_report.csv','independent_verification.json','SHA256SUMS'):
            shutil.copyfile(local/name,public/name)
        records[seed]=dict(result=result,test=test,history=history,independent=independent)
    require(configs[0]==configs[1]==configs[2], 'Task03 configurations differ beyond the seed')
    require(len({r['result']['initial_weight_sha256'] for r in records.values()})==3, 'Task03 seeds do not have distinct initial weights')
    require(len({r['result']['order_sha256'][0] for r in records.values()})==3, 'Task03 seeds do not have distinct first-epoch sample orders')

    fields=('accuracy','macro_f1','loss')
    stats={k:dict(mean=mean(r['test'][k] for r in records.values()),
                  sample_sd=stdev(r['test'][k] for r in records.values())) for k in fields}
    deltas={s:{k:r['test'][k]-records[42]['test'][k] for k in fields} for s,r in records.items()}
    save(out/'summary.json',dict(status='PASS',statistics=stats,deltas_vs_gpu_seed42=deltas,
        seeds={s:{**{k:r['test'][k] for k in fields}, 'best_epoch':r['test']['best_epoch'],
                  'epochs':r['result']['epochs_completed']} for s,r in records.items()}))
    plot(records,out)
    lines=['# GRU GPU 三种子结果','',
           '| Seed | Accuracy | Macro-F1 | Loss | 最佳轮 | 实际轮 |',
           '| ---: | ---: | ---: | ---: | ---: | ---: |']
    for s,r in records.items():
        t,run=r['test'],r['result']
        lines.append(f'| {s} | {t["accuracy"]:.4%} | {t["macro_f1"]:.4%} | {t["loss"]:.6f} | {t["best_epoch"]} | {run["epochs_completed"]} |')
    lines+=['','## 均值、样本标准差与对照','',
            '| 指标 | 均值 | 样本标准差 |', '| --- | ---: | ---: |']
    for label,k in (('Accuracy','accuracy'),('Macro-F1','macro_f1'),('Loss','loss')):
        a,b=stats[k]['mean'],stats[k]['sample_sd']
        lines.append(f'| {label} | {a:.4%} | {b*100:.4f} pp |' if k!='loss' else f'| {label} | {a:.6f} | {b:.6f} |')
    lines+=['','| Seed | Accuracy 差值（pp） | Macro-F1 差值（pp） | Loss 差值 |',
            '| ---: | ---: | ---: | ---: |']
    for s,d in deltas.items():
        lines.append(f'| {s} | {d["accuracy"]*100:+.4f} | {d["macro_f1"]*100:+.4f} | {d["loss"]:+.6f} |')
    lines+=['','差值参照 GPU Seed42。样本标准差使用 n−1。','',
            '## 类别表现','',
            '| Seed | 坐→站 | 站→坐 | 步行类内部错分 | LAYING 正确／537 | 最低 F1 类别 |',
            '| ---: | ---: | ---: | ---: | ---: | --- |']
    for s,r in records.items():
        t=r['test']
        cm=np.array(t['confusion_matrix'])
        j=int(np.argmin(t['f1']))
        walk=cm[:3,:3].sum()-np.trace(cm[:3,:3])
        lines.append(f'| {s} | {cm[3,4]} | {cm[4,3]} | {walk} | {cm[5,5]} | {LABELS[j]}（{t["f1"][j]:.2%}） |')
    f1_ranges=np.ptp([r['test']['f1'] for r in records.values()],axis=0)
    j=int(np.argmax(f1_ranges))
    lines+=['',f'三个种子间 F1 最大跨度出现在 {LABELS[j]}（{100*f1_ranges[j]:.2f} 个百分点）。'
            '所有运行共享同一套数据划分，差异衡量本次初始化与采样顺序的联合变化。'
            '历史 CPU Seed42 采用 Windows 与 PyTorch 2.0.1，本次 GPU 组采用 Linux 与 PyTorch 2.5.1。'
            '历史参考与新组的差异无法归因于单一设备变量。','',
            '[训练曲线](training_curves.png) · [混淆矩阵](confusion_matrices.png) · [逐类指标](class_metrics.png)','']
    (out/'comparison.md').write_text('\n'.join(lines),encoding='utf-8')
    print('PASS: all seeds, logits, metrics, checkpoints and figures verified')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('runs',type=Path)
    p.add_argument('frozen_data',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    main(a.runs,a.frozen_data,a.output)
