"""Real train-window forward/backward/checkpoint acceptance; no optimizer or metrics."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from har_lab.cnn import MinimalHARConvNet, parameter_calculation, targets_from_official
from har_contracts import (CHANNELS, NAMES, validate_channel_order, validate_labels,
                           validate_scaler_provenance, validate_window_shape)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args):
    for value in (args.run_id, args.source_run):
        require(re.fullmatch(r'[A-Za-z0-9_]+', value) is not None, 'Unsafe run ID')
    output = ROOT / 'reports' / args.run_id
    checkpoints = ROOT / 'checkpoints' / args.run_id
    require(not output.exists() and not checkpoints.exists(), 'Use a new run ID; outputs already exist')
    output.mkdir(parents=True)
    checkpoints.mkdir(parents=True)
    source_report = ROOT / 'reports' / args.source_run
    processed = ROOT / 'data' / 'processed' / (args.source_run + '_audit02')
    # Anchor to the already successful independent Day 01 verification.
    independent = read(source_report / 'independent_verification.json')
    require(independent['status'] == 'PASS', 'Day 01 independent verification must have passed')
    require(independent['artifact_run'] == processed.name, 'Verification artifact ID mismatch')
    metadata = read(processed / 'splits/split_metadata.json')
    scaler = read(processed / 'scaler_train_only.json')
    validate_scaler_provenance(scaler, metadata)
    require(digest(processed / 'splits/sample_manifest.csv') == metadata['sample_manifest_sha256'],
            'Manifest identity mismatch')
    # Verify current raw files and train arrays against the verified source, not just a stale PASS flag.
    originals = read(source_report / 'audit02/original_files_before.json')
    require(len(originals) == 29 and all(digest(ROOT / p) == h for p, h in originals.items()),
            'Original raw-file hashes changed')
    protected = [p for p in processed.rglob('*') if p.is_file()] + [ROOT / p for p in originals]
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in protected}
    provenance = read(source_report / 'download_provenance.json')
    raw = ROOT / provenance['dataset_root'] / 'train'
    with np.load(processed / 'train_standardized.npz', allow_pickle=False) as data:
        X, y, subjects, rows = [data[k] for k in ('X', 'y', 'subject', 'official_row_1based')]
        validate_window_shape(X.shape, metadata['splits']['train']['n_windows'])
        validate_channel_order(data['channels'].tolist())
        validate_labels(y, require_all=True)
        require(X.dtype == np.float32 and np.isfinite(X).all(), 'Invalid saved train values')
        require(y.shape == subjects.shape == rows.shape == (len(X),), 'Metadata dimensions mismatch')
        require(sorted(set(subjects.tolist())) == metadata['splits']['train']['subjects'], 'Train subjects mismatch')
        official_y = np.loadtxt(raw / 'y_train.txt', dtype=np.int64)
        official_s = np.loadtxt(raw / 'subject_train.txt', dtype=np.int64)
        require(((rows >= 1) & (rows <= len(official_y))).all(), 'Invalid original row')
        require(np.array_equal(y, official_y[rows - 1]) and np.array_equal(subjects, official_s[rows - 1]),
                'Saved labels/subjects do not match official rows')
        mean, std = np.array(scaler['mean']), np.array(scaler['std'])
        # Independently check all final-train standardized values without fitting anything.
        for c, channel in enumerate(CHANNELS):
            values = np.loadtxt(raw / 'Inertial Signals' / (channel + '_train.txt'), dtype=np.float64)
            expected = ((values[rows - 1] - mean[c]) / std[c]).astype(np.float32)
            require(np.array_equal(X[:, :, c], expected), 'Saved standardized channel changed: ' + channel)
        selected = [int(np.flatnonzero(y == label)[0]) for label in range(1, 7)]
        batch = torch.from_numpy(X[selected].copy()).permute(0, 2, 1).contiguous()
        official_labels = torch.from_numpy(y[selected].copy()).long()
    targets = targets_from_official(official_labels)
    torch.set_num_threads(1)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    model = MinimalHARConvNet().cpu()
    initial = {k: v.detach().clone() for k, v in model.state_dict().items()}
    shapes = {'saved_batch': [6, 128, 9], 'model_input': list(batch.shape)}
    handles = []
    for name, layer in model.named_children():
        def capture(module, inputs, result, name=name):
            shapes[name] = list(result.shape)
        handles.append(layer.register_forward_hook(capture))
    model.train()
    logits = model(batch)
    for handle in handles:
        handle.remove()
    require(list(logits.shape) == [6, 6] and torch.isfinite(logits).all(), 'Invalid logits')
    loss = torch.nn.CrossEntropyLoss()(logits, targets)
    require(torch.isfinite(loss).item(), 'Nonfinite loss')
    loss.backward()
    gradients = {}
    for name, parameter in model.named_parameters():
        grad = parameter.grad
        require(grad is not None and torch.isfinite(grad).all().item(), 'Missing/nonfinite gradient: ' + name)
        gradients[name] = {'shape': list(grad.shape), 'finite': True,
                           'l2_norm': float(grad.norm()), 'max_abs': float(grad.abs().max()),
                           'nonzero_elements': int(torch.count_nonzero(grad))}
        require(gradients[name]['nonzero_elements'] > 0, 'Entire gradient is zero: ' + name)
    unchanged = all(torch.equal(initial[k], v) for k, v in model.state_dict().items())
    require(unchanged, 'Parameters changed despite no optimizer')
    calculated = parameter_calculation()
    actual = sum(p.numel() for p in model.parameters())
    require(actual == calculated['total'], 'Parameter count mismatch')
    actual_layers = {name: sum(p.numel() for p in getattr(model, name).parameters())
                     for name in calculated['layers']}
    require(actual_layers == calculated['layers'], 'Layer parameter count mismatch')
    checkpoint = checkpoints / 'untrained_state_dict.pt'
    with checkpoint.open('xb') as stream:
        torch.save(model.state_dict(), stream)
    loaded = MinimalHARConvNet().cpu()
    # Only this locally created state_dict is loaded, using the restricted weights loader.
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    loaded.load_state_dict(state, strict=True)
    model.eval()
    loaded.eval()
    with torch.no_grad():
        before_output, after_output = model(batch), loaded(batch)
    difference = float((before_output - after_output).abs().max())
    require(torch.equal(before_output, after_output), 'Checkpoint output differs')
    require(all(torch.equal(initial[k], v) for k, v in loaded.state_dict().items()), 'Reload weights differ')
    after = {p: digest(ROOT / p) for p in before}
    require(before == after, 'Day 01 inputs changed during smoke verification')
    hashes = {p: digest(ROOT / p) for p in [
        'src/har_lab/cnn.py', 'scripts/day02_cnn_smoke.py', 'scripts/har_contracts.py']}
    result = {
        'status': 'PASS', 'run_id': args.run_id,
        'timestamp': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
        'scope': 'One real train batch, one forward and backward; no optimizer, updates, training loop or accuracy.',
        'base_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'executed_source_sha256': hashes, 'source_state': 'Working-tree code hashed above, before archival commit',
        'environment': {'python': platform.python_version(), 'pytorch': torch.__version__,
                        'numpy': np.__version__, 'platform': platform.platform(), 'device': 'cpu',
                        'cuda_available': torch.cuda.is_available(), 'torch_cuda_build': torch.version.cuda,
                        'threads': torch.get_num_threads(), 'seed': args.seed, 'deterministic_algorithms': True},
        'architecture': {'input': '[B,9,128]', 'convolutions': [[9, 64], [64, 128]],
                         'kernel_size': 3, 'stride': 1, 'padding': 1, 'bias': True,
                         'activation': 'ReLU after each convolution', 'pool': 'AdaptiveAvgPool1d(1)',
                         'output': '6 raw logits; no softmax before CrossEntropyLoss'},
        'data': {'artifact_id': processed.name, 'split': 'train', 'selection': 'First saved train row of each official class 1..6',
                 'subjects_unchanged': True, 'new_scaler_fit': False, 'channels': CHANNELS,
                 'sample_manifest_sha256': metadata['sample_manifest_sha256'],
                 'samples': [{'train_index_0based': i, 'official_row_1based': int(rows[i]),
                              'subject_id': int(subjects[i]), 'official_label': int(y[i]),
                              'loss_target': int(y[i]) - 1, 'activity': NAMES[int(y[i])]} for i in selected],
                 'official_to_loss_label': {str(i): i - 1 for i in range(1, 7)},
                 'all_train_values_rechecked_against_raw_and_saved_scaler': True,
                 'input_files_sha256_before_and_after_equal': True, 'protected_files_sha256': before},
        'tensor_shapes': shapes, 'parameters': {'calculated': calculated, 'actual': actual, 'actual_layers': actual_layers},
        'cross_entropy_loss': float(loss.detach()), 'gradients': gradients,
        'backward_calls': 1, 'optimizer_steps': 0, 'parameters_unchanged': unchanged,
        'checkpoint': {'path': checkpoint.relative_to(ROOT).as_posix(), 'sha256': digest(checkpoint),
                       'bytes': checkpoint.stat().st_size, 'state': 'Untrained initial weights, no gradients/optimizer',
                       'strict_load': True, 'weights_only': True, 'eval_max_abs_difference': difference,
                       'outputs_exactly_equal': True, 'weights_equal_initial': True}}
    with (output / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'shapes': shapes, 'parameters': actual,
                      'loss': result['cross_entropy_loss'], 'reload_max_abs_difference': difference}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    parser.add_argument('--source-run', default='day01_repro_20261031_run01')
    parser.add_argument('--seed', type=int, default=20261111)
    run(parser.parse_args())
