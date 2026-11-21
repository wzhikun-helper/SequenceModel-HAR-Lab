"""Recompute saved classification/selection evidence without running any model."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def verify(run):
    report = ROOT / 'reports' / run
    read = lambda n: json.loads((report / n).read_text(encoding='utf-8'))
    config, result, metrics = [read(n) for n in ['config.json', 'training_result.json', 'metrics.json']]
    with (report / 'training_history.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    best_f1, best_loss, best_epoch, stale = -1.0, float('inf'), 0, 0
    for epoch, row in enumerate(rows, 1):
        assert int(row['epoch']) == epoch
        assert int(row['train_samples']) == 6037 and int(row['train_batches']) == 95
        assert all(math.isfinite(float(row[k])) for k in ['training_loss', 'training_accuracy',
                   'validation_loss', 'validation_accuracy', 'validation_macro_f1', 'epoch_seconds'])
        assert float(row['epoch_seconds']) > 0 and 0 <= float(row['training_accuracy']) <= 1
        f1, loss = float(row['validation_macro_f1']), float(row['validation_loss'])
        update = f1 > best_f1 or (f1 == best_f1 and loss < best_loss)
        if update:
            best_f1, best_loss, best_epoch, stale = f1, loss, epoch, 0
        else:
            stale += 1
        assert (row['updated_best'] == 'True') == update
        assert int(row['best_epoch']) == best_epoch and int(row['early_stopping_count']) == stale
        assert float(row['learning_rate']) == config['learning_rate']
        assert stale < config['early_stopping_patience'] or epoch == len(rows)
    assert best_epoch == result['best_epoch'] and len(rows) == result['epochs_completed']
    assert len(rows) == config['max_epochs'] or stale == config['early_stopping_patience']
    assert best_f1 == result['best_validation']['macro_f1'] and best_loss == result['best_validation']['loss']
    with (report / 'test_predictions.csv').open(encoding='utf-8', newline='') as stream:
        predictions = list(csv.DictReader(stream))
    matrix = [[0] * 6 for _ in range(6)]
    for index, row in enumerate(predictions, 1):
        y, p = int(row['true_label_0based']), int(row['pred_label_0based'])
        assert int(row['official_test_row_1based']) == index and 0 <= y < 6 and 0 <= p < 6
        matrix[y][p] += 1
    support = [sum(row) for row in matrix]
    predicted = [sum(matrix[i][j] for i in range(6)) for j in range(6)]
    precision = [matrix[i][i] / predicted[i] if predicted[i] else 0 for i in range(6)]
    recall = [matrix[i][i] / support[i] if support[i] else 0 for i in range(6)]
    f1 = [2 * matrix[i][i] / (support[i] + predicted[i]) if support[i] + predicted[i] else 0 for i in range(6)]
    accuracy = sum(matrix[i][i] for i in range(6)) / len(predictions)
    assert len(predictions) == 2947 and matrix == metrics['confusion_matrix']
    assert abs(accuracy - metrics['accuracy']) < 1e-14 and abs(sum(f1) / 6 - metrics['macro_f1']) < 1e-14
    for key, values in [('precision', precision), ('recall', recall), ('f1', f1), ('support', support)]:
        assert all(abs(x - y) < 1e-14 for x, y in zip(values, metrics[key]))
    with np.load(ROOT / 'data/processed' / config['source_artifact'] / 'test_standardized.npz', allow_pickle=False) as data:
        assert [int(row['true_label_0based']) for row in predictions] == (data['y'] - 1).tolist()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    source = read('source_provenance.json')
    for path, expected in {**source['protected_inputs'], **source['source_sha256']}.items():
        assert sha(ROOT / path) == expected, path
    assert sha(report / 'config.json') == source['config_sha256']
    audit = json.loads((ROOT / 'reports/gru_baseline_preflight_20261121/audit_evidence.json').read_text(encoding='utf-8'))
    runtime = read('runtime_conditions.json')
    assert runtime['optimizer_defaults'] == audit['adam_all_parameters']
    for key, value in audit['cnn_config'].items():
        if key in config and key != 'input_shape':
            assert config[key] == value, key
    for key in ['best', 'last']:
        checkpoint = read('checkpoint_reload_verification.json')['checkpoints'][key]
        assert sha(ROOT / checkpoint['path']) == checkpoint['sha256']
    # Compare the two independent loader generators using saved data IDs only; no model or new scores.
    import torch
    from train_gru_baseline import loader as gru_loader
    from train_cnn_baseline_a import loader as cnn_loader
    cnn_config = audit['cnn_config']
    same_order = True
    for (cx, cy), (gx, gy) in zip(cnn_loader('train', cnn_config), gru_loader('train', config)):
        same_order &= torch.equal(cy, gy) and torch.equal(cx.permute(0, 2, 1), gx)
    assert same_order
    output = dict(status='PASS',selection_and_patience_replayed=True,epoch_coverage=True,
                  classification_metrics_recomputed_from_predictions=True,classification_tolerance=1e-14,
                  test_loss_scope='Recorded original forward loss, not reconstructed from argmax labels',
                  fixed_official_test_labels_match=True,common_configs_equal=True,
                  runtime_adam_matches_audit=True,all_first_epoch_batches_exactly_match_cnn_after_layout_swap=True,
                  input_and_source_hashes_match=True,best_last_checkpoint_hashes_match=True,
                  model_inference_performed=False)
    with (report / 'independent_verification.json').open('x', encoding='utf-8') as stream:
        json.dump(output, stream, indent=2)
    print(json.dumps(output))


if __name__ == '__main__':
    verify(sys.argv[1])
