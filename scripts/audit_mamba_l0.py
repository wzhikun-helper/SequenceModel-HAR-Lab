"""Print a read-only audit of the frozen inputs, baselines, and local runtime."""
import csv
import importlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

from har_contracts import validate_scaler_provenance, validate_window_shape, validate_labels, validate_channel_order
from train_cnn_baseline_a import sha

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
CNN = REPORTS / 'cnn_baseline_seed42_20261119_run01'
GRU = REPORTS / 'gru_baseline_seed42_20261121_run01'
TRANSFORMER = REPORTS / 'transformer_baseline_seed42_20261122_run01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check_hash(path, expected):
    actual = sha(path)
    if actual != expected:
        raise ValueError(f'SHA-256 mismatch: {path.relative_to(ROOT)}')
    return actual


def main():
    data = ROOT / 'data/processed/day01_data_20261026_run02_audit02'
    inputs = read(CNN / 'data_audit.json')['protected_sha256']
    if not inputs:
        raise ValueError('Empty input manifest')
    for name, expected in inputs.items():
        check_hash(ROOT / name, expected)
    download = read(REPORTS / 'day01_data_20261026_run02/download_provenance.json')
    check_hash(ROOT / download['relative_path'], download['sha256'])
    check_hash(ROOT / download['inner_archive']['path'], download['inner_archive']['sha256'])
    split = read(data / 'splits/split_metadata.json')
    scaler = read(data / 'scaler_train_only.json')
    validate_scaler_provenance(scaler, split)
    check_hash(data / 'splits/sample_manifest.csv', split['sample_manifest_sha256'])
    for part, count, subjects in [('train', 6037, 17), ('validation', 1315, 4), ('test', 2947, 9)]:
        with np.load(data / (part + '_standardized.npz'), allow_pickle=False) as arrays:
            validate_window_shape(arrays['X'].shape, count)
            validate_channel_order(arrays['channels'].tolist())
            validate_labels(arrays['y'], require_all=True)
            ids = sorted(set(arrays['subject'].tolist()))
            if (arrays['X'].dtype != np.float32 or arrays['y'].shape != (count,)
                    or not np.isfinite(arrays['X']).all() or len(ids) != subjects
                    or ids != split['splits'][part]['subjects']):
                raise ValueError(f'Data contract failure: {part}')
    cnn_config = read(CNN / 'config.json')
    common = ('seed', 'batch_size', 'optimizer', 'learning_rate', 'adam_betas', 'adam_eps',
              'weight_decay', 'max_epochs', 'early_stopping_patience', 'drop_last', 'loss',
              'selection_metric', 'tie_breaker', 'train_shuffle', 'num_workers', 'scheduler',
              'class_weights', 'augmentation', 'source_artifact')
    baselines = []
    for folder in (CNN, GRU, TRANSFORMER):
        config = read(folder / 'config.json')
        provenance = read(folder / 'source_provenance.json')
        check_hash(folder / 'config.json', provenance['config_sha256'])
        for key in common:
            if config[key] != cnn_config[key]:
                raise ValueError(f'{folder.name}: common config differs at {key}')
        result = read(folder / 'training_result.json')
        metrics = read(folder / 'test_metrics.json')
        reloaded = read(folder / 'checkpoint_reload_verification.json')
        best = reloaded.get('checkpoints', {}).get('best', reloaded)
        best_path = best['path'] if 'path' in best else best['checkpoint_path']
        check_hash(ROOT / best_path, best['sha256'])
        if (result['status'] != 'PASS' or reloaded['status'] != 'PASS'
                or metrics['checkpoint_sha256'] != best['sha256']
                or metrics['test_model_evaluation_passes'] != 1 or metrics['selection_used_test']):
            raise ValueError(f'{folder.name}: saved evaluation evidence disagrees')
        baselines.append(dict(run=folder.name, accuracy=metrics['accuracy'], macro_f1=metrics['macro_f1'],
                              loss=metrics['loss'], parameters=read(folder/'model_summary.json')['actual_parameters'],
                              best_epoch=result['best_epoch'], epochs=result['epochs_completed'],
                              config_sha256=provenance['config_sha256'], best_checkpoint_sha256=best['sha256']))
    ablation = REPORTS / 'cnn_ablation_20261122'
    with (ablation / 'results.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    expected_pairs = {(str(seed), group) for seed in (42, 43, 44) for group in 'ABC'}
    if len(rows) != 9 or {(row['seed'], row['group']) for row in rows} != expected_pairs:
        raise ValueError('Saved ablation is incomplete')
    for row in rows:
        source = ROOT / row['run']
        metrics = read(source / 'test_metrics.json')
        for key in ('accuracy', 'macro_f1', 'loss'):
            if float(row[key]) != metrics[key]:
                raise ValueError(f'{source.name}: archived {key} mismatch')
    for seed in (42, 43, 44):
        if read(ablation / f'independent_seed{seed}.json')['status'] != 'PASS':
            raise ValueError(f'Missing ablation verification for seed {seed}')
    imports = {}
    for package in ('mamba_ssm', 'selective_scan_cuda', 'causal_conv1d'):
        try:
            importlib.import_module(package)
            imports[package] = {'status': 'imported'}
        except (ImportError, OSError) as exc:
            imports[package] = {'status': 'failed', 'type': type(exc).__name__, 'message': str(exc)}
    print(json.dumps(dict(project_audit='PASS', git_head=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), source_zip_sha256=download['sha256'],
        inner_zip_sha256=download['inner_archive']['sha256'], frozen_inputs=inputs, splits=split['splits'],
        common_config={key: cnn_config[key] for key in common}, baselines=baselines, ablation_rows=len(rows),
        platform=platform.platform(), python=platform.python_version(), pytorch=torch.__version__,
        numpy=np.__version__, torch_cuda_build=torch.version.cuda, cuda_available=torch.cuda.is_available(),
        imports=imports), indent=2))


if __name__ == '__main__':
    main()
