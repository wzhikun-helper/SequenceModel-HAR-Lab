"""Train one paired CNN ablation run under the frozen A42 protocol."""
import argparse
import csv
import hashlib
import json
import time
import traceback

import torch
from torch import nn

from audit_cnn_ablation import AUDIT, ROOT
from cnn_metrics import improves
from har_contracts import NAMES
from har_lab.cnn_ablation import build_model
from train_cnn_baseline_a import evaluate, loader, read, relative, require, seed_all, sha, write
from train_gru_baseline import now, optimizer
from train_transformer_baseline import state_signature


def save(path, state):
    with path.open('xb') as stream:
        torch.save(state, stream)


def reload_model(path, variant):
    state = torch.load(path, map_location='cpu', weights_only=True)
    model = build_model(variant)
    model.load_state_dict(state['state_dict'], strict=True)
    return model.eval(), state


def initialized(config, variant):
    seed_all(config)
    reference = build_model('A')
    seed_all(config)
    model = build_model(variant)
    shared = reference.state_dict()
    require(all(torch.equal(value, model.state_dict()[key]) for key, value in shared.items()),
            'Shared layers differ from seed-matched A')
    return model, state_signature(reference)


def update(model, adam, X, y):
    adam.zero_grad(set_to_none=True)
    logits = model(X)
    require(logits.shape == (len(X), 6) and torch.isfinite(logits).all(), 'Invalid logits')
    loss = nn.functional.cross_entropy(logits, y)
    require(torch.isfinite(loss), 'Nonfinite loss')
    loss.backward()
    require(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()),
            'Invalid gradients')
    adam.step()
    return float(loss.detach()), int((logits.detach().argmax(1) == y).sum())


def preflight(config, variant, report, checkpoints):
    model, shared_sha = initialized(config, variant)
    initial_sha = state_signature(model)
    initial = {name: p.detach().clone() for name, p in model.named_parameters()}
    adam = optimizer(model, config)
    losses, gradients = [], []
    for index, (X, y) in enumerate(loader('train', config)):
        require(X.shape == (64, 9, 128) and y.dtype == torch.long and ((0 <= y) & (y < 6)).all(),
                'Invalid preflight batch')
        loss, _ = update(model, adam, X, y)
        losses.append(loss)
        nonzero = {name: int(torch.count_nonzero(p.grad)) for name, p in model.named_parameters()}
        require(sum(nonzero.values()) > 0, 'Zero total gradient')
        if variant != 'A':
            require(all(n > 0 for name, n in nonzero.items() if name.startswith('extra.')),
                    'Zero gradient in added tensor')
        gradients.append(nonzero)
        if index == 1:
            break
    require(len(losses) == 2, 'Missing preflight batches')
    updated = {name: not torch.equal(initial[name], p) for name, p in model.named_parameters()}
    require(all(updated.values()), 'A parameter tensor did not update')
    path = checkpoints / 'preflight.pt'
    save(path, {'state_dict': model.state_dict()})
    copy, _ = reload_model(path, variant)
    with torch.no_grad():
        require(torch.equal(model.eval()(X), copy(X)), 'Preflight reload mismatch')
    count = sum(p.numel() for p in model.parameters())
    added = sum(p.numel() for name, p in model.named_parameters() if name.startswith('extra.'))
    require((count, added) == ((27270, 0) if variant == 'A' else (31510, 4240)), 'Parameter count mismatch')
    write(report / 'preflight.json', dict(status='PASS', losses=losses, input_shape=[64, 9, 128],
          output_shape=[64, 6], gradients_nonzero=gradients, tensors_updated=updated,
          reload_max_abs_difference=0.0, checkpoint_sha256=sha(path), model=str(model),
          parameters=count, added_parameters=added, shared_initial_sha256=shared_sha,
          initial_state_sha256=initial_sha))
    return initial_sha, shared_sha, count


