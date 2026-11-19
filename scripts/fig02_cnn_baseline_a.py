"""Reproducible Baseline A figures from saved history/metrics, never model execution."""
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

ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main(run):
    if not run.replace('_','').isalnum(): raise ValueError('Unsafe run ID')
    report=ROOT/'reports'/run
    result=json.loads((report/'training_result.json').read_text(encoding='utf-8'))
    if result['status']!='PASS':raise RuntimeError('Training incomplete')
    output=ROOT/'outputs/figures'/run; output.mkdir(parents=True,exist_ok=False)
    with (report/'training_history.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    epochs=np.array([int(r['epoch']) for r in rows])
    train=np.array([float(r['training_loss']) for r in rows])
    val=np.array([float(r['validation_loss']) for r in rows])
    f1=np.array([float(r['validation_macro_f1']) for r in rows])
    best=result['best_epoch']
    with (report/'confusion_matrix.csv').open(encoding='utf-8',newline='') as f:
        csvrows=list(csv.reader(f)); matrix=np.array([[int(v) for v in row[1:]] for row in csvrows[1:]])
    contracts={
      'train_val_loss':dict(core_claim='Observed train and validation loss trajectory for the single approved run.',
           hero='train/validation loss vs epoch',source='training_history.csv',N='6037 train / 1315 validation windows'),
      'validation_macro_f1':dict(core_claim='Checkpoint selection uses validation Macro-F1 with loss only on exact ties.',
           hero='validation Macro-F1 vs epoch; selected epoch marked',source='training_history.csv',N='1315 validation windows / 4 subjects'),
      'confusion_matrix':dict(core_claim='Final best-checkpoint test errors by true and predicted activity.',
           hero='six-class confusion matrix',source='confusion_matrix.csv',N='2947 test windows / 9 subjects')}
    (output/'figure_contracts.json').write_text(json.dumps(contracts,indent=2),encoding='utf-8')
    palette=paper_style(); manifest=[]
    def export(fig,name):
        for p in save(fig,output/name):
            target=report/p.name
            if target.exists():raise FileExistsError(target)
            shutil.copyfile(p,target)
            if sha(p)!=sha(target):raise RuntimeError('Figure copy differs')
            entry=dict(path=target.relative_to(ROOT).as_posix(),local_original=p.relative_to(ROOT).as_posix(),
                       sha256=sha(target),bytes=target.stat().st_size,
                       source_csv=contracts[name]['source'],source_sha256=sha(report/contracts[name]['source']))
            if p.suffix=='.png':
                with Image.open(p) as im:
                    im.load();entry.update(pixels=list(im.size),dpi=list(im.info['dpi']))
            manifest.append(entry)
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.5,3.6))
    ax.plot(epochs,train,color=palette[0],marker='o',markersize=3,label='Training')
    ax.plot(epochs,val,color=palette[1],linestyle='--',marker='s',markersize=3,label='Validation')
    ax.axvline(best,color='0.4',linestyle=':',linewidth=.9,label='Selected epoch '+str(best))
    ax.set(xlabel='Epoch',ylabel='Mean cross-entropy loss (unitless)',title='Baseline A: observed loss trajectory',
           xlim=(1,int(epochs[-1])),ylim=(0,max(train.max(),val.max())*1.12))
    ax.legend(frameon=False); ax.grid(axis='y',alpha=.18)
    fig.text(.5,.015,'Train N=6037; validation N=1315 | seed 42 | one run; no uncertainty interval',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.05,1,1));export(fig,'train_val_loss')
    fig,ax=plt.subplots(figsize=(6.5,3.6))
    ax.plot(epochs,f1,color=palette[0],marker='o',markersize=3)
    ax.axvline(best,color='0.4',linestyle=':',linewidth=.9)
    ax.scatter([best],[f1[best-1]],s=40,facecolors='white',edgecolors=palette[1],zorder=4)
    ax.annotate('Selected epoch '+str(best)+'; F1='+format(f1[best-1],'.4f'),xy=(best,f1[best-1]),
                xytext=(.04,.12),textcoords='axes fraction',fontsize=8,
                arrowprops=dict(arrowstyle='-',color='0.4',lw=.8))
    ax.set(xlabel='Epoch',ylabel='Validation Macro-F1 (unitless)',title='Validation-only checkpoint selection',
           ylim=(0,1.02),xlim=(1,int(epochs[-1])))
    ax.grid(axis='y',alpha=.18)
    fig.text(.5,.015,'N=1315 windows / 4 subjects | seed 42 | one run; no uncertainty interval',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.05,1,1));export(fig,'validation_macro_f1')
    labels=['Walking','Walking\nupstairs','Walking\ndownstairs','Sitting','Standing','Laying']
    fig,ax=plt.subplots(figsize=(6.7,5.5))
    im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=int(matrix.max()))
    for i in range(6):
        for j in range(6):
            ax.text(j,i,str(matrix[i,j]),ha='center',va='center',fontsize=9,
                    color='white' if matrix[i,j]>matrix.max()*.55 else '0.15')
    ax.set(xticks=range(6),yticks=range(6),xticklabels=labels,yticklabels=labels,
           xlabel='Predicted activity',ylabel='True activity',title='Baseline A: official test confusion matrix')
    ax.tick_params(axis='both',which='both',length=0)
    fig.colorbar(im,ax=ax,shrink=.85,label='Window count')
    fig.text(.5,.015,'N=2947 windows / 9 held-out subjects | seed 42 | descriptive counts; no uncertainty interval',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.05,1,1));export(fig,'confusion_matrix')
    with (report/'figure_manifest.json').open('x',encoding='utf-8') as f:json.dump(manifest,f,indent=2)
    with (report/'figure_quality.md').open('x',encoding='utf-8') as f:
        f.write('# Figure quality and scope\n\n'
          'Backend: matplotlib; shared existing project paper_style; PNG 300 dpi, editable PDF/SVG. '
          'All three plots load saved CSV; no inline simulated results.\n\n'
          '- Depth: selected epoch is explicitly marked; confusion rows/columns and count scale are stated.\n'
          '- Elegance: one claim per figure, no decorative panels; loss series have distinct markers and line styles.\n'
          '- Integrity: N and seed appear on every plot; one run has no between-seed uncertainty interval. '
          'Window dependence prevents interpreting N as independent participant replicates.\n'
          '- Legibility: common typography, colorblind-safe line colors, grayscale-separable styles, '
          'monotone Blues confusion map with numerical labels and editable vector text.\n\n'
          'Icarus bundled paperfig and scripts/critique.py are absent in the installed skill. '
          'Mechanical gate is unavailable, not reported as passed; local image rendering/content checks and manual review used.\n')
    print('FIGURES PASS: 3 plots x PNG/PDF/SVG; source hashes, PNG dimensions/dpi recorded')
if __name__=='__main__':main(sys.argv[1])
