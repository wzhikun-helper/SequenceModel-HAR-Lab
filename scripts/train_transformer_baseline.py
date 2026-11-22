"""Approved Transformer C, audited shared conditions, integrated checks and one test."""
import argparse
import csv
import datetime as dt
import hashlib
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
from har_lab.transformer_baseline_c import TransformerBaselineC, parameter_calculation
from har_lab.cnn import targets_from_official
from har_contracts import validate_window_shape, validate_channel_order, validate_labels, NAMES
from cnn_metrics import improves
from train_cnn_baseline_a import (seed_all, evaluate, read, write, sha, require, relative)

AUDIT = ROOT / 'reports/transformer_preflight_20261122'
CNN = ROOT / 'reports/cnn_baseline_seed42_20261119_run01'
DATA = ROOT / 'data/processed/day01_data_20261026_run02_audit02'


def now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()


from train_gru_baseline import loader, optimizer


def state_signature(model):
    result = hashlib.sha256()
    for name, value in model.state_dict().items():
        result.update(name.encode('ascii'))
        result.update(value.detach().cpu().contiguous().numpy().tobytes())
    return result.hexdigest()


def make_config(audit):
    config = dict(audit['gru_config'])
    for key in ['hidden_size', 'bidirectional', 'classifier_input', 'initial_hidden']:
        config.pop(key)
    config.update(model='Transformer Baseline C', d_model=64, nhead=4, num_layers=1,
                  dim_feedforward=128, activation='ReLU', dropout=0.0,
                  batch_first=True, norm_first=False, layer_norm_eps=1e-5,
                  positional_encoding='fixed sinusoidal, base10000, positions0..127',
                  positional_max_length=128, positional_trainable=False,
                  pooling='time mean', final_encoder_norm=None, input_scaling=None,
                  encoder_nested_tensor=True, attention_mask=None,
                  initialization='PyTorch 2.0.1 defaults, seed42')
    return config


def integrated_checks(config, report, checkpoints):
    seed_all(config)
    model = TransformerBaselineC().to(config['device'])
    optim = optimizer(model, config)
    initial = {k: v.clone() for k, v in model.state_dict().items()}
    initial_signature = state_signature(model)
    shapes, losses, gradients = {}, [], []
    handles = []
    for name in ['projection', 'position', 'encoder', 'pool', 'classifier']:
        def capture(module, inputs, output, name=name):
            shapes[name] = list(output.shape)
        handles.append(getattr(model, name).register_forward_hook(capture))
    for index, (X, y) in enumerate(loader('train', config)):
        X, y = X.to(config['device']), y.to(config['device'])
        require(X.shape == (64, 128, 9) and y.dtype == torch.long and ((y >= 0) & (y <= 5)).all(),
                'Real batch input/target contract')
        optim.zero_grad(set_to_none=True)
        logits = model(X)
        require(logits.shape == (64, 6), 'Logits shape')
        loss = nn.functional.cross_entropy(logits, y)
        require(torch.isfinite(loss).item(), 'Nonfinite preflight loss')
        loss.backward()
        check = {}
        for name, parameter in model.named_parameters():
            require(parameter.grad is not None and torch.isfinite(parameter.grad).all().item(),
                    'Missing/nonfinite gradient: ' + name)
            check[name] = dict(finite=True, l2=float(parameter.grad.norm()),
                               nonzero=int(torch.count_nonzero(parameter.grad)))
        require(sum(v['nonzero'] for v in check.values()) > 0, 'All gradients are zero')
        optim.step()
        gradients.append(check)
        losses.append(float(loss.detach()))
        if index == 1:
            break
    for handle in handles:
        handle.remove()
    changes = {name: not torch.equal(initial[name], p) for name, p in model.named_parameters()}
    require(any(changes.values()), 'Adam did not update parameters')
    require(torch.equal(initial['position.encoding'], model.position.encoding), 'Position buffer changed')
    require('position.encoding' not in dict(model.named_parameters()), 'Positions became trainable')
    require(shapes == dict(projection=[64, 128, 64], position=[64, 128, 64],
                          encoder=[64, 128, 64], pool=[64, 64], classifier=[64, 6]), 'Layer shapes')
    actual = sum(p.numel() for p in model.parameters())
    require(actual == parameter_calculation()['total'] == 34502, 'Parameter count mismatch')
    checkpoint = checkpoints / 'preflight.pt'
    with checkpoint.open('xb') as stream:
        torch.save(model.state_dict(), stream)
    other = TransformerBaselineC().to(config['device'])
    other.load_state_dict(torch.load(checkpoint, map_location=config['device'], weights_only=True), strict=True)
    model.eval()
    other.eval()
    with torch.no_grad():
        a, b = model(X), other(X)
    require(torch.equal(a, b), 'Preflight checkpoint outputs differ')
    write(report / 'integrated_preflight.json', dict(status='PASS', batches=2, losses=losses,
          gradients=gradients, parameter_updates=changes, total_gradient_nonzero=True,
          initial_state_sha256=initial_signature, position_buffer_unchanged=True,
          checkpoint=dict(path=relative(checkpoint), bytes=checkpoint.stat().st_size, sha256=sha(checkpoint)),
          reload_max_abs_difference=float((a-b).abs().max()), formal_objects_reinitialized=True))
    write(report / 'model_summary.json', dict(architecture=str(model), input_shape=[64, 128, 9],
          shapes=shapes, actual_parameters=actual, calculated=parameter_calculation(),
          position_buffer_shape=list(model.position.encoding.shape),
          parameters={k: dict(shape=list(p.shape), numel=p.numel(), dtype=str(p.dtype))
                      for k, p in model.named_parameters()},
          buffers={k: dict(shape=list(p.shape), numel=p.numel(), requires_grad=p.requires_grad)
                   for k, p in model.named_buffers()}))
    print('PREFLIGHT PASS: two real batches, finite gradients, Adam updates, exact checkpoint reload', flush=True)


