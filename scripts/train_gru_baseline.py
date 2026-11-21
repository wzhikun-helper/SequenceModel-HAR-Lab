"""One audited GRU experiment, integrated disposable checks, no test-based tuning."""
import argparse
import csv
import datetime as dt
import inspect
import json
from pathlib import Path
import platform
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
from har_lab.gru_baseline_b import GRUBaselineB, parameter_calculation
from har_lab.cnn import targets_from_official
from har_contracts import validate_window_shape, validate_channel_order, validate_labels, NAMES
from cnn_metrics import improves
from train_cnn_baseline_a import (seed_all, evaluate, read, write, sha, require, relative)

AUDIT = ROOT / 'reports/gru_baseline_preflight_20261121'
CNN = ROOT / 'reports/cnn_baseline_seed42_20261119_run01'
DATA = ROOT / 'data/processed/day01_data_20261026_run02_audit02'


def now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()


def make_config(audit):
    # Copy actual CNN configuration before removing only CNN-specific architecture keys.
    config = dict(audit['cnn_config'])
    for key in ['conv_channels', 'kernel_size', 'stride', 'padding', 'dilation',
                'maxpool_size', 'activation', 'pooling']:
        config.pop(key)
    config.update(model='GRU Baseline B', input_shape=[128, 9], input_size=9, hidden_size=64,
                  num_layers=1, bidirectional=False, batch_first=True, dropout=0.0,
                  classifier_input='h_n[-1]', initial_hidden='implicit zeros',
                  gradient_clipping=None, amp=False, dtype='float32',
                  adam_all_parameters=audit['adam_all_parameters'],
                  zero_grad_set_to_none=True, loss_ignore_index=-100, label_smoothing=0.0,
                  validation_shuffle=False, test_shuffle=False, pin_memory=False,
                  persistent_workers=False, initialization='PyTorch 2.0.1 defaults, seed42')
    return config


def loader(split, config):
    with np.load(DATA / (split + '_standardized.npz'), allow_pickle=False) as data:
        validate_window_shape(data['X'].shape, {'train': 6037, 'validation': 1315, 'test': 2947}[split])
        validate_channel_order(data['channels'].tolist())
        validate_labels(data['y'], require_all=True)
        require(data['X'].dtype == np.float32 and np.isfinite(data['X']).all(), 'Invalid input values')
        require(data['y'].dtype == np.int64, 'Official labels must remain int64')
        X = torch.from_numpy(data['X'].copy()).contiguous()
        y = targets_from_official(torch.from_numpy(data['y'].copy()))
    generator = torch.Generator().manual_seed(config['seed'])
    return DataLoader(TensorDataset(X, y), batch_size=config['batch_size'], shuffle=split == 'train',
                      drop_last=config['drop_last'], num_workers=config['num_workers'],
                      generator=generator, pin_memory=False, persistent_workers=False)


def optimizer(model, config):
    adam = config['adam_all_parameters']
    return torch.optim.Adam(model.parameters(), lr=adam['lr'], betas=tuple(adam['betas']),
                            eps=adam['eps'], weight_decay=adam['weight_decay'],
                            amsgrad=adam['amsgrad'], foreach=adam['foreach'],
                            maximize=adam['maximize'], capturable=adam['capturable'],
                            differentiable=adam['differentiable'], fused=adam['fused'])


