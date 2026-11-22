"""Recompute metrics and replay the paired loader and validation selection."""
import csv
import hashlib
import math
import sys

import numpy as np
import torch

from audit_cnn_ablation import AUDIT, DATA, OLD, ROOT, SUITE
from train_cnn_baseline_a import loader, read, sha, write


def rows(folder, name):
    with (folder / name).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def verify_model(folder, group, seed):
    config = read(folder / 'config.json')
    result = read(folder / 'training_result.json')
    metric = read(folder / 'test_metrics.json')
    history = rows(folder, 'training_history.csv')
    stale, best, best_score = 0, 0, (-1, float('-inf'))
    for epoch, row in enumerate(history, 1):
        assert int(row['epoch']) == epoch and int(row['train_samples']) == 6037
        assert int(row['train_batches']) == 95 and float(row['learning_rate']) == 0.001
        score = float(row['validation_macro_f1']), -float(row['validation_loss'])
        assert all(math.isfinite(v) for v in (*score, float(row['training_loss'])))
        improvement = score > best_score
        if improvement:
            best, best_score, stale = epoch, score, 0
        else:
            stale += 1
        assert (row['updated_best'] == 'True') == improvement
        assert int(row['best_epoch']) == best and int(row['early_stopping_count']) == stale
        assert stale < 8 or epoch == len(history)
    assert best == result['best_epoch'] == metric['best_epoch']
    assert len(history) == result['epochs_completed'] and (stale == 8 or len(history) == 30)
    assert metric['test_model_evaluation_passes'] == 1 and not metric['selection_used_test']
    with np.load(DATA / 'test_standardized.npz', allow_pickle=False) as data:
        official = (data['y']-1).tolist()
    predictions = rows(folder, 'test_predictions.csv')
    matrix = [[0]*6 for _ in range(6)]
    assert len(predictions) == len(official) == 2947
    for idx, (record, true) in enumerate(zip(predictions, official), 1):
        predicted = int(record['pred_label_0based'])
        assert int(record['official_test_row_1based']) == idx and int(record['true_label_0based']) == true
        assert 0 <= predicted < 6
        matrix[true][predicted] += 1
    assert matrix == metric['confusion_matrix']
    accuracy = sum(matrix[i][i] for i in range(6))/2947
    f1 = []
    for i in range(6):
        support = sum(matrix[i])
        predicted = sum(row[i] for row in matrix)
        tp = matrix[i][i]
        precision = tp/predicted if predicted else 0
        recall = tp/support if support else 0
        f1.append(2*tp/(support+predicted) if support+predicted else 0)
        for key, value in [('precision', precision), ('recall', recall), ('f1', f1[-1]), ('support', support)]:
            assert abs(metric[key][i]-value) < 1e-14
    assert abs(accuracy-metric['accuracy']) < 1e-14
    assert abs(sum(f1)/6-metric['macro_f1']) < 1e-14
    reload = read(folder / 'checkpoint_reload_verification.json')
    assert reload['status'] == 'PASS'
    if (group, seed) != ('A', 42):
        prov = read(folder / 'provenance.json')
        assert sha(folder / 'config.json') == prov['config_sha256']
        assert sha(AUDIT / 'evidence.json') == prov['audit_sha256']
        for path, expected in {**prov['sources'], **prov['protected_inputs']}.items():
            assert sha(ROOT/path) == expected, path
        for item in reload['checkpoints'].values():
            assert sha(ROOT/item['path']) == item['sha256']
        assert metric['checkpoint_sha256'] == reload['checkpoints']['best']['sha256']
        assert reload['best_max_abs_difference'] == reload['last_max_abs_difference'] == 0
        assert reload['validation_replay_exact']
    else:
        assert sha(ROOT/reload['checkpoint_path']) == reload['sha256'] == metric['checkpoint_sha256']
    return config, result, [row.get('order_sha256') for row in history]


def main(seed):
    audit = read(AUDIT / 'evidence.json')
    actual = {}
    for group in 'ABC':
        folder = OLD if (group, seed) == ('A', 42) else SUITE / f'cnn_ablation_{group}_seed{seed}_20261122_run01'
        config, result, orders = verify_model(folder, group, seed)
        assert all(config[key] == (seed if key == 'seed' else value)
                   for key, value in audit['common_config'].items())
        actual[group] = dict(shared_initial=result.get('shared_initial_sha256',
                             audit['reconstructed_a42_initial_sha256']), epochs=len(orders), orders=orders)
    assert len({value['shared_initial'] for value in actual.values()}) == 1
    # Reconstruct A's independent seeded loader even where historical A42 lacks order hashes.
    torch.set_num_threads(2)
    expected_orders = []
    batches = loader('train', dict(audit['common_config'], seed=seed))
    for _ in range(max(value['epochs'] for value in actual.values())):
        digest = hashlib.sha256()
        for X, y in batches:
            digest.update(X.numpy().tobytes())
            digest.update(y.numpy().tobytes())
        expected_orders.append(digest.hexdigest())
    for group, item in actual.items():
        expected = expected_orders[:item['epochs']]
        if (group, seed) == ('A', 42):
            item['orders'] = expected
            item['order_evidence'] = 'Reconstructed from original loader and seed'
        else:
            assert item['orders'] == expected
            item['order_evidence'] = 'Observed in training; exact match to independent replay'
    write(SUITE / f'independent_seed{seed}.json', dict(status='PASS', seed=seed, runs=actual,
          confusion_and_classification_metrics_recomputed=True, validation_selection_replayed=True,
          test_loss_scope='Original cross-entropy; cannot recompute from class predictions alone',
          model_inference_performed=False, exact_same_initial_shared_weights_for_new_runs=True))
    print(f'Seed {seed}: paired initialization, loader order, checkpoint and saved metrics verified')


if __name__ == '__main__':
    main(int(sys.argv[1]))
