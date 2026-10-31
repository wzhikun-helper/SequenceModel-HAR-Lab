"""Independent on-disk verification; never fits or changes delivered artifacts."""
import csv
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from har_contracts import (validate_channel_order, validate_labels, validate_scaler_provenance,
                           validate_subject_groups, validate_window_shape)

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main(source_run, artifact_run, verification_id=None):
    if not all(name.replace('_', '').isalnum() for name in [source_run, artifact_run]):
        raise ValueError('Unsafe run ID')
    reports = ROOT / 'reports' / source_run
    processed = ROOT / 'data' / 'processed' / artifact_run
    figures = ROOT / 'outputs' / 'figures' / artifact_run
    if verification_id is not None and not verification_id.replace('_', '').isalnum():
        raise ValueError('Unsafe verification ID')
    suffix = '_' + verification_id if verification_id else ''
    output = reports / ('independent_verification' + suffix + '.json')
    result = {'timestamp': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
              'artifact_run': artifact_run, 'checks': {}, 'status': 'STARTED'}
    with (ROOT / 'logs' / (artifact_run + '_verification' + suffix + '.log')).open('x', encoding='utf-8', buffering=1) as log:
        def mark(name, info='PASS'):
            result['checks'][name] = info
            message = name + ': ' + str(info)
            print(message, flush=True)
            log.write(message + '\n')
        try:
            provenance = read_json(reports / 'download_provenance.json')
            dataset = ROOT / provenance['dataset_root']
            assert digest(ROOT / provenance['relative_path']) == provenance['sha256']
            inner = provenance['inner_archive']
            assert digest(ROOT / inner['path']) == inner['sha256']
            mark('archive_sha256_unchanged')
            original_hashes = read_json(reports / 'audit02' / 'original_files_before.json')
            assert len(original_hashes) == 29
            assert all(digest(ROOT / name) == expected for name, expected in original_hashes.items())
            baseline = read_json(reports / 'existing_files_baseline.json')
            assert all(digest(ROOT / name) == expected for name, expected in baseline.items())
            mark('29_original_files_and_4_existing_files_unchanged')
            metadata = read_json(processed / 'splits' / 'split_metadata.json')
            scaler = read_json(processed / 'scaler_train_only.json')
            validate_scaler_provenance(scaler, metadata)
            manifest_path = processed / 'splits' / 'sample_manifest.csv'
            assert digest(manifest_path) == metadata['sample_manifest_sha256'] == scaler['sample_manifest_sha256']
            with manifest_path.open(encoding='utf-8', newline='') as stream:
                rows = list(csv.DictReader(stream))
            assert len(rows) == len({row['sample_id'] for row in rows}) == 10299
            original = {}
            for partition, count in [('train', 7352), ('test', 2947)]:
                labels = np.loadtxt(dataset / partition / f'y_{partition}.txt', dtype=int)
                subjects = np.loadtxt(dataset / partition / f'subject_{partition}.txt', dtype=int)
                assert labels.shape == subjects.shape == (count,)
                original[partition] = (labels, subjects)
            selected = {}
            loaded = {}
            for split in ['train', 'validation', 'test']:
                selected[split] = [row for row in rows if row['split'] == split]
                part_rows = selected[split]
                assert [int(row['split_index_0based']) for row in part_rows] == list(range(len(part_rows)))
                subject_ids = sorted({int(row['subject_id']) for row in part_rows})
                assert subject_ids == metadata['splits'][split]['subjects']
                counts = Counter(row['activity_name'] for row in part_rows)
                assert dict(counts) == metadata['splits'][split]['class_counts']
                for row in part_rows:
                    source = row['official_split']
                    index = int(row['official_row_1based']) - 1
                    assert row['sample_id'] == f'{source}:{index + 1:06d}'
                    assert int(row['activity_id']) == original[source][0][index]
                    assert int(row['subject_id']) == original[source][1][index]
                    assert source == ('test' if split == 'test' else 'train')
                with np.load(processed / f'{split}_standardized.npz', allow_pickle=False) as archive:
                    loaded[split] = {key: archive[key] for key in archive.files}
                data = loaded[split]
                validate_window_shape(data['X'].shape, expected_windows=len(part_rows))
                validate_channel_order(data['channels'].tolist())
                validate_labels(data['y'].tolist(), require_all=True)
                assert data['X'].dtype == np.float32
                assert np.isfinite(data['X']).all()
                assert np.array_equal(data['y'], [int(row['activity_id']) for row in part_rows])
                assert np.array_equal(data['subject'], [int(row['subject_id']) for row in part_rows])
                assert np.array_equal(data['official_row_1based'], [int(row['official_row_1based']) for row in part_rows])
                assert data['channels'].tolist() == scaler['channels']
            sets = {split: set(data['subject'].tolist()) for split, data in loaded.items()}
            validate_subject_groups(sets)
            assert sets['validation'] == set(sorted(set(original['train'][1].tolist()))[:4]) == {1, 3, 5, 6}
            assert not (sets['train'] & sets['validation'] or sets['train'] & sets['test'] or sets['validation'] & sets['test'])
            assert np.array_equal(loaded['test']['official_row_1based'], np.arange(1, 2948))
            assert np.array_equal(loaded['test']['subject'], original['test'][1])
            assert np.array_equal(loaded['test']['y'], original['test'][0])
            mark('all_10299_manifest_rows_and_saved_npz_metadata')
            mark('official_test_order_labels_subjects_preserved')
            mark('three_subject_sets_disjoint_and_validation_rule_exact')
            assert scaler['fit_subject_ids'] == sorted(sets['train'])
            assert scaler['fit_windows'] == 6037 and scaler['fit_values_per_channel'] == 6037 * 128
            max_mean_error = max_std_error = 0.0
            examples = read_json(processed / 'examples' / 'example_metadata.json')
            example_frames = {e['activity_id']: np.genfromtxt(ROOT / e['source_csv'], delimiter=',', names=True) for e in examples}
            for channel_index, channel in enumerate(scaler['channels']):
                raw = {partition: np.loadtxt(dataset / partition / 'Inertial Signals' / f'{channel}_{partition}.txt') for partition in ['train', 'test']}
                indices = loaded['train']['official_row_1based'] - 1
                fit_values = raw['train'][indices].ravel()
                # Independently recompute one channel at a time from original rows.
                mu = float(np.sum(fit_values, dtype=np.float64) / fit_values.size)
                sigma = float(np.sqrt(np.sum((fit_values - mu) ** 2, dtype=np.float64) / fit_values.size))
                max_mean_error = max(max_mean_error, abs(mu - scaler['mean'][channel_index]))
                max_std_error = max(max_std_error, abs(sigma - scaler['std'][channel_index]))
                assert np.isclose(mu, scaler['mean'][channel_index], rtol=0, atol=1e-12)
                assert np.isclose(sigma, scaler['std'][channel_index], rtol=0, atol=1e-12)
                for split, data in loaded.items():
                    source = 'test' if split == 'test' else 'train'
                    values = raw[source][data['official_row_1based'] - 1]
                    expected = ((values - scaler['mean'][channel_index]) / scaler['std'][channel_index]).astype(np.float32)
                    assert np.array_equal(expected, data['X'][:, :, channel_index])
                for example in examples:
                    frame = example_frames[example['activity_id']]
                    assert np.array_equal(frame[channel], raw['train'][example['official_row_1based'] - 1])
                    assert int(original['train'][0][example['official_row_1based'] - 1]) == example['activity_id']
                    assert example['subject_id'] in sets['train']
            mark('train_only_scaler_independent_moments', {'status': 'PASS', 'max_mean_abs_error': max_mean_error, 'max_std_abs_error': max_std_error})
            mark('all_saved_normalized_values_exactly_match_raw_and_train_scaler')
            for frame in example_frames.values():
                assert np.array_equal(frame['time_s'], np.arange(128) / 50)
            mark('both_example_csvs_match_all_original_128_by_9_values')
            image_checks = []
            for activity in ['walking', 'standing']:
                stem = figures / f'fig01_{activity}_nine_channels'
                png = stem.with_suffix('.png')
                with Image.open(png) as im:
                    size = im.size
                    dpi = im.info.get('dpi')
                    assert size == (2460, 3450)
                    assert dpi and min(dpi) >= 299
                    im.verify()
                pdf = stem.with_suffix('.pdf')
                with pdf.open('rb') as stream:
                    assert stream.read(5) == b'%PDF-'
                svg = stem.with_suffix('.svg')
                tree = ET.parse(svg)
                texts = [node.text for node in tree.iter() if node.tag.endswith('}text') and node.text]
                text = '\n'.join(texts)
                assert activity.upper() in text and all(channel in text for channel in scaler['channels'])
                assert 'Time within window (s)' in text and 'rad/s' in text and '(g)' in text
                assert 'n = 1 observed window' in text
                image_checks.append({'activity': activity, 'png_pixels': size, 'dpi': dpi,
                                     'pdf_signature': 'PASS', 'svg_editable_text_and_labels': 'PASS'})
            mark('two_figures_png_pdf_svg_and_labels', image_checks)
            # A Git repository is expected after initial project setup; only the
            # tracking boundary matters, not whether .git exists.
            tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z', '--',
                                      'data', 'models', 'outputs', 'logs', '.aws', '.ssh'],
                                     capture_output=True)
            if tracked.returncode == 0:
                if tracked.stdout:
                    raise ValueError('Local data/model/log/credential directories are tracked by Git')
                mark('git_tracking_boundary', 'PASS: protected directories are not tracked')
            else:
                raise RuntimeError('Git tracking boundary could not be verified')
            assert '/data/' in (ROOT / '.gitignore').read_text() and '/models/' in (ROOT / '.gitignore').read_text()
            mark('existing_data_model_ignore_rules')
            result['status'] = 'PASS'
        except Exception as exc:
            result['status'] = 'FAIL'
            result['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            log.write(traceback.format_exc())
            print(traceback.format_exc(), flush=True)
        with output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
    if result['status'] != 'PASS':
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source_run')
    parser.add_argument('artifact_run')
    parser.add_argument('--verification-id', help='Fresh suffix for an additional read-only verification report')
    args = parser.parse_args()
    main(args.source_run, args.artifact_run, args.verification_id)
