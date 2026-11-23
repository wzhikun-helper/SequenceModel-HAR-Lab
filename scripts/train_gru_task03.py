"""Run the approved three-seed CUDA GRU experiment with frozen inputs."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
import yaml

from train_gru_baseline import DATA, GRUBaselineB, integrated_checks, loader, optimizer
from train_cnn_baseline_a import evaluate, read, require, seed_all, sha, write
from cnn_metrics import improves
from har_contracts import NAMES

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/gru_task03/gpu_base.yaml'
SEEDS = (42, 43, 44)


def now():
    return datetime.now(timezone.utc).isoformat()


def cfg(seed):
    return dict(yaml.safe_load(CONFIG.read_text()), seed=seed)


def initialize(config):
    seed_all(config)
    torch.backends.cuda.matmul.allow_tf32 = config['tf32']
    torch.backends.cudnn.allow_tf32 = config['tf32']
    return GRUBaselineB().to(config['device'])


def fingerprint(model):
    digest = hashlib.sha256()
    for name, p in model.state_dict().items():
        digest.update(name.encode('ascii') + b'\0')
        digest.update(p.detach().cpu().numpy().astype('<f4', copy=False).tobytes())
    return digest.hexdigest()


def train_with_rows(config):
    historical = loader('train', config)
    with np.load(DATA / 'train_standardized.npz', allow_pickle=False) as frozen:
        rows = torch.from_numpy(frozen['official_row_1based'].astype(np.int64))
    return DataLoader(TensorDataset(*historical.dataset.tensors, rows),
                      batch_size=historical.batch_size, shuffle=True,
                      num_workers=historical.num_workers, drop_last=historical.drop_last,
                      generator=historical.generator, pin_memory=historical.pin_memory,
                      persistent_workers=historical.persistent_workers)


def checkpoint(path, model, epoch, seed, config_path, probe):
    model.eval()
    with torch.no_grad():
        reference = model(probe).cpu()
    with path.open('xb') as stream:
        torch.save(dict(state_dict=model.state_dict(), epoch=epoch, seed=seed,
                        config_sha256=sha(config_path), validation_logits=reference), stream)


def reload_checkpoint(path, config, config_path, probe):
    state = torch.load(path, map_location='cpu', weights_only=True)
    require(state['seed'] == config['seed'] and state['config_sha256'] == sha(config_path),
            'Checkpoint provenance differs')
    model = GRUBaselineB().to(config['device'])
    model.load_state_dict(state['state_dict'], strict=True)
    model.eval()
    with torch.no_grad():
        out = model(probe).cpu()
    require(torch.equal(out, state['validation_logits']), 'Checkpoint validation logits differ')
    return model, state['epoch']


def preflight(path):
    path.mkdir()
    conf = cfg(42)
    a = initialize(conf)
    first, second = fingerprint(a), fingerprint(initialize(conf))
    require(first == second, 'Same-seed initialization did not repeat')
    require(len({fingerprint(initialize(cfg(seed))) for seed in SEEDS}) == 3,
            'Seeds did not yield distinct starts')
    train = train_with_rows(conf)
    original = loader('train', conf)
    for (x, y, _), (reference, labels) in zip(train, original):
        require(torch.equal(x, reference) and torch.equal(y, labels), 'Sampler adapter changed data order')
    initialize(conf)
    integrated_checks(conf, path)
    adam = optimizer(a, conf)
    actual = {k: list(v) if isinstance(v, tuple) else v for k, v in adam.defaults.items()}
    require(actual == conf['adam_all_parameters'], 'Adam defaults differ')
    val = loader('validation', conf)
    probe = next(iter(val))[0][:8].to(conf['device'])
    config_path = path / 'config.yaml'
    config_path.write_text(yaml.safe_dump(conf, sort_keys=False))
    checkpoint(path / 'preflight.pt', a, 0, 42, config_path, probe)
    reload_checkpoint(path / 'preflight.pt', conf, config_path, probe)
    write(path / 'checks.json', dict(status='PASS', same_seed_initialization=first,
          all_seeds_distinct=True, original_loader_order_equal=True, checkpoint_reload_exact=True,
          adam_defaults=actual, tf32=False, amp=False, fp32=True))


def run(seed, out, admission):
    approval = read(admission)
    require(approval['training_authorization'] == 'APPROVED', 'Task 03 admission is not approved')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
            == approval['prep_head'], 'Reviewed training commit changed')
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
            'Worktree must remain clean during formal training')
    expected = approval['data_sha256']
    require(all(sha(DATA / name) == digest for name, digest in expected.items()), 'Frozen inputs changed')
    require(seed == SEEDS[sum((out.parent / f'seed{s}' / 'training_result.json').is_file()
                             for s in SEEDS)], 'Run seeds in the approved sequence')
    started = now()
    out.mkdir()
    config = cfg(seed)
    config_path = out / 'config.yaml'
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    model = initialize(config)
    initial = fingerprint(model)
    adam = optimizer(model, config)
    train, val = train_with_rows(config), loader('validation', config)
    device = config['device']
    probe = next(iter(val))[0][:8].to(device)
    require(sum(p.numel() for p in model.parameters()) == 14790
            and all(p.dtype == torch.float32 for p in model.parameters()), 'Model contract changed')
    header = ['epoch','training_loss','training_accuracy','validation_loss','validation_accuracy',
              'validation_macro_f1','best_epoch','early_stopping_count','epoch_seconds','peak_allocated_bytes',
              'order_sha256']
    best_epoch, best_f1, best_loss, stale = 0, -1.0, float('inf'), 0
    best_path = None
    orders = []
    order_set = None
    start = time.perf_counter()
    with (out / 'training_history.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=header, lineterminator='\n')
        writer.writeheader()
        for epoch in range(1, config['max_epochs'] + 1):
            tick = time.perf_counter()
            torch.cuda.reset_peak_memory_stats()
            model.train()
            total, correct, count = 0.0, 0, 0
            order = []
            for x, y, rows in train:
                order.extend(rows.tolist())
                x, y = x.to(device), y.to(device)
                adam.zero_grad(set_to_none=True)
                logits = model(x)
                loss = nn.functional.cross_entropy(logits, y)
                require(torch.isfinite(loss).item(), 'Nonfinite loss')
                loss.backward()
                require(all(p.grad is not None and torch.isfinite(p.grad).all().item()
                            for p in model.parameters()), 'Nonfinite or missing gradient')
                adam.step()
                total += loss.item()*len(y)
                correct += int((logits.detach().argmax(1)==y).sum())
                count += len(y)
            if order_set is None:
                order_set = set(train.dataset.tensors[-1].tolist())
            require(len(train)==95 and len(order)==count==6037 and set(order)==order_set,
                    'Training epoch omitted or repeated an official row')
            sequence = hashlib.sha256(np.asarray(order, dtype='<i8').tobytes()).hexdigest()
            orders.append(sequence)
            metrics, _, _, _ = evaluate(model, val, device)
            if improves(metrics['macro_f1'], metrics['loss'], best_f1, best_loss):
                best_epoch, best_f1, best_loss, stale = epoch, metrics['macro_f1'], metrics['loss'], 0
                best_path = out / f'epoch_{epoch:03d}.pt'
                checkpoint(best_path, model, epoch, seed, config_path, probe)
            else:
                stale += 1
            row = dict(epoch=epoch, training_loss=total/count, training_accuracy=correct/count,
                       validation_loss=metrics['loss'], validation_accuracy=metrics['accuracy'],
                       validation_macro_f1=metrics['macro_f1'], best_epoch=best_epoch,
                       early_stopping_count=stale, epoch_seconds=time.perf_counter()-tick,
                       peak_allocated_bytes=torch.cuda.max_memory_allocated(), order_sha256=sequence)
            writer.writerow(row)
            stream.flush()
            print(json.dumps(row), flush=True)
            if stale >= config['early_stopping_patience']:
                break
    elapsed = time.perf_counter()-start
    last_path = out / 'last.pt'
    checkpoint(last_path, model, epoch, seed, config_path, probe)
    with (out / 'best.pt').open('xb') as f:
        f.write(best_path.read_bytes())
    best, loaded_best = reload_checkpoint(out/'best.pt',config,config_path,probe)
    _, loaded_last = reload_checkpoint(last_path,config,config_path,probe)
    require((loaded_best,loaded_last)==(best_epoch,epoch),'Checkpoint epoch metadata differs')
    validation, _, _, _ = evaluate(best, val, device)
    require((validation['macro_f1'],validation['loss'])==(best_f1,best_loss), 'Best validation replay changed')
    test, logits, truth, pred = evaluate(best, loader('test', config), device)
    with np.load(DATA/'test_standardized.npz',allow_pickle=False) as frozen:
        row_ids = frozen['official_row_1based'].tolist()
        require((frozen['y']-1).tolist()==truth and len(truth)==2947,'Official test order changed')
    with (out/'test_predictions.csv').open('x',newline='') as f:
        writer = csv.writer(f,lineterminator='\n')
        writer.writerow(['official_row_1based','true_label_0based','pred_label_0based',
                         *[f'logit_{i}' for i in range(6)]])
        writer.writerows((i,y,p,*values) for i,y,p,values in zip(row_ids,truth,pred,logits.tolist()))
    with (out/'classification_report.csv').open('x',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['label','activity','precision','recall','f1','support'])
        writer.writerows(zip(NAMES,NAMES.values(),test['precision'],test['recall'],test['f1'],test['support']))
    test.update(seed=seed,best_epoch=best_epoch,test_model_evaluation_passes=1,
                selection_used_test=False,test_artifact_sha256=expected['test_standardized.npz'])
    write(out/'test_metrics.json',test)
    require(all(sha(DATA/name)==digest for name,digest in expected.items()),'Frozen inputs changed during run')
    write(out/'training_result.json',dict(status='PASS',seed=seed,initial_weight_sha256=initial,
          order_sha256=orders,order_encoding='concatenated official training row IDs, little-endian int64',
          best_epoch=best_epoch,epochs_completed=epoch,optimizer_steps=95*epoch,
          stopped_early=stale>=config['early_stopping_patience'],final_stale_count=stale,
          best_validation=validation,test_model_evaluation_passes=1,
          best_sha256=sha(out/'best.pt'),last_sha256=sha(last_path),strict_reloads_equal=True,
          started_at=started,finished_at=now(),training_seconds=elapsed,prep_head=approval['prep_head']))
    print('FINAL '+json.dumps(test),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight',type=Path)
    parser.add_argument('--seed',type=int,choices=SEEDS)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--admission',type=Path)
    args=parser.parse_args()
    if args.preflight:
        preflight(args.preflight)
    elif args.seed is not None and args.out and args.admission:
        run(args.seed,args.out,args.admission)
    else:
        parser.error('supply --preflight or --seed, --out and --admission')
