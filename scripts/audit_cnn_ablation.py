"""Audit historical A42 and freeze inputs before running the ablation."""
import ast
import csv
import json
import platform
import subprocess
import sys

import numpy as np
import torch

from train_cnn_baseline_a import ROOT, DATA, seed_all, sha, read, write, require
from har_lab.cnn_baseline_a import CNNBaselineA
from har_contracts import validate_scaler_provenance, validate_window_shape, validate_labels, validate_channel_order
from train_transformer_baseline import state_signature

OLD = ROOT / 'reports/cnn_baseline_seed42_20261119_run01'
AUDIT = ROOT / 'reports/cnn_ablation_audit_20261122'
SUITE = ROOT / 'reports/cnn_ablation_20261122'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main(remote_head):
    require(not AUDIT.exists(), 'Audit already exists')
    require(git('status', '--porcelain', '--untracked-files=all') in
            ['', '?? scripts/audit_cnn_ablation.py'], 'Unexpected tracked/untracked changes')
    require(git('branch', '--show-current') == 'main' and git('rev-parse', 'HEAD') == remote_head,
            'Main differs from the verified remote')
    require(git('remote', 'get-url', 'origin') == 'https://github.com/wzhikun-helper/SequenceModel-HAR-Lab.git',
            'Unexpected origin')
    config, prov, env = (read(OLD / name) for name in
                         ['config.json', 'source_provenance.json', 'environment.json'])
    require(sha(OLD / 'config.json') == prov['config_sha256'], 'Historical config SHA mismatch')
    for name, expected in prov['executed_sources'].items():
        info = prov.get('postrun_source_formatting', {}).get(name)
        if info:
            snapshot = ROOT / info['executed_snapshot']
            require(sha(snapshot) == expected and sha(ROOT / name) == info['published_sha256'], name)
            require(ast.dump(ast.parse(snapshot.read_text(encoding='utf-8'))) ==
                    ast.dump(ast.parse((ROOT / name).read_text(encoding='utf-8'))), name)
        else:
            require(sha(ROOT / name) == expected, name)
    current = dict(python=sys.version, interpreter=sys.executable, platform=platform.platform(),
                   pytorch=torch.__version__, numpy=np.__version__, cuda_build=torch.version.cuda,
                   cuda_available=torch.cuda.is_available(), device='cpu')
    require(current == env and torch.get_default_dtype() == torch.float32, 'Runtime mismatch')
    protected = read(OLD / 'data_audit.json')['protected_sha256']
    for name, expected in protected.items():
        require(sha(ROOT / name) == expected, name)
    split = read(DATA / 'splits/split_metadata.json')
    scaler = read(DATA / 'scaler_train_only.json')
    validate_scaler_provenance(scaler, split)
    require(sha(DATA / 'splits/sample_manifest.csv') == split['sample_manifest_sha256'], 'Manifest SHA')
    for part, count, subjects in [('train', 6037, 17), ('validation', 1315, 4), ('test', 2947, 9)]:
        with np.load(DATA / (part + '_standardized.npz'), allow_pickle=False) as data:
            validate_window_shape(data['X'].shape, count)
            validate_channel_order(data['channels'].tolist())
            validate_labels(data['y'], require_all=True)
            require(data['X'].dtype == np.float32 and np.isfinite(data['X']).all(), part)
            ids = sorted(set(data['subject'].tolist()))
            require(len(ids) == subjects and ids == split['splits'][part]['subjects'], part)
    checkpoint = read(OLD / 'checkpoint_reload_verification.json')
    require(sha(ROOT / checkpoint['checkpoint_path']) == checkpoint['sha256'], 'Historical checkpoint SHA')
    historical_logs = read(OLD / 'local_log_manifest.json')
    for name, info in historical_logs.items():
        require(sha(ROOT / name) == info['sha256'], name)
    command = read(ROOT / 'logs' / OLD.name / '04_training.json')
    with (OLD / 'training_history.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    log = (ROOT / command['log']).read_text(encoding='utf-8').splitlines()
    epochs = [json.loads(line) for line in log if line.startswith('{"epoch"')]
    require(len(rows) == len(epochs) == 15 and command['exit_code'] == 0, 'A42 execution evidence')
    for row, epoch in zip(rows, epochs):
        require(all(str(epoch[key]) == value for key, value in row.items()), 'A42 history/stdout mismatch')
    require(read(OLD / 'independent_result_verification.json')['status'] == 'PASS', 'A42 verification')
    seed_all(config)
    initial = state_signature(CNNBaselineA())
    defaults = torch.optim.Adam(CNNBaselineA().parameters(), lr=config['learning_rate'],
                               betas=tuple(config['adam_betas']), eps=config['adam_eps'],
                               weight_decay=config['weight_decay']).defaults
    frozen = {path: sha(ROOT / path) for path in git('ls-files').splitlines()}
    AUDIT.mkdir()
    write(AUDIT / 'evidence.json', dict(status='PASS', base_head=remote_head, common_config=config,
          environment=current, protected_inputs=protected, frozen_tracked=frozen, split=split,
          historical_checkpoint=checkpoint, historical_logs=historical_logs, historical_command=command,
          cnn_config_sha256=prov['config_sha256'], adam_defaults=defaults,
          reconstructed_a42_initial_sha256=initial, a42_initial_hash_contemporaneous=False,
          a42_last_available=False, a42_reused_without_evaluation=True))
    print('Audit PASS. A42 init reconstructed from original constructor and seed:', initial)


if __name__ == '__main__':
    main(sys.argv[1])