def integrated_checks(config, report):
    """Disposable model/optimizer, then caller reseeds and initializes formal objects."""
    seed_all(config)
    model = GRUBaselineB().to(config['device'])
    optim = optimizer(model, config)
    initial = {k: v.clone() for k, v in model.state_dict().items()}
    shapes, losses, gradients = {}, [], []

    def capture_gru(module, inputs, outputs):
        shapes.update(input=list(inputs[0].shape), output=list(outputs[0].shape),
                      h_n=list(outputs[1].shape), last_hidden=list(outputs[1][-1].shape))

    def capture_classifier(module, inputs, output):
        shapes.update(classifier_input=list(inputs[0].shape), logits=list(output.shape))

    handles = [model.gru.register_forward_hook(capture_gru),
               model.classifier.register_forward_hook(capture_classifier)]
    for index, (X, y) in enumerate(loader('train', config)):
        X, y = X.to(config['device']), y.to(config['device'])
        require(X.shape == (64, 128, 9) and y.dtype == torch.int64 and ((y >= 0) & (y <= 5)).all(),
                'Integrated batch/label contract failed')
        optim.zero_grad(set_to_none=True)
        logits = model(X)
        require(logits.shape == (64, 6), 'Expected [B,6] logits')
        loss = nn.functional.cross_entropy(logits, y)
        require(torch.isfinite(loss).item(), 'Nonfinite integrated-check loss')
        loss.backward()
        grad = {}
        for name, parameter in model.named_parameters():
            require(parameter.grad is not None and torch.isfinite(parameter.grad).all().item()
                    and torch.count_nonzero(parameter.grad).item() > 0, 'Invalid gradient: ' + name)
            grad[name] = dict(finite=True, nonzero=int(torch.count_nonzero(parameter.grad)),
                              l2=float(parameter.grad.norm()))
        optim.step()
        gradients.append(grad)
        losses.append(float(loss.detach()))
        if index == 1:
            break
    for handle in handles:
        handle.remove()
    changes = {k: not torch.equal(initial[k], v) for k, v in model.state_dict().items()}
    require(all(changes.values()), 'Adam failed to update every parameter tensor')
    require(shapes == dict(input=[64, 128, 9], output=[64, 128, 64], h_n=[1, 64, 64],
                           last_hidden=[64, 64], classifier_input=[64, 64], logits=[64, 6]), 'GRU shapes')
    calculated = parameter_calculation()
    actual = sum(p.numel() for p in model.parameters())
    require(actual == calculated['total'] == 14790, 'Parameter count mismatch')
    write(report / 'integrated_preflight.json', dict(status='PASS', batches=2, losses=losses,
          gradients=gradients, updated_parameters=changes, shapes=shapes,
          formal_objects_reinitialized_after_checks=True, separate_minimal_experiment=False))
    write(report / 'model_summary.json', dict(architecture=str(model), shapes=shapes,
          calculated=calculated, actual_parameters=actual,
          parameters={k: dict(shape=list(p.shape), numel=p.numel(), dtype=str(p.dtype))
                      for k, p in model.named_parameters()}))
    print('INTEGRATED CHECKS PASS: two real batches; updates confirmed; discard model/optimizer', flush=True)


