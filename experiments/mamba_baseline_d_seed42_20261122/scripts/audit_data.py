"""Check an official UCI rebuild against the historical source and data protocol."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main(project, run, artifact, output):
    historical = json.loads((project / 'reports/mamba_l0_20261122/project_audit.json').read_text())
    download = json.loads((project / 'reports' / run / 'download_provenance.json').read_text())
    processed = project / 'data/processed' / artifact
    raw = project / download['dataset_root']
    outer = sha(project / download['relative_path'])
    inner = sha(project / download['inner_archive']['path'])
    require(outer == historical['source_zip_sha256'], 'Outer source archive SHA-256 changed')
    require(inner == historical['inner_zip_sha256'], 'Inner source archive SHA-256 changed')
    raw_count = 0
    marker = '/extracted/UCI HAR Dataset/'
    frozen = {}
    for key, expected in historical['frozen_inputs'].items():
        if marker in key:
            require(sha(raw / key.split(marker, 1)[1]) == expected, f'Raw source SHA-256 changed: {key}')
            raw_count += 1
        elif key.endswith('.npz') or key.endswith('/scaler_train_only.json'):
            frozen[Path(key).name] = expected

    rebuilt = {name: sha(processed / name) for name in frozen}
    channels = [f'{kind}_{axis}' for kind in ('body_acc', 'body_gyro', 'total_acc') for axis in 'xyz']
    raw_signals, raw_labels, raw_subjects = {}, {}, {}
    for source in ('train', 'test'):
        directory = raw / source
        raw_signals[source] = np.stack([
            np.loadtxt(directory / 'Inertial Signals' / f'{c}_{source}.txt') for c in channels
        ], axis=2)
        raw_labels[source] = np.loadtxt(directory / f'y_{source}.txt', dtype=np.int64)
        raw_subjects[source] = np.loadtxt(directory / f'subject_{source}.txt', dtype=np.int64)

    train_fp64 = raw_signals['train'][np.isin(raw_subjects['train'], historical['splits']['train']['subjects'])]
    local_scaler = json.loads((processed / 'scaler_train_only.json').read_text())
    public_scaler = json.loads((project / 'docs/day01/standardization_train_only.json').read_text())
    mean, std = train_fp64.mean(axis=(0, 1)), train_fp64.std(axis=(0, 1), ddof=0)
    for saved in (local_scaler, public_scaler):
        np.testing.assert_array_equal(mean, saved['mean'])
        np.testing.assert_array_equal(std, saved['std'])

    all_subjects = set()
    for split, expectation in historical['splits'].items():
        source = expectation['official_source']
        select = np.isin(raw_subjects[source], expectation['subjects'])
        subjects = set(raw_subjects[source][select].tolist())
        require(not (subjects & all_subjects) and sorted(subjects) == expectation['subjects'],
                f'Subject contract failed: {split}')
        all_subjects.update(subjects)
        with np.load(processed / f'{split}_standardized.npz', allow_pickle=False) as saved:
            expected = ((raw_signals[source][select] - mean) / std).astype(np.float32)
            require(saved['X'].shape == (expectation['n_windows'], 128, 9)
                    and saved['X'].dtype == np.float32 and np.isfinite(saved['X']).all(),
                    f'Window contract failed: {split}')
            np.testing.assert_array_equal(saved['X'], expected)
            np.testing.assert_array_equal(saved['channels'], channels)
            np.testing.assert_array_equal(saved['y'], raw_labels[source][select])
            np.testing.assert_array_equal(saved['subject'], raw_subjects[source][select])
            np.testing.assert_array_equal(saved['official_row_1based'], np.where(select)[0] + 1)

    with output.open('x', encoding='utf-8') as stream:
        json.dump(dict(status='PASS', source_zip_sha256=outer, inner_zip_sha256=inner,
                       raw_member_hash_matches=raw_count, historical_sha256=frozen,
                       rebuilt_sha256=rebuilt, byte_matches={k: frozen[k] == rebuilt[k] for k in frozen},
                       train_only_scaler_equals_historical=True,
                       all_normalized_fp32_values_verified_against_raw=True,
                       labels_subjects_and_order_verified=True), stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('run')
    parser.add_argument('artifact')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.project, args.run, args.artifact, args.output)
