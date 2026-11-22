"""Audit, preflight, train, and evaluate Mamba D once on the frozen HAR protocol."""
import argparse
import csv
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def main(project, data, run_dir):
    sys.path[:0] = [str(ROOT / 'src'), str(project / 'scripts'), str(project / 'src')]
    from cnn_metrics import improves
    from har_contracts import NAMES, validate_channel_order, validate_labels, validate_window_shape
    from har_lab.cnn import targets_from_official
    from train_cnn_baseline_a import evaluate, read, require, seed_all, sha, write
    from train_gru_baseline import optimizer
    from mamba_baseline_d import MambaBaselineD
    import numpy as np
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset
    import selective_scan_cuda

    config_file = ROOT / 'configs/seed42.json'
    config = read(config_file)
    historical = read(project / 'reports/mamba_l0_20261122/project_audit.json')
    require(all(config[k] == v for k, v in historical['common_config'].items()),
            'Training protocol differs from the historical audit')
    require(version('mamba-ssm') == config['mamba_version'], 'Incorrect official Mamba version')
    require(torch.cuda.is_available(), 'CUDA is required')
    require(run_dir.is_dir(), 'Run directory must be prepared first')
    report, checkpoints = run_dir / 'reports', run_dir / 'checkpoints'
    require(report.is_dir() and checkpoints.is_dir() and not any(report.iterdir())
            and not any(checkpoints.iterdir()), 'Use fresh report and checkpoint directories')

    filenames = [f'{split}_standardized.npz' for split in historical['splits']]
    filenames.append('scaler_train_only.json')
    frozen = {Path(p).name: digest for p, digest in historical['frozen_inputs'].items()
              if Path(p).name in filenames}
    require(set(filenames) == set(frozen), 'Incomplete frozen hash manifest')
    actual = {name: sha(data / name) for name in filenames}
    require(actual == frozen, 'Training inputs must match historical SHA-256 exactly')
    write(report / 'data_hashes.json', dict(observed=actual, historical=frozen,
          byte_matches={name: actual[name] == frozen[name] for name in actual}))

    device = torch.device(config['device'])
    seed_all(config)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    started_at = datetime.now(timezone.utc).isoformat()

    def loader(split):
        expected = historical['splits'][split]
        with np.load(data / f'{split}_standardized.npz', allow_pickle=False) as file:
            X, y, subjects = file['X'], file['y'], file['subject']
            validate_window_shape(X.shape, expected['n_windows'])
            validate_channel_order(file['channels'].tolist())
            validate_labels(y, require_all=True)
            require(X.dtype == np.float32 and np.isfinite(X).all(), 'Invalid FP32 windows')
            require(y.dtype == np.int64, 'Official labels must be int64')
            require(np.unique(subjects).tolist() == expected['subjects'], 'Subject split differs')
            require(dict(zip(NAMES.values(), np.bincount(y, minlength=7)[1:].tolist()))
                    == expected['class_counts'], 'Class counts differ')
            if split == 'test':
                require(np.array_equal(file['official_row_1based'], np.arange(1, len(y) + 1)),
                        'Official test rows are out of order')
            dataset = TensorDataset(torch.from_numpy(X), targets_from_official(torch.from_numpy(y)))
        return DataLoader(dataset, batch_size=config['batch_size'], shuffle=split == 'train',
                          generator=torch.Generator().manual_seed(config['seed']),
                          drop_last=config['drop_last'], num_workers=config['num_workers'])

    def save_checkpoint(name, model, epoch, probe_logits=None):
        path = checkpoints / name
        with path.open('xb') as stream:
            torch.save(dict(state_dict=model.state_dict(), epoch=epoch, seed=config['seed'],
                            validation_logits=probe_logits, config_sha256=sha(config_file)), stream)
        return path

    def initialize():
        seed_all(config)
        return MambaBaselineD(**config['block']).to(device)

    def reload(path):
        state = torch.load(path, map_location=device, weights_only=True)
        require(state['config_sha256'] == sha(config_file), 'Checkpoint configuration differs')
        model = MambaBaselineD(**config['block']).to(device)
        model.load_state_dict(state['state_dict'], strict=True)
        return model.eval(), state

    def train_step(model, adam, X, y):
        adam.zero_grad(set_to_none=True)
        logits = model(X)
        require(logits.shape == (len(y), 6) and logits.dtype == torch.float32
                and logits.is_cuda, 'FP32 CUDA logits contract failed')
        loss = nn.functional.cross_entropy(logits, y)
        require(torch.isfinite(loss).item(), 'Nonfinite training loss')
        loss.backward()
        require(torch.stack([torch.isfinite(p.grad).all() for p in model.parameters()
                             if p.grad is not None]).all().item()
                and all(p.grad is not None for p in model.parameters()), 'Missing/nonfinite gradient')
        adam.step()
        return loss.detach(), logits.detach()

    preflight = initialize()
    initial = {name: param.detach().clone() for name, param in preflight.named_parameters()}
    parameter_count = sum(p.numel() for p in preflight.parameters() if p.requires_grad)
    write(report / 'model_summary.json', dict(
        model=str(preflight), actual_parameters=parameter_count,
        parameters={name: dict(shape=list(p.shape), count=p.numel(), dtype=str(p.dtype),
                               requires_grad=p.requires_grad) for name, p in preflight.named_parameters()}))
    print(f'Trainable parameters: {parameter_count}', flush=True)
    write(report / 'runtime.json', dict(
        started_at=started_at, python=sys.version.split()[0], pytorch=torch.__version__,
        cuda_runtime=torch.version.cuda, gpu=torch.cuda.get_device_name(device),
        gpu_compute_capability=torch.cuda.get_device_capability(device), mamba=version('mamba-ssm'),
        torch_cxx11_abi=torch._C._GLIBCXX_USE_CXX11_ABI, numpy=np.__version__,
        dtype=str(next(preflight.parameters()).dtype), tf32=False, amp=False,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        cudnn_deterministic=torch.backends.cudnn.deterministic, config_sha256=sha(config_file)))
    adam = optimizer(preflight, config)
    preflight_rows = []
    batches = iter(loader('train'))
    for index in range(1, 3):
        X, y = (t.to(device) for t in next(batches))
        before = {name: p.detach().clone() for name, p in preflight.block.named_parameters()}
        with patch.object(selective_scan_cuda, 'fwd', wraps=selective_scan_cuda.fwd) as fwd, \
             patch.object(selective_scan_cuda, 'bwd', wraps=selective_scan_cuda.bwd) as bwd:
            loss, logits = train_step(preflight, adam, X, y)
        require(fwd.call_count == bwd.call_count == 1
                and fwd.call_args.args[0].is_cuda and bwd.call_args.args[0].is_cuda,
                'Official CUDA selective scan forward/backward was not observed')
        gradients = {n: dict(finite=True, l2=p.grad.norm().item(),
                             nonzero=torch.count_nonzero(p.grad).item())
                     for n, p in preflight.block.named_parameters()}
        deltas = {n: (p.detach() - before[n]).abs().max().item()
                  for n, p in preflight.block.named_parameters()}
        require(any(deltas.values()) and any(v['nonzero'] for v in gradients.values()),
                'Original Mamba block did not receive a nonzero gradient and Adam update')
        preflight_rows.append(dict(batch=index, input_shape=list(X.shape), logits_shape=list(logits.shape),
                                   loss=loss.item(), fwd_calls=fwd.call_count, bwd_calls=bwd.call_count,
                                   block_gradients=gradients, block_max_parameter_deltas=deltas))
    probe_path = save_checkpoint('preflight.pt', preflight, 0)
    preflight_copy, _ = reload(probe_path)
    preflight.eval()
    with torch.no_grad():
        diff = (preflight(X) - preflight_copy(X)).abs().max().item()
    require(diff == 0.0, 'Preflight checkpoint changed eval outputs')
    write(report / 'preflight.json', dict(status='PASS', batches=preflight_rows,
          checkpoint_sha256=sha(probe_path), reload_max_abs_difference=diff))
    print('PREFLIGHT PASS', flush=True)

    model = initialize()
    require(all(torch.equal(initial[n], p) for n, p in model.named_parameters()),
            'Formal initialization differs from Seed42 preflight initialization')
    del preflight, preflight_copy, adam, initial, before, X, y, batches
    torch.cuda.empty_cache()
    adam = optimizer(model, config)
    train, val = loader('train'), loader('validation')
    probe = next(iter(val))[0][:8].to(device)
    best_f1, best_loss, stale, best_path = -1.0, float('inf'), 0, None
    tick = time.perf_counter()
    with (report / 'training_history.csv').open('x', newline='') as stream:
        writer = None
        for epoch in range(1, config['max_epochs'] + 1):
            epoch_tick = time.perf_counter()
            torch.cuda.reset_peak_memory_stats(device)
            model.train()
            total, count = 0.0, 0
            for X, y in train:
                loss, _ = train_step(model, adam, X.to(device), y.to(device))
                total += loss.item() * len(y)
                count += len(y)
            require(count == 6037 and len(train) == 95, 'Incomplete training epoch')
            validation, _, _, _ = evaluate(model, val, device)
            require(validation['n'] == 1315, 'Incomplete validation epoch')
            updated = improves(validation['macro_f1'], validation['loss'], best_f1, best_loss)
            if updated:
                best_f1, best_loss, stale, best_epoch = validation['macro_f1'], validation['loss'], 0, epoch
                with torch.no_grad():
                    best_path = save_checkpoint(f'epoch_{epoch:03d}.pt', model, epoch, model(probe).cpu())
            else:
                stale += 1
            row = dict(epoch=epoch, training_loss=total / count, validation_loss=validation['loss'],
                       validation_accuracy=validation['accuracy'], validation_macro_f1=validation['macro_f1'],
                       best_epoch=best_epoch, updated_best=updated, early_stopping_count=stale,
                       epoch_seconds=time.perf_counter() - epoch_tick,
                       peak_allocated_bytes=torch.cuda.max_memory_allocated(device),
                       peak_reserved_bytes=torch.cuda.max_memory_reserved(device))
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=row)
                writer.writeheader()
            writer.writerow(row)
            stream.flush()
            print(json.dumps(row), flush=True)
            if stale >= config['early_stopping_patience']:
                break
    duration = time.perf_counter() - tick

    best_alias = checkpoints / 'best_checkpoint.pt'
    with best_alias.open('xb') as stream:
        stream.write(best_path.read_bytes())
    last_path = save_checkpoint('last_checkpoint.pt', model, epoch)
    best, state = reload(best_alias)
    last, _ = reload(last_path)
    model.eval()
    with torch.no_grad():
        best_diff = (best(probe) - state['validation_logits']).abs().max().item()
        last_diff = (last(probe) - model(probe)).abs().max().item()
    require(best_diff == last_diff == 0.0, 'Checkpoint changed eval outputs')
    replay, _, _, _ = evaluate(best, val, device)
    require(replay['macro_f1'] == best_f1 and replay['loss'] == best_loss,
            'Best validation replay mismatch')
    write(report / 'checkpoint_reload.json', dict(
        status='PASS', strict=True, validation_replay_exact=True, best_max_abs_difference=best_diff,
        last_max_abs_difference=last_diff, best_sha256=sha(best_alias), last_sha256=sha(last_path)))
    require(all(sha(data / name) == digest for name, digest in actual.items()), 'Input hashes changed')

    test, logits, truth, pred = evaluate(best, loader('test'), device)
    require(test['n'] == 2947, 'Incomplete official test evaluation')
    test.update(activity_names=list(NAMES.values()), best_epoch=best_epoch, epochs_completed=epoch,
                parameters=parameter_count, test_model_evaluation_passes=1, selection_used_test=False,
                checkpoint_sha256=sha(best_alias))
    with (report / 'test_predictions.csv').open('x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['official_test_row_1based', 'true_label_0based', 'pred_label_0based',
                         *[f'logit_{i}' for i in range(6)]])
        writer.writerows((i, y, prediction, *values)
                         for i, (y, prediction, values) in enumerate(zip(truth, pred, logits.tolist()), 1))
    write(report / 'test_metrics.json', test)
    write(report / 'training_result.json', dict(
        status='PASS', seed=config['seed'], best_epoch=best_epoch, epochs_completed=epoch,
        stopped_early=stale >= config['early_stopping_patience'], optimizer_steps=95 * epoch,
        training_seconds=duration, best_validation=replay,
        initial_state_equal_to_preflight=True, test_evaluation_passes=1,
        finished_at=datetime.now(timezone.utc).isoformat()))
    print(f'FINAL accuracy={test["accuracy"]:.8f} macro_f1={test["macro_f1"]:.8f}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    main(args.project.resolve(), args.data.resolve(), args.run_dir.resolve())