def main(run):
    require(run.replace('_', '').isalnum(), 'Unsafe run ID')
    report, checkpoints = ROOT / 'reports' / run, ROOT / 'checkpoints' / run
    require(not report.exists() and not checkpoints.exists(), 'Use a new run ID; refuse overwrites')
    report.mkdir(parents=True)
    checkpoints.mkdir(parents=True)
    started_at = now()
    try:
        audit = read(AUDIT / 'audit_evidence.json')
        require(audit['status'] == 'PASS', 'CNN configuration audit must pass first')
        cnn_config = read(CNN / 'config.json')
        require(sha(CNN / 'config.json') == audit['config_sha256'], 'Audited CNN configuration changed')
        for path, expected in audit['frozen_before'].items():
            require(sha(ROOT / path) == expected, 'Frozen pre-implementation source/report changed: ' + path)
        protected = read(CNN / 'data_audit.json')['protected_sha256']
        require(all(sha(ROOT / p) == h for p, h in protected.items()), 'Data/scaler/ignore integrity failure')
        current = dict(python=sys.version, interpreter=sys.executable, platform=platform.platform(),
                       pytorch=torch.__version__, numpy=np.__version__, cuda_build=torch.version.cuda,
                       cuda_available=torch.cuda.is_available(), device='cpu')
        require(current == audit['environment'], 'Environment differs from audited CNN')
        config = make_config(audit)
        # Formal common keys must match copied CNN values exactly.
        for key in cnn_config:
            if key in config and key != 'input_shape':
                require(config[key] == cnn_config[key], 'Common configuration mismatch: ' + key)
        write(report / 'config.json', config)
        write(report / 'environment.json', dict(current, torch_default_dtype=str(torch.get_default_dtype()),
              torch_threads=config['torch_threads'], amp=False, deterministic_algorithms=True,
              cudnn_benchmark=False, cudnn_deterministic=True, cublas_workspace_config=':4096:8'))
        source_paths = ['scripts/train_gru_baseline.py', 'src/har_lab/gru_baseline_b.py',
                        'scripts/train_cnn_baseline_a.py', 'scripts/cnn_metrics.py',
                        'scripts/har_contracts.py', 'src/har_lab/cnn.py']
        write(report / 'source_provenance.json', dict(base_head=subprocess.check_output(
              ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              source_sha256={p: sha(ROOT / p) for p in source_paths},
              config_sha256=sha(report / 'config.json'), audit_sha256=sha(AUDIT / 'audit_evidence.json'),
              protected_inputs=protected, started_at=started_at))
        integrated_checks(config, report)
        seed_all(config)
        model = GRUBaselineB().to(config['device'])
        optim = optimizer(model, config)
        require(all(p.dtype == torch.float32 for p in model.parameters()), 'Must use audited FP32')
        train_loader, val_loader = loader('train', config), loader('validation', config)
        # Same data-order RNG as CNN; its model-side RNG usage is intentionally model-specific.
        probe = next(iter(val_loader))[0][:8].to(config['device'])
        actual_adam = {k: list(v) if isinstance(v, tuple) else v for k, v in optim.defaults.items()}
        require(actual_adam == audit['adam_all_parameters'], 'Runtime optimizer differs')
        write(report / 'runtime_conditions.json', dict(optimizer_defaults=actual_adam,
              zero_grad_set_to_none=True, dtype=str(next(model.parameters()).dtype),
              threads=torch.get_num_threads(), deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
              amp=False, gradient_clipping=None, scheduler=None, loss_reduction='mean',
              parameter_updates_validation=False, test_model_passes_before_selection=0,
              loader=dict(batch_size=train_loader.batch_size, drop_last=train_loader.drop_last,
              num_workers=train_loader.num_workers, sampler=type(train_loader.sampler).__name__,
              validation_sampler=type(val_loader.sampler).__name__, generator_seed=train_loader.generator.initial_seed())))
        headers = ['epoch', 'training_loss', 'training_accuracy', 'validation_loss', 'validation_accuracy',
                   'validation_macro_f1', 'learning_rate', 'epoch_seconds', 'best_epoch',
                   'updated_best', 'early_stopping_count', 'train_samples', 'train_batches']
        best_f1, best_loss, best_epoch, stale = -1.0, float('inf'), 0, 0
        history, epoch_durations = [], []
        best_path = None
        loop_started = time.perf_counter()
        with (report / 'training_history.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            stream.flush()
            for epoch in range(1, config['max_epochs'] + 1):
                tick = time.perf_counter()
                model.train()
                total, count, correct, batches = 0.0, 0, 0, 0
                for X, y in train_loader:
                    X, y = X.to(config['device']), y.to(config['device'])
                    optim.zero_grad(set_to_none=True)
                    logits = model(X)
                    loss = nn.functional.cross_entropy(logits, y)
                    require(torch.isfinite(loss).item(), 'Nonfinite training loss')
                    loss.backward()
                    require(all(p.grad is not None and torch.isfinite(p.grad).all().item()
                                for p in model.parameters()), 'Missing/nonfinite gradient')
                    optim.step()
                    total += float(loss.detach()) * len(y)
                    correct += int((logits.detach().argmax(1) == y).sum())
                    count += len(y)
                    batches += 1
                require(count == 6037 and batches == 95, 'Incomplete training epoch')
                val, _, _, _ = evaluate(model, val_loader, config['device'])
                update = improves(val['macro_f1'], val['loss'], best_f1, best_loss)
                if update:
                    best_f1, best_loss, best_epoch, stale = val['macro_f1'], val['loss'], epoch, 0
                    best_path = checkpoints / ('epoch_%03d.pt' % epoch)
                    with torch.no_grad():
                        reference = model(probe).cpu()
                    with best_path.open('xb') as stream_ck:
                        torch.save(dict(state_dict=model.state_dict(), epoch=epoch, seed=config['seed'],
                              validation_logits=reference, config_sha256=sha(report / 'config.json')), stream_ck)
                else:
                    stale += 1
                elapsed = time.perf_counter() - tick
                epoch_durations.append(elapsed)
                row = dict(epoch=epoch, training_loss=total / count, training_accuracy=correct / count,
                           validation_loss=val['loss'], validation_accuracy=val['accuracy'],
                           validation_macro_f1=val['macro_f1'], learning_rate=optim.param_groups[0]['lr'],
                           epoch_seconds=elapsed, best_epoch=best_epoch, updated_best=update,
                           early_stopping_count=stale, train_samples=count, train_batches=batches)
                history.append(row)
                writer.writerow(row)
                stream.flush()
                print(json.dumps(row), flush=True)
                if stale >= config['early_stopping_patience']:
                    break
        loop_seconds = time.perf_counter() - loop_started
        last_path = checkpoints / 'last_checkpoint.pt'
        with last_path.open('xb') as stream:
            torch.save(dict(state_dict=model.state_dict(), epoch=len(history), seed=config['seed'],
                            config_sha256=sha(report / 'config.json')), stream)
        # A byte-identical, explicit best_checkpoint alias without overwriting epoch files.
        best_alias = checkpoints / 'best_checkpoint.pt'
        with best_alias.open('xb') as target, best_path.open('rb') as source:
            target.write(source.read())
        require(sha(best_alias) == sha(best_path), 'Best alias differs')
        saved = torch.load(best_alias, map_location=config['device'], weights_only=True)
        best = GRUBaselineB().to(config['device'])
        best.load_state_dict(saved['state_dict'], strict=True)
        best.eval()
        with torch.no_grad():
            output = best(probe).cpu()
        require(torch.equal(output, saved['validation_logits'].cpu()), 'Best reload outputs differ')
        val, _, _, _ = evaluate(best, val_loader, config['device'])
        require(val['macro_f1'] == best_f1 and val['loss'] == best_loss, 'Best validation replay differs')
        last_copy = GRUBaselineB().to(config['device'])
        last_copy.load_state_dict(torch.load(last_path, map_location=config['device'],
                                           weights_only=True)['state_dict'], strict=True)
        model.eval()
        last_copy.eval()
        with torch.no_grad():
            last_a, last_b = model(probe), last_copy(probe)
        require(torch.equal(last_a, last_b), 'Last checkpoint reload outputs differ')
        checkpoint_info = dict(best_epoch=best_epoch, best_validation_macro_f1=best_f1,
                               best_validation_loss=best_loss, best_epoch_file=relative(best_path))
        for name, path in [('best', best_alias), ('last', last_path)]:
            checkpoint_info[name] = dict(path=relative(path), bytes=path.stat().st_size, sha256=sha(path))
        write(report / 'checkpoint_reload_verification.json', dict(status='PASS', strict=True,
              weights_only=True, best_max_abs_difference=float((output - saved['validation_logits'].cpu()).abs().max()),
              last_max_abs_difference=float((last_a - last_b).abs().max()),
              validation_replay_exact=True, checkpoints=checkpoint_info))
        # Only official model evaluation on test; no test loader is used by the training loop.
        test, _, truth, pred = evaluate(best, loader('test', config), config['device'])
        test.update(activity_names=[NAMES[i] for i in range(1, 7)], best_epoch=best_epoch,
                    test_model_evaluation_passes=1, selection_used_test=False,
                    checkpoint_sha256=sha(best_alias))
        write(report / 'metrics.json', test)
        write(report / 'test_metrics.json', test)
        write(report / 'classification_report.json', {
            name: dict(official_label=i + 1, precision=test['precision'][i], recall=test['recall'][i],
                       f1=test['f1'][i], support=test['support'][i])
            for i, name in enumerate(test['activity_names'])})
        with (report / 'confusion_matrix.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['true_activity'] + test['activity_names'])
            for name, row in zip(test['activity_names'], test['confusion_matrix']):
                writer.writerow([name] + row)
        with (report / 'test_predictions.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['official_test_row_1based', 'true_label_0based', 'pred_label_0based'])
            for index, (y, prediction) in enumerate(zip(truth, pred), 1):
                writer.writerow([index, y, prediction])
        with (report / 'per_class_metrics.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['official_label', 'activity', 'precision', 'recall', 'f1', 'support'])
            for i, name in enumerate(test['activity_names']):
                writer.writerow([i + 1, name, test['precision'][i], test['recall'][i], test['f1'][i], test['support'][i]])
        require(all(sha(ROOT / p) == h for p, h in protected.items()), 'Input/scaler/gitignore changed')
        write(report / 'training_result.json', dict(status='PASS', seed=config['seed'],
              best_epoch=best_epoch, epochs_completed=len(history), final_stale_count=stale,
              stopped_early=stale >= config['early_stopping_patience'],
              stop_reason='patience' if stale >= config['early_stopping_patience'] else 'max_epochs',
              best_validation=val, epoch_loop_seconds=loop_seconds,
              epoch_seconds_sum=sum(epoch_durations), started_at=started_at, finished_at=now(),
              optimizer_steps=95 * len(history), test_evaluation_passes=1,
              inference_seconds=None, inference_timing_status='not separately measured',
              checkpoints=checkpoint_info, input_hashes_unchanged=True))
        print('FINAL ' + json.dumps(dict(best_epoch=best_epoch, epochs=len(history),
              test_accuracy=test['accuracy'], test_macro_f1=test['macro_f1'])), flush=True)
    except Exception:
        traceback.print_exc()
        failure = report / 'failure.json'
        if not failure.exists():
            write(failure, dict(status='FAIL', timestamp=now(), traceback=traceback.format_exc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    main(parser.parse_args().run_id)