def save_csv(path, fields, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def train(report, checkpoints, variant, seed):
    started = now()
    audit = read(AUDIT / 'evidence.json')
    require(audit['status'] == 'PASS', 'Missing passing audit')
    protected = audit['protected_inputs']
    require(all(sha(ROOT / p) == h for p, h in protected.items()), 'Frozen input mismatch')
    config = dict(audit['common_config'], seed=seed, variant=variant, dataloader_seed=seed,
                  module_initialization='PyTorch Linear defaults after shared CNN construction',
                  adam_all_parameters=audit['adam_defaults'], amp=False, gradient_clipping=None,
                  dtype='float32', pin_memory=False, persistent_workers=False)
    write(report / 'config.json', config)
    config_sha = sha(report / 'config.json')
    write(report / 'provenance.json', dict(config_sha256=config_sha,
          audit_sha256=sha(AUDIT / 'evidence.json'), protected_inputs=protected,
          sources={name: sha(ROOT / name) for name in ['scripts/train_cnn_ablation.py',
              'src/har_lab/cnn_ablation.py', 'scripts/train_cnn_baseline_a.py', 'scripts/cnn_metrics.py',
              'scripts/train_gru_baseline.py', 'scripts/train_transformer_baseline.py',
              'src/har_lab/cnn_baseline_a.py', 'src/har_lab/cnn.py']}))
    init_sha, shared_sha, parameters = preflight(config, variant, report, checkpoints)
    model, formal_shared = initialized(config, variant)
    require(shared_sha == formal_shared and init_sha == state_signature(model), 'Preflight state carried over')
    if seed == 42:
        require(formal_shared == audit['reconstructed_a42_initial_sha256'], 'A42 reconstruction mismatch')
    adam = optimizer(model, config)
    training, validation = loader('train', config), loader('validation', config)
    probe = next(iter(validation))[0][:8]
    fields = ['epoch', 'training_loss', 'training_accuracy', 'validation_loss', 'validation_accuracy',
              'validation_macro_f1', 'learning_rate', 'epoch_seconds', 'best_epoch',
              'updated_best', 'early_stopping_count', 'train_samples', 'train_batches', 'order_sha256']
    best_f1, best_loss, best_epoch, stale = -1, float('inf'), 0, 0
    loop_start = time.perf_counter()
    with (report / 'training_history.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for epoch in range(1, config['max_epochs'] + 1):
            tick = time.perf_counter()
            order = hashlib.sha256()
            loss_sum = correct = count = batches = 0
            model.train()
            for X, y in training:
                order.update(X.numpy().tobytes())
                order.update(y.numpy().tobytes())
                loss, num_correct = update(model, adam, X, y)
                loss_sum += loss * len(y)
                correct += num_correct
                count += len(y)
                batches += 1
            require((count, batches, len(y)) == (6037, 95, 21), 'Incomplete epoch')
            val, _, _, _ = evaluate(model, validation, 'cpu')
            changed = improves(val['macro_f1'], val['loss'], best_f1, best_loss)
            if changed:
                best_f1, best_loss, best_epoch, stale = val['macro_f1'], val['loss'], epoch, 0
                best_path = checkpoints / f'epoch_{epoch:03d}.pt'
                with torch.no_grad():
                    best_probe = model(probe)
                save(best_path, dict(state_dict=model.state_dict(), epoch=epoch, probe=best_probe,
                                     seed=seed, config_sha256=config_sha))
            else:
                stale += 1
            row = dict(epoch=epoch, training_loss=loss_sum/count, training_accuracy=correct/count,
                       validation_loss=val['loss'], validation_accuracy=val['accuracy'],
                       validation_macro_f1=val['macro_f1'], learning_rate=adam.param_groups[0]['lr'],
                       epoch_seconds=time.perf_counter()-tick, best_epoch=best_epoch, updated_best=changed,
                       early_stopping_count=stale, train_samples=count, train_batches=batches,
                       order_sha256=order.hexdigest())
            writer.writerow(row)
            stream.flush()
            print(json.dumps(row), flush=True)
            if stale >= config['early_stopping_patience']:
                break
    loop_seconds = time.perf_counter()-loop_start
    best_alias, last = checkpoints / 'best_checkpoint.pt', checkpoints / 'last_checkpoint.pt'
    with best_alias.open('xb') as stream:
        stream.write(best_path.read_bytes())
    save(last, dict(state_dict=model.state_dict(), epoch=epoch, seed=seed, config_sha256=config_sha))
    best, state = reload_model(best_alias, variant)
    last_model, _ = reload_model(last, variant)
    with torch.no_grad():
        require(torch.equal(best(probe), state['probe']), 'Best probe reload mismatch')
        require(torch.equal(model.eval()(probe), last_model(probe)), 'Last probe reload mismatch')
    replay, _, _, _ = evaluate(best, validation, 'cpu')
    require((replay['macro_f1'], replay['loss']) == (best_f1, best_loss), 'Validation replay differs')
    checks = {name: dict(path=relative(path), sha256=sha(path), bytes=path.stat().st_size)
              for name, path in [('best', best_alias), ('last', last)]}
    write(report / 'checkpoint_reload_verification.json', dict(status='PASS', strict=True, weights_only=True,
          best_max_abs_difference=0.0, last_max_abs_difference=0.0, validation_replay_exact=True,
          checkpoints=checks, best_epoch_file=relative(best_path)))
    metrics, _, truth, pred = evaluate(best, loader('test', config), 'cpu')
    names = list(NAMES.values())
    metrics.update(activity_names=names, test_model_evaluation_passes=1, selection_used_test=False,
                   best_epoch=best_epoch, checkpoint_sha256=checks['best']['sha256'])
    write(report / 'test_metrics.json', metrics)
    save_csv(report / 'confusion_matrix.csv', ['true_activity'] + names,
             [[name] + row for name, row in zip(names, metrics['confusion_matrix'])])
    save_csv(report / 'test_predictions.csv',
             ['official_test_row_1based', 'true_label_0based', 'pred_label_0based'],
             [(i, y, p) for i, (y, p) in enumerate(zip(truth, pred), 1)])
    save_csv(report / 'per_class_metrics.csv', ['activity', 'precision', 'recall', 'f1', 'support'],
             [[name] + [metrics[k][i] for k in ['precision', 'recall', 'f1', 'support']]
              for i, name in enumerate(names)])
    require(all(sha(ROOT / p) == h for p, h in protected.items()), 'Input changed during training')
    write(report / 'training_result.json', dict(status='PASS', seed=seed, variant=variant, parameters=parameters,
          best_epoch=best_epoch, epochs_completed=epoch, final_stale_count=stale,
          stopped_early=stale >= config['early_stopping_patience'], best_validation=replay,
          shared_initial_sha256=formal_shared, formal_initial_sha256=init_sha, dataloader_seed=seed,
          started_at=started, finished_at=now(), epoch_loop_seconds=loop_seconds))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices='ABC')
    parser.add_argument('seed', type=int, choices=[42, 43, 44])
    parser.add_argument('run')
    args = parser.parse_args()
    require((args.variant, args.seed) != ('A', 42), 'Reuse archived A42')
    require(args.run.replace('_', '').isalnum(), 'Invalid run identifier')
    report = ROOT / 'reports/cnn_ablation_20261122' / args.run
    checkpoints = ROOT / 'checkpoints' / args.run
    require(not report.exists() and not checkpoints.exists(), 'Run already exists')
    report.mkdir(parents=True)
    checkpoints.mkdir(parents=True)
    try:
        train(report, checkpoints, args.variant, args.seed)
    except Exception:
        write(report / 'failure.json', dict(status='FAIL', timestamp=now(), traceback=traceback.format_exc()))
        raise


if __name__ == '__main__':
    main()
