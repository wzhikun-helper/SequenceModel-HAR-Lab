"""Three required Transformer plots, generated solely from saved CSV."""
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


def main(run):
    report=ROOT/'reports'/run
    result=json.loads((report/'training_result.json').read_text(encoding='utf-8'))
    if result['status']!='PASS':raise RuntimeError('Training not completed')
    output=ROOT/'outputs/figures'/run
    output.mkdir(parents=True,exist_ok=False)
    with (report/'training_history.csv').open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    with (report/'confusion_matrix.csv').open(encoding='utf-8',newline='') as stream:
        matrix=np.array([[int(v) for v in row[1:]] for row in list(csv.reader(stream))[1:]])
    contracts=dict(training_loss=dict(claim='Observed training/validation loss for the fixed single run',source='training_history.csv'),
                   validation_macro_f1=dict(claim='Validation-only checkpoint selection',source='training_history.csv'),
                   confusion_matrix=dict(claim='Official test errors using only the best checkpoint',source='confusion_matrix.csv'))
    (output/'figure_contracts.json').write_text(json.dumps(contracts,indent=2),encoding='utf-8')
    colors=paper_style()
    epochs=[int(row['epoch']) for row in rows]
    best=result['best_epoch']
    manifest=[]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

    def export(fig,name):
        for path in save(fig,output/name):
            entry=dict(local_path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
                       sha256=sha(path),source_csv=contracts[name]['source'],
                       source_sha256=sha(report/contracts[name]['source']),public_path=None)
            if path.suffix in ['.png','.pdf']:
                target=report/path.name
                if target.exists():raise FileExistsError(target)
                shutil.copyfile(path,target)
                assert sha(path)==sha(target)
                entry['public_path']=target.relative_to(ROOT).as_posix()
            if path.suffix=='.png':
                with Image.open(path) as image:
                    image.load();entry.update(pixels=list(image.size),dpi=list(image.info['dpi']))
            manifest.append(entry)
        plt.close(fig)

    fig,ax=plt.subplots(figsize=(6.6,3.8))
    ax.plot(epochs,[float(r['training_loss']) for r in rows],color=colors[0],marker='o',markersize=3,label='Training')
    ax.plot(epochs,[float(r['validation_loss']) for r in rows],color=colors[1],linestyle='--',marker='s',markersize=3,label='Validation')
    ax.axvline(best,color='0.4',linestyle=':',linewidth=.9)
    ax.text(.04,.86,'Selected epoch '+str(best),transform=ax.transAxes,fontsize=8,va='top')
    ax.set(xlabel='Epoch',ylabel='Mean cross-entropy (unitless)',title='Transformer C: observed loss trajectory',
           xlim=(1,epochs[-1]),ylim=(0,None))
    ax.legend(frameon=False,loc='upper right');ax.grid(axis='y',alpha=.18)
    fig.text(.5,.015,'Train N=6037; validation N=1315 | seed 42 | single run; no uncertainty interval',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.05,1,1));export(fig,'training_loss')
    fig,ax=plt.subplots(figsize=(6.6,3.8))
    f1=[float(r['validation_macro_f1']) for r in rows]
    ax.plot(epochs,f1,color=colors[0],marker='o',markersize=3)
    ax.axvline(best,color='0.4',linestyle=':',linewidth=.9)
    ax.scatter([best],[f1[best-1]],facecolors='white',edgecolors=colors[1],s=40,zorder=4)
    ax.text(.04,.12,'Selected epoch '+str(best)+'; F1='+format(f1[best-1],'.4f'),transform=ax.transAxes,fontsize=8)
    ax.set(xlabel='Epoch',ylabel='Validation Macro-F1 (unitless)',title='Transformer C: validation-only selection',
           xlim=(1,epochs[-1]),ylim=(0,1.02))
    ax.grid(axis='y',alpha=.18)
    fig.text(.5,.015,'N=1315 windows / 4 subjects | seed 42 | single run; no uncertainty interval',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.05,1,1));export(fig,'validation_macro_f1')
    labels=['Walking','Walking\nupstairs','Walking\ndownstairs','Sitting','Standing','Laying']
    fig,ax=plt.subplots(figsize=(6.7,5.5))
    image=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=int(matrix.max()))
    for i in range(6):
        for j in range(6):
            ax.text(j,i,str(matrix[i,j]),ha='center',va='center',fontsize=9,
                    color='white' if matrix[i,j]>matrix.max()*.55 else '0.15')
    ax.set(xticks=range(6),yticks=range(6),xticklabels=labels,yticklabels=labels,
           xlabel='Predicted activity',ylabel='True activity',title='Transformer C: official test confusion matrix')
    ax.tick_params(axis='both',which='both',length=0)
    fig.colorbar(image,ax=ax,shrink=.85,label='Window count')
    fig.text(.5,.015,'N=2947 windows / 9 held-out subjects | seed 42 | descriptive counts; no CI',ha='center',fontsize=7)
    fig.tight_layout(rect=(0,.05,1,1));export(fig,'confusion_matrix')
    with (report/'figure_manifest.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,indent=2)
    print('FIGURES PASS: saved CSV to 3 PNG/PDF plots plus editable local SVG; hashes/dpi recorded')


if __name__=='__main__':main(sys.argv[1])
