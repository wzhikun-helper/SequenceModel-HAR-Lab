"""UCI HAR data audit and subject-disjoint preprocessing. No model operations."""
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import traceback

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = [f'{group}_{axis}' for group in ('body_acc', 'body_gyro', 'total_acc') for axis in 'xyz']
NAMES = {1: 'WALKING', 2: 'WALKING_UPSTAIRS', 3: 'WALKING_DOWNSTAIRS',
         4: 'SITTING', 5: 'STANDING', 6: 'LAYING'}


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def safe(path):
    path = Path(os.path.abspath(path))
    path.relative_to(ROOT)
    for part in [path, *path.parents]:
        if part.exists() and (part.is_symlink() or (getattr(part.lstat(), 'st_file_attributes', 0) & 1024)):
            raise ValueError('Linked/reparse path rejected: ' + str(part))
        if part == ROOT:
            break
    return path


def jwrite(path, value):
    safe(path)
    payload = json.dumps(value, ensure_ascii=False, indent=2)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)


def cwrite(path, fields, rows):
    safe(path)
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(run, attempt='audit'):
    if not run.replace('_', '').replace('-', '').isalnum():
        raise ValueError('Unsafe run ID')
    if not attempt.replace('_', '').isalnum():
        raise ValueError('Unsafe attempt ID')
    provenance = json.loads((ROOT / 'reports' / run / 'download_provenance.json').read_text(encoding='utf-8'))
    if provenance['status'] != 'COMPLETE':
        raise ValueError('Official download did not complete')
    dataset = safe(ROOT / provenance['dataset_root'])
    report = safe(ROOT / 'reports' / run / attempt)
    artifact_run = run if attempt == 'audit' else run + '_' + attempt
    processed = safe(ROOT / 'data' / 'processed' / artifact_run)
    for folder in [report, processed]:
        folder.mkdir(parents=True, exist_ok=False)
    for sub in ['splits', 'examples']:
        (processed / sub).mkdir()
    status = {'run_id': run, 'artifact_run': artifact_run, 'attempt': attempt,
              'processed_directory': processed.relative_to(ROOT).as_posix(),
              'started_at': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
              'python': platform.python_version(), 'numpy': np.__version__, 'stages': {},
              'channels': CHANNELS, 'layout': 'N, time=128, channels=9', 'labels': NAMES,
              'split_rule': 'Sort official training subject IDs ascending; reserve the first 4 for validation; all other official training subjects for training. Official test rows/subjects unchanged. No random or label-based selection.'}
    with (ROOT / 'logs' / (artifact_run + '_audit.log')).open('x', encoding='utf-8', buffering=1) as log:
        def say(message):
            print(message, flush=True)
            log.write(message + '\n')
        try:
            original_files = sorted(p for p in dataset.rglob('*') if p.is_file())
            raw_before = {p.relative_to(ROOT).as_posix(): sha(p) for p in original_files}
            archive_manifest = json.loads((ROOT / 'reports' / run / 'archive_integrity.json').read_text(encoding='utf-8'))
            archive_files = {entry['path']: entry['sha256'] for archive in archive_manifest for entry in archive['files']}
            assert all(archive_files.get(name) == digest for name, digest in raw_before.items())
            assert len(raw_before) > 0
            jwrite(report / 'original_files_before.json', raw_before)
            status['stages']['archive_to_raw_hashes'] = 'PASS'
            labels = dict((int(line.split()[0]), line.split()[1]) for line in (dataset / 'activity_labels.txt').read_text().splitlines())
            assert labels == NAMES
            features = (dataset / 'features.txt').read_text().splitlines()
            assert len(features) == 561
            official = {}
            channel_rows = []
            for partition, expected in [('train', 7352), ('test', 2947)]:
                part = dataset / partition
                y = np.loadtxt(part / f'y_{partition}.txt', dtype=np.int64)
                subjects = np.loadtxt(part / f'subject_{partition}.txt', dtype=np.int64)
                assert y.shape == subjects.shape == (expected,)
                assert set(y.tolist()) == set(NAMES)
                assert np.all((subjects >= 1) & (subjects <= 30))
                feature_matrix = np.loadtxt(part / f'X_{partition}.txt', dtype=np.float64)
                assert feature_matrix.shape == (expected, 561) and np.isfinite(feature_matrix).all()
                feature_info = {'shape': list(feature_matrix.shape), 'minimum': float(feature_matrix.min()),
                                'maximum': float(feature_matrix.max()), 'finite': True}
                del feature_matrix
                expected_names = {f'{channel}_{partition}.txt' for channel in CHANNELS}
                actual_names = {p.name for p in (part / 'Inertial Signals').iterdir() if p.is_file()}
                assert actual_names == expected_names, (actual_names, expected_names)
                arrays = []
                for channel in CHANNELS:
                    path = part / 'Inertial Signals' / f'{channel}_{partition}.txt'
                    values = np.loadtxt(path, dtype=np.float64)
                    assert values.shape == (expected, 128) and np.isfinite(values).all()
                    arrays.append(values)
                    channel_rows.append({'official_split': partition, 'channel': channel,
                                         'rows': expected, 'samples_per_window': 128, 'finite': True,
                                         'min': float(values.min()), 'max': float(values.max()),
                                         'unit': 'rad/s' if 'gyro' in channel else 'g',
                                         'sha256': raw_before[path.relative_to(ROOT).as_posix()]})
                x = np.stack(arrays, axis=-1)
                del arrays
                assert x.shape == (expected, 128, 9)
                official[partition] = {'x': x, 'y': y, 'subject': subjects,
                                       'row': np.arange(1, expected + 1), 'features': feature_info}
                say(f'Official {partition}: X={x.shape}, y={y.shape}, subjects={np.unique(subjects).tolist()}, finite=True')
            status['official'] = {name: {'windows': len(data['y']), 'subjects': np.unique(data['subject']).tolist(),
                                         'signal_shape': list(data['x'].shape), 'features_561': data['features']}
                                  for name, data in official.items()}
            assert not set(official['train']['subject']) & set(official['test']['subject'])
            assert set(official['train']['subject']) | set(official['test']['subject']) == set(range(1, 31))
            assert len(np.unique(official['train']['subject'])) == 21
            assert len(np.unique(official['test']['subject'])) == 9
            cwrite(report / 'channel_file_audit.csv', list(channel_rows[0]), channel_rows)
            status['stages']['official_schema_all_18_signals'] = 'PASS'

            # Rule fixed before reading class counts; labels do not choose validation subjects.
            validation_subjects = np.unique(official['train']['subject'])[:4]
            train_mask = ~np.isin(official['train']['subject'], validation_subjects)
            selections = {'train': ('train', train_mask), 'validation': ('train', ~train_mask),
                          'test': ('test', np.ones(len(official['test']['y']), dtype=bool))}
            split_data = {}
            manifest_rows = []
            distributions = []
            subject_rows = []
            status['splits'] = {}
            for split, (source, mask) in selections.items():
                data = {key: official[source][key][mask] for key in ['x', 'y', 'subject', 'row']}
                split_data[split] = data
                ids = np.unique(data['subject']).tolist()
                counts = {NAMES[label]: int(np.sum(data['y'] == label)) for label in NAMES}
                assert all(count > 0 for count in counts.values())
                status['splits'][split] = {'official_source': source, 'subjects': ids,
                                           'n_subjects': len(ids), 'n_windows': len(data['y']), 'class_counts': counts}
                for split_index, (y, subject, row) in enumerate(zip(data['y'], data['subject'], data['row'])):
                    manifest_rows.append({'sample_id': f'{source}:{row:06d}', 'split': split,
                                          'split_index_0based': split_index, 'official_split': source,
                                          'official_row_1based': int(row), 'subject_id': int(subject),
                                          'activity_id': int(y), 'activity_name': NAMES[int(y)]})
                for label in NAMES:
                    distributions.append({'split': split, 'activity_id': label,
                                          'activity_name': NAMES[label], 'windows': counts[NAMES[label]]})
                for subject in ids:
                    for label in NAMES:
                        count = int(np.sum((data['subject'] == subject) & (data['y'] == label)))
                        subject_rows.append({'split': split, 'subject_id': subject, 'activity_id': label,
                                             'activity_name': NAMES[label], 'windows': count})
                say(f'{split}: subjects={ids}; windows={len(data["y"])}; classes={counts}')
            id_sets = {name: set(data['subject']) for name, data in split_data.items()}
            assert not (id_sets['train'] & id_sets['validation'] or id_sets['train'] & id_sets['test'] or id_sets['validation'] & id_sets['test'])
            assert len(manifest_rows) == 10299
            assert len({row['sample_id'] for row in manifest_rows}) == 10299
            assert sum(len(data['y']) for key, data in split_data.items() if key != 'test') == 7352
            assert np.array_equal(split_data['test']['row'], np.arange(1, 2948))
            split_csv = processed / 'splits' / 'sample_manifest.csv'
            cwrite(split_csv, list(manifest_rows[0]), manifest_rows)
            split_metadata = {'rule': status['split_rule'], 'random_seed': None, 'randomness': 'None: deterministic ID order',
                              'labels_kept': 'Original 1..6, not zero-based', 'splits': status['splits'],
                              'sample_manifest_sha256': sha(split_csv), 'pairwise_subject_overlap': [],
                              'official_test_preserved': True}
            jwrite(processed / 'splits' / 'split_metadata.json', split_metadata)
            cwrite(report / 'class_distribution.csv', list(distributions[0]), distributions)
            cwrite(report / 'subject_class_distribution.csv', list(subject_rows[0]), subject_rows)
            status['stages']['subject_disjoint_split'] = 'PASS'

            # Exact duplicate audit; overlapping neighboring windows remain untouched.
            sample_hashes = {}
            duplicates = {'within_split_extra_windows': {}, 'cross_split_identical_windows': []}
            for split, data in split_data.items():
                hashes = [hashlib.sha256(np.ascontiguousarray(window).tobytes()).hexdigest() for window in data['x']]
                sample_hashes[split] = set(hashes)
                duplicates['within_split_extra_windows'][split] = len(hashes) - len(set(hashes))
            for a, b in [('train', 'validation'), ('train', 'test'), ('validation', 'test')]:
                duplicates['cross_split_identical_windows'].append({'splits': [a, b], 'count': len(sample_hashes[a] & sample_hashes[b])})
            status['exact_duplicates'] = duplicates
            jwrite(report / 'exact_duplicate_audit.json', duplicates)

            # Channel-wise population moments of final train windows ONLY (over N and time).
            fit = split_data['train']['x']
            mean = fit.mean(axis=(0, 1), dtype=np.float64)
            std = fit.std(axis=(0, 1), dtype=np.float64, ddof=0)
            assert np.isfinite(mean).all() and np.isfinite(std).all() and np.all(std > 1e-12)
            scaler = {'method': 'Per-channel z=(x-mean)/std', 'fit_split': 'train',
                      'fit_subject_ids': [int(value) for value in sorted(id_sets['train'])],
                      'excluded_subject_ids': [int(value) for value in sorted(id_sets['validation'] | id_sets['test'])],
                      'channels': CHANNELS, 'mean': mean.tolist(), 'std': std.tolist(), 'ddof': 0,
                      'reduction_axes': [0, 1], 'fit_windows': len(fit), 'fit_values_per_channel': len(fit) * 128,
                      'moment_dtype': 'float64', 'output_dtype': 'float32', 'epsilon': None,
                      'zero_std_policy': 'Fail rather than silently replace', 'sample_manifest_sha256': sha(split_csv),
                      'source_archive_sha256': provenance['sha256'],
                      'overlap_weighting': 'Each retained window/timepoint has equal weight; 50%-overlapping windows are not deduplicated.',
                      'raw_signals': 'Official preprocessed physical-unit inertial signals; not the official 561 normalized engineered features.'}
            jwrite(processed / 'scaler_train_only.json', scaler)
            standardization_checks = {}
            for split, data in split_data.items():
                normalized = ((data['x'] - mean) / std).astype(np.float32)
                assert np.isfinite(normalized).all()
                with (processed / f'{split}_standardized.npz').open('xb') as out:
                    np.savez_compressed(out, X=normalized, y=data['y'], subject=data['subject'],
                                        official_row_1based=data['row'], channels=np.array(CHANNELS))
                moments = {'mean': normalized.mean(axis=(0, 1), dtype=np.float64).tolist(),
                           'std': normalized.std(axis=(0, 1), dtype=np.float64).tolist(), 'shape': list(normalized.shape)}
                if split == 'train':
                    assert np.max(np.abs(moments['mean'])) < 1e-6
                    assert np.max(np.abs(np.array(moments['std']) - 1)) < 1e-6
                standardization_checks[split] = moments
            status['standardization_checks'] = standardization_checks
            status['stages']['train_only_standardization'] = 'PASS'
            say('Train-only standardization complete; parameters and three float32 NPZ artifacts saved.')

            examples = []
            for label in [1, 5]:
                data = split_data['train']
                index = int(np.flatnonzero(data['y'] == label)[0])
                window = data['x'][index]
                csv_path = processed / 'examples' / f'{NAMES[label].lower()}_window.csv'
                rows = [dict(time_s=float(t / 50), **dict(zip(CHANNELS, window[t].tolist()))) for t in range(128)]
                cwrite(csv_path, ['time_s'] + CHANNELS, rows)
                examples.append({'activity_id': label, 'activity_name': NAMES[label], 'subject_id': int(data['subject'][index]),
                                 'official_split': 'train', 'official_row_1based': int(data['row'][index]),
                                 'final_split': 'train', 'selection': 'First final-training window in original official row order with this activity label',
                                 'source_csv': csv_path.relative_to(ROOT).as_posix(), 'shape': [128, 9],
                                 'sampling_hz': 50, 'window_duration_s': 2.56, 'last_sample_time_s': 2.54,
                                 'standardized': False, 'n_windows': 1, 'uncertainty': 'Not applicable: one observed window, no aggregate inference.'})
            jwrite(processed / 'examples' / 'example_metadata.json', examples)
            status['stages']['real_sample_exports'] = 'PASS'
            after = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(dataset.rglob('*')) if p.is_file()}
            assert after == raw_before
            jwrite(report / 'original_files_after.json', after)
            baseline = json.loads((ROOT / 'reports' / run / 'existing_files_baseline.json').read_text(encoding='utf-8'))
            assert all(sha(ROOT / name) == digest for name, digest in baseline.items())
            status['stages']['original_and_existing_files_unchanged'] = 'PASS'
            status['raw_file_count'] = len(raw_before)
            status['git'] = {'repository_exists': (ROOT / '.git').exists(), 'git_writes': False, 'uploads': False}
            status['status'] = 'COMPLETE'
            say(f'Audit complete. {len(raw_before)} original files hash-identical; existing startup files unchanged.')
        except Exception as exc:
            status['status'] = 'FAILED'
            status['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            say(traceback.format_exc())
        finally:
            status['finished_at'] = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
            jwrite(report / 'audit_results.json', status)
    if status['status'] != 'COMPLETE':
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'audit')
