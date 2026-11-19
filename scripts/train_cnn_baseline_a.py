"""Three explicit stages: read-only data audit, disposable preflight, one seed42 training."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
import traceback

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from har_lab.cnn import parameter_calculation, targets_from_official
from har_lab.cnn_baseline_a import CNNBaselineA
from har_contracts import (CHANNELS, NAMES, validate_window_shape, validate_channel_order,
                          validate_labels, validate_scaler_provenance)
from cnn_metrics import classification_metrics, improves

SOURCE = 'day01_data_20261026_run02'
DATA = ROOT / 'data/processed' / (SOURCE + '_audit02')
BASE_CONFIG = dict(seed=42, batch_size=64, optimizer='Adam', learning_rate=0.001,
                   max_epochs=30, early_stopping_patience=8, drop_last=False,
                   loss='CrossEntropyLoss', selection_metric='validation Macro-F1',
                   tie_breaker='validation Loss', train_shuffle=True, num_workers=0,
                   adam_betas=[0.9, 0.999], adam_eps=1e-8, weight_decay=0,
                   scheduler=None, class_weights=None, augmentation=None,
                   input_shape=[9,128], conv_channels=[9,64,128], kernel_size=3,
                   stride=1, padding=1, dilation=1, bias=True, maxpool_size=2,
                   activation='ReLU', pooling='time mean', classes=6,
                   source_artifact=SOURCE + '_audit02', torch_threads=2,
                   improvement_rule='strictly higher float64 macro-F1; exactly equal F1 then strictly lower loss',
                   early_stop_rule='8 consecutive validation epochs without selection improvement',
                   label_mapping={str(i): i-1 for i in range(1,7)})


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def require(ok, message):
    if not ok: raise RuntimeError(message)


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def seed_all(config):
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(config['seed'])
    torch.set_num_threads(config['torch_threads'])
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)


def artifact(split):
    with np.load(DATA / (split + '_standardized.npz'), allow_pickle=False) as d:
        X, y = d['X'].copy(), d['y'].copy()
    return TensorDataset(torch.from_numpy(X).permute(0,2,1).contiguous(),
                         targets_from_official(torch.from_numpy(y).long()))


def loader(split, config):
    generator = torch.Generator().manual_seed(config['seed'])
    return DataLoader(artifact(split), batch_size=config['batch_size'], shuffle=split=='train',
                      drop_last=False, num_workers=0, generator=generator)


def evaluate(model, batches, device):
    model.eval()
    truth, predicted, all_logits = [], [], []
    total, n = 0.0, 0
    with torch.no_grad():
        for X, y in batches:
            out = model(X.to(device))
            require(torch.isfinite(out).all().item(), 'Nonfinite evaluation logits')
            total += float(nn.functional.cross_entropy(out, y.to(device), reduction='sum'))
            n += len(y)
            truth.extend(y.tolist()); predicted.extend(out.argmax(1).cpu().tolist())
            all_logits.append(out.cpu())
    metrics = classification_metrics(np.array(truth), np.array(predicted))
    metrics['loss'] = total / n
    return metrics, torch.cat(all_logits), truth, predicted


def audit(report):
    report.mkdir(parents=True, exist_ok=False)
    require(read(ROOT/'reports'/SOURCE/'independent_verification.json')['status']=='PASS', 'Day01 not verified')
    meta = read(DATA/'splits/split_metadata.json'); scaler = read(DATA/'scaler_train_only.json')
    require(meta == read(ROOT/'docs/day01/split_metadata.json'), 'Split differs from published protocol')
    require(scaler == read(ROOT/'docs/day01/standardization_train_only.json'), 'Scaler differs from published protocol')
    validate_scaler_provenance(scaler, meta)
    require(sha(DATA/'splits/sample_manifest.csv') == meta['sample_manifest_sha256'], 'Manifest hash mismatch')
    baseline = read(ROOT/'reports'/SOURCE/'audit02/original_files_before.json')
    require(len(baseline)==29 and all(sha(ROOT/p)==h for p,h in baseline.items()), 'Raw-file hash mismatch')
    rawroot = ROOT / read(ROOT/'reports'/SOURCE/'download_provenance.json')['dataset_root']
    source = {}
    for part in ['train','test']:
        source[part] = dict(y=np.loadtxt(rawroot/part/('y_'+part+'.txt'),dtype=np.int64),
                            subject=np.loadtxt(rawroot/part/('subject_'+part+'.txt'),dtype=np.int64))
    summary = {}
    for split, n in [('train',6037),('validation',1315),('test',2947)]:
        with np.load(DATA/(split+'_standardized.npz'), allow_pickle=False) as d:
            validate_window_shape(d['X'].shape, n); validate_channel_order(d['channels'].tolist())
            validate_labels(d['y'], require_all=True)
            require(d['X'].dtype == np.float32 and np.isfinite(d['X']).all(), 'Invalid input values')
            require(d['y'].shape == d['subject'].shape == d['official_row_1based'].shape == (n,), 'Metadata shape')
            require(sorted(set(d['subject'].tolist())) == meta['splits'][split]['subjects'], 'Subject mismatch')
            part = 'test' if split=='test' else 'train'; rows = d['official_row_1based'] - 1
            require(((rows>=0)&(rows<len(source[part]['y']))).all(), 'Invalid source row')
            require(np.array_equal(d['y'],source[part]['y'][rows]) and
                    np.array_equal(d['subject'],source[part]['subject'][rows]), 'Row label/subject mismatch')
            if split=='test': require(np.array_equal(rows,np.arange(n)), 'Official test order changed')
            require({NAMES[i]:int((d['y']==i).sum()) for i in range(1,7)}==meta['splits'][split]['class_counts'],
                    'Class counts mismatch')
            summary[split] = dict(n=n, subjects=meta['splits'][split]['subjects'],
                                  class_counts=meta['splits'][split]['class_counts'])
    # Read-only current-value verification, reusing saved moments, never fitting.
    for part in ['train','test']:
        splits = ['train','validation'] if part=='train' else ['test']
        for c, channel in enumerate(CHANNELS):
            raw = np.loadtxt(rawroot/part/'Inertial Signals'/(channel+'_'+part+'.txt'),dtype=np.float64)
            for split in splits:
                with np.load(DATA/(split+'_standardized.npz'),allow_pickle=False) as d:
                    expected=((raw[d['official_row_1based']-1]-scaler['mean'][c])/scaler['std'][c]).astype(np.float32)
                    require(np.array_equal(d['X'][:,:,c], expected), 'Saved standardization differs: '+split+channel)
    files = [p for p in DATA.rglob('*') if p.is_file()] + [ROOT/p for p in baseline]
    files += [ROOT/'.gitignore']
    protected = {relative(p):sha(p) for p in files}
    env = dict(python=sys.version, interpreter=sys.executable, platform=platform.platform(),
               pytorch=torch.__version__, numpy=np.__version__, cuda_build=torch.version.cuda,
               cuda_available=torch.cuda.is_available(), device='cuda:0' if torch.cuda.is_available() else 'cpu')
    if torch.cuda.is_available(): env['gpu_name']=torch.cuda.get_device_name(0)
    write(report/'data_audit.json', dict(status='PASS', splits=summary, channels=CHANNELS,
          scaler_source='final training subjects only, saved Day01 parameters; no fitting',
          current_all_values_match_raw=True, protected_sha256=protected,
          test_access_scope='Read-only integrity/label audit; no model predictions or performance metrics'))
    config=dict(BASE_CONFIG, device=env['device'])
    write(report/'config.json',config); write(report/'environment.json',env)
    tracked = subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    write(report/'source_provenance.json', dict(base_head=subprocess.check_output(
          ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          tracked_before={p:sha(ROOT/p) for p in tracked},
          executed_sources={p:sha(ROOT/p) for p in ['scripts/train_cnn_baseline_a.py','scripts/cnn_metrics.py',
                            'src/har_lab/cnn_baseline_a.py','src/har_lab/cnn.py','scripts/har_contracts.py']},
          config_sha256=sha(report/'config.json')))
    print('AUDIT PASS: fixed 6037/1315/2947, all saved values match raw+saved train scaler',flush=True)


def preflight(report, checkpoint_dir):
    config=read(report/'config.json'); seed_all(config); device=torch.device(config['device'])
    model=CNNBaselineA().to(device); shapes={}
    handles=[]
    for name in ['conv1','relu1','maxpool','conv2','relu2','pool','flatten','classifier']:
        def hook(m, i, o, name=name): shapes[name]=list(o.shape)
        handles.append(getattr(model,name).register_forward_hook(hook))
    optim=torch.optim.Adam(model.parameters(),lr=config['learning_rate'])
    initial={k:v.clone() for k,v in model.state_dict().items()}
    batch_losses=[]; grad_checks=[]
    for batch_index,(X,y) in enumerate(loader('train',config)):
        X,y=X.to(device),y.to(device)
        require(list(X.shape)==[64,9,128] and y.dtype==torch.int64 and ((y>=0)&(y<6)).all(), 'Batch contract')
        optim.zero_grad(); out=model(X); require(list(out.shape)==[64,6], 'Logits contract')
        loss=nn.functional.cross_entropy(out,y); require(torch.isfinite(loss).item(), 'Nonfinite preflight loss')
        loss.backward()
        checks={}
        for name,p in model.named_parameters():
            require(p.grad is not None and torch.isfinite(p.grad).all().item() and torch.count_nonzero(p.grad)>0,
                    'Invalid preflight gradient: '+name)
            checks[name]=dict(finite=True,l2=float(p.grad.norm()),nonzero=int(torch.count_nonzero(p.grad)))
        optim.step(); batch_losses.append(float(loss.detach())); grad_checks.append(checks)
        if batch_index==1: break
    for h in handles: h.remove()
    updated={k:bool(not torch.equal(initial[k],v)) for k,v in model.state_dict().items()}
    require(all(updated.values()), 'Optimizer did not update all parameter tensors')
    checkpoint_dir.mkdir(parents=True,exist_ok=False)
    p=checkpoint_dir/'preflight.pt'
    with p.open('xb') as f: torch.save(model.state_dict(),f)
    other=CNNBaselineA().to(device); other.load_state_dict(torch.load(p,map_location=device,weights_only=True),strict=True)
    model.eval(); other.eval()
    with torch.no_grad(): a,b=model(X),other(X)
    require(torch.equal(a,b), 'Preflight reload output differs')
    calc=parameter_calculation(); require(sum(p.numel() for p in model.parameters())==calc['total'], 'Parameter count')
    expected=dict(conv1=[64,64,128],relu1=[64,64,128],maxpool=[64,64,64],conv2=[64,128,64],
                  relu2=[64,128,64],pool=[64,128,1],flatten=[64,128],classifier=[64,6])
    require(shapes==expected, 'Layer shapes mismatch')
    write(report/'model_summary.json',dict(architecture=str(model),input_shape=[64,9,128],layer_shapes=shapes,
          parameter_calculation=calc,actual_parameters=sum(p.numel() for p in model.parameters()),
          maxpool_parameters=0, difference_from_minimal='MaxPool1d(2) after first ReLU; old model unchanged'))
    write(report/'preflight.json',dict(status='PASS',batches=2,losses=batch_losses,gradients=grad_checks,
          parameter_tensors_updated=updated,reload_max_abs_difference=float((a-b).abs().max()),
          checkpoint_path=relative(p),checkpoint_bytes=p.stat().st_size,checkpoint_sha256=sha(p),
          formal_run_reinitializes_model_optimizer_and_all_rngs=True))
    print('PREFLIGHT PASS: 2 real batches, finite nonzero gradients, Adam updates, exact reload',flush=True)


def train(report, checkpoint_dir):
    require(read(report/'preflight.json')['status']=='PASS', 'Preflight missing or failed')
    config=read(report/'config.json'); provenance=read(report/'source_provenance.json')
    require(sha(report/'config.json')==provenance['config_sha256'], 'Configuration changed after audit')
    for p,h in provenance['executed_sources'].items(): require(sha(ROOT/p)==h, 'Executed source changed')
    seed_all(config); device=torch.device(config['device'])
    model=CNNBaselineA().to(device)
    optim=torch.optim.Adam(model.parameters(),lr=config['learning_rate'],
                           betas=tuple(config['adam_betas']),eps=config['adam_eps'],weight_decay=0)
    train_loader,val_loader=loader('train',config),loader('validation',config)
    history=[]; best_f1,best_loss=-1.0,float('inf'); best_epoch=0; stale=0; best_path=None
    probe=next(iter(val_loader))[0][:8].to(device)
    headers=['epoch','training_loss','validation_loss','validation_accuracy','validation_macro_f1',
             'learning_rate','best_epoch','updated_best','early_stopping_count','train_samples','train_batches']
    started=time.perf_counter()
    with (report/'training_history.csv').open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=headers); writer.writeheader(); f.flush()
        for epoch in range(1,config['max_epochs']+1):
            model.train(); total=0.0; n=0; batches=0
            for X,y in train_loader:
                X,y=X.to(device),y.to(device); optim.zero_grad(); out=model(X)
                loss=nn.functional.cross_entropy(out,y)
                require(torch.isfinite(loss).item(), 'Nonfinite training loss')
                loss.backward()
                require(all(p.grad is not None and torch.isfinite(p.grad).all().item() for p in model.parameters()),
                        'Nonfinite/missing training gradients')
                optim.step(); total+=float(loss.detach())*len(y); n+=len(y); batches+=1
            require(n==6037 and batches==95, 'Training did not consume all windows')
            val,_,_,_=evaluate(model,val_loader,device)
            update=improves(val['macro_f1'],val['loss'],best_f1,best_loss)
            if update:
                best_f1,best_loss,best_epoch=val['macro_f1'],val['loss'],epoch; stale=0
                best_path=checkpoint_dir/('epoch_%03d.pt'%epoch)
                with torch.no_grad(): reference=model(probe).cpu()
                with best_path.open('xb') as ck:
                    torch.save(dict(state_dict=model.state_dict(),epoch=epoch,config_sha256=provenance['config_sha256'],
                                    validation_logits=reference,seed=42),ck)
            else: stale+=1
            row=dict(epoch=epoch,training_loss=total/n,validation_loss=val['loss'],
                     validation_accuracy=val['accuracy'],validation_macro_f1=val['macro_f1'],
                     learning_rate=optim.param_groups[0]['lr'],best_epoch=best_epoch,updated_best=update,
                     early_stopping_count=stale,train_samples=n,train_batches=batches)
            history.append(row); writer.writerow(row); f.flush()
            print(json.dumps(row),flush=True)
            if stale>=config['early_stopping_patience']: break
    saved=torch.load(best_path,map_location=device,weights_only=True)
    best=CNNBaselineA().to(device); best.load_state_dict(saved['state_dict'],strict=True); best.eval()
    with torch.no_grad(): reloaded=best(probe).cpu()
    require(torch.equal(reloaded,saved['validation_logits'].cpu()),'Best checkpoint reload mismatch')
    # Full validation replay of the best checkpoint must reproduce its saved selection metrics.
    val,_,_,_=evaluate(best,val_loader,device)
    require(val['macro_f1']==best_f1 and val['loss']==best_loss, 'Best validation replay mismatch')
    write(report/'checkpoint_reload_verification.json',dict(status='PASS',best_epoch=best_epoch,
          config_sha256=provenance['config_sha256'],strict_load=True,weights_only=True,
          max_abs_difference=float((reloaded-saved['validation_logits'].cpu()).abs().max()),
          validation_replay_exact=True,probe='first 8 fixed validation rows, eval/no_grad',
          checkpoint_path=relative(best_path),bytes=best_path.stat().st_size,sha256=sha(best_path)))
    # The only model evaluation on the official test split; never called during fitting/selection.
    test,_,truth,pred=evaluate(best,loader('test',config),device)
    write(report/'test_metrics.json',dict(test,activity_names=[NAMES[i] for i in range(1,7)],
          best_epoch=best_epoch,test_model_evaluation_passes=1,
          selection_used_test=False,checkpoint_sha256=sha(best_path)))
    with (report/'confusion_matrix.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['true_activity']+[NAMES[i] for i in range(1,7)])
        for i,row in enumerate(test['confusion_matrix']): w.writerow([NAMES[i+1]]+row)
    with (report/'per_class_metrics.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['official_label','activity','precision','recall','f1','support'])
        for i in range(6): w.writerow([i+1,NAMES[i+1],test['precision'][i],test['recall'][i],test['f1'][i],test['support'][i]])
    with (report/'test_predictions.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['official_test_row_1based','true_label_0based','pred_label_0based'])
        for i,(y,p) in enumerate(zip(truth,pred)): w.writerow([i+1,y,p])
    old=read(report/'data_audit.json')['protected_sha256']
    require(all(sha(ROOT/p)==h for p,h in old.items()), 'Input or gitignore changed')
    write(report/'training_result.json',dict(status='PASS',best_epoch=best_epoch,epochs_completed=len(history),
          stopped_early=stale>=config['early_stopping_patience'],final_stale_count=stale,
          stop_reason='patience' if stale>=config['early_stopping_patience'] else 'max_epochs',
          best_validation=val,seconds=time.perf_counter()-started,seed=42,
          optimizer_steps=95*len(history),test_evaluation_passes=1,input_hashes_unchanged=True))
    print('FINAL '+json.dumps(dict(best_epoch=best_epoch,epochs=len(history),
                                   test_accuracy=test['accuracy'],test_macro_f1=test['macro_f1'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('stage',choices=['audit','preflight','train'])
    p.add_argument('run_id'); args=p.parse_args()
    require(args.run_id.replace('_','').isalnum(), 'Unsafe run ID')
    report=ROOT/'reports'/args.run_id; checkpoints=ROOT/'checkpoints'/args.run_id
    try:
        if args.stage=='audit': audit(report)
        elif args.stage=='preflight': preflight(report,checkpoints)
        else: train(report,checkpoints)
    except Exception:
        traceback.print_exc()
        if report.is_dir():
            failure=report/('failure_'+args.stage+'.json')
            if not failure.exists(): write(failure,dict(status='FAIL',stage=args.stage,traceback=traceback.format_exc()))
        raise