def main(run):
    require(run.replace('_', '').isalnum(), 'Unsafe run ID')
    report, checkpoints = ROOT / 'reports' / run, ROOT / 'checkpoints' / run
    require(not report.exists() and not checkpoints.exists(), 'Use a new run ID; refuse overwrites')
    report.mkdir(parents=True)
    checkpoints.mkdir(parents=True)
    started_at = now()
    try:
        audit = read(AUDIT / 'audit_evidence.json')
        require(audit['status'] == 'PASS', 'Baseline/data audit must pass first')
        cnn_config = read(CNN / 'config.json')
        require(sha(CNN / 'config.json') == audit['cnn_config_sha256'], 'Audited CNN configuration changed')
        for path, expected in audit['scientific_frozen'].items():
            require(sha(ROOT / path) == expected, 'Frozen pre-implementation source/report changed: ' + path)
        protected = audit['protected_inputs']
        require(all(sha(ROOT / p) == h for p, h in protected.items()), 'Data/scaler/ignore integrity failure')
        current = dict(python=sys.version, interpreter=sys.executable, platform=platform.platform(),
                       pytorch=torch.__version__, numpy=np.__version__, cuda_build=torch.version.cuda,
                       cuda_available=torch.cuda.is_available(), device='cpu')
        require(current == audit['environment'], 'Environment differs from audited CNN')
        config = make_config(audit)
        # Formal common keys must match copied CNN values exactly.
        for key in audit['common_keys']:
            if key in config:
                require(config[key] == cnn_config[key], 'Common configuration mismatch: ' + key)
        write(report / 'config.json', config)
        write(report / 'environment.json', dict(current, torch_default_dtype=str(torch.get_default_dtype()),
              torch_threads=config['torch_threads'], amp=False, deterministic_algorithms=True,
              cudnn_benchmark=False, cudnn_deterministic=True, cublas_workspace_config=':4096:8'))
        source_paths = ['scripts/train_transformer_baseline.py', 'src/har_lab/transformer_baseline_c.py',
                        'scripts/train_gru_baseline.py', 'src/har_lab/gru_baseline_b.py',
                        'scripts/train_cnn_baseline_a.py', 'scripts/cnn_metrics.py',
                        'scripts/har_contracts.py', 'src/har_lab/cnn.py']
        write(report / 'source_provenance.json', dict(base_head=subprocess.check_output(
              ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              source_sha256={p: sha(ROOT / p) for p in source_paths},
              config_sha256=sha(report / 'config.json'), audit_sha256=sha(AUDIT / 'audit_evidence.json'),
              protected_inputs=protected, started_at=started_at))
        integrated_checks(config, report, checkpoints)
        seed_all(config)
        model = TransformerBaselineC().to(config['device'])
        require(state_signature(model) == read(report / 'integrated_preflight.json')['initial_state_sha256'], 'Formal initialization differs from original seed42 initialization')
        optim = optimizer(model, config)
        require(all(p.dtype == torch.float32 for p in model.parameters()), 'Must use audited FP32')
        train_loader, val_loader = loader('train', config), loader('validation', config)
        # Same data-order RNG as CNN; its model-side RNG usage is intentionally model-specific.
        probe = next(iter(val_loader))[0][:8].to(config['device'])
        actual_adam = {k: list(v) if isinstance(v, tuple) else v for k, v in optim.defaults.items()}
        require(actual_adam == audit['gru_config']['adam_all_parameters'], 'Runtime optimizer differs')
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
        best = TransformerBaselineC().to(config['device'])
        best.load_state_dict(saved['state_dict'], strict=True)
        best.eval()
        with torch.no_grad():
            output = best(probe).cpu()
        require(torch.equal(output, saved['validation_logits'].cpu()), 'Best reload outputs differ')
        val, _, _, _ = evaluate(best, val_loader, config['device'])
        require(val['macro_f1'] == best_f1 and val['loss'] == best_loss, 'Best validation replay differs')
        last_copy = TransformerBaselineC().to(config['device'])
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
              formal_initialization_matches_precheck_initial=True,
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
