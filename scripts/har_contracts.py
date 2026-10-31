"""Shared UCI HAR contracts, independent of NumPy, files, and model libraries."""
import math
from numbers import Integral, Real
import re

CHANNELS = [f'{group}_{axis}' for group in ('body_acc', 'body_gyro', 'total_acc') for axis in 'xyz']
NAMES = {1: 'WALKING', 2: 'WALKING_UPSTAIRS', 3: 'WALKING_DOWNSTAIRS',
         4: 'SITTING', 5: 'STANDING', 6: 'LAYING'}
WINDOW_LENGTH = 128


def _integer(value):
    return isinstance(value, Integral) and not isinstance(value, bool)


def validate_window_shape(shape, expected_windows=None):
    shape = tuple(shape)
    if (len(shape) != 3 or any(not _integer(n) or n <= 0 for n in shape)
            or shape[1:] != (WINDOW_LENGTH, len(CHANNELS))):
        raise ValueError('Expected positive N x 128 time steps x 9 channels')
    if expected_windows is not None and shape[0] != expected_windows:
        raise ValueError('Window count does not match labels/manifest')


def validate_channel_order(channels):
    if list(channels) != CHANNELS:
        raise ValueError('Nine-channel order must be body_acc_xyz, body_gyro_xyz, total_acc_xyz')


def validate_activity_mapping(mapping):
    if (any(not _integer(key) for key in mapping) or dict(mapping) != NAMES):
        raise ValueError('Official activity mapping must preserve IDs 1..6 and names')


def validate_labels(labels, require_all=False):
    labels = list(labels)
    if not labels or any(not _integer(label) or label not in NAMES for label in labels):
        raise ValueError('Activity labels must be nonempty integer IDs 1..6; no implicit remapping')
    if require_all and set(labels) != set(NAMES):
        raise ValueError('All six activity classes are required')


def activity_name(label):
    validate_labels([label])
    return NAMES[int(label)]


def _subject_set(subjects):
    values = list(subjects)
    if not values or any(not _integer(value) or not 1 <= value <= 30 for value in values):
        raise ValueError('Subject IDs must be nonempty integer IDs 1..30')
    return set(values)


def validation_subject_ids(official_train_subjects, count=4):
    subjects = sorted(_subject_set(official_train_subjects))
    if not _integer(count) or count <= 0 or len(subjects) <= count:
        raise ValueError('Validation must leave at least one final training subject')
    return subjects[:count]


def validate_subject_groups(groups):
    if set(groups) != {'train', 'validation', 'test'}:
        raise ValueError('Exactly train, validation and test subject groups are required')
    sets = {name: _subject_set(values) for name, values in groups.items()}
    for a, b in [('train', 'validation'), ('train', 'test'), ('validation', 'test')]:
        if sets[a] & sets[b]:
            raise ValueError(f'Subject leakage between {a} and {b}')


def validate_scaler_provenance(scaler, split_metadata):
    """Validate declared training provenance; raw-value fitting is verified separately."""
    splits = split_metadata['splits']
    groups = {name: values['subjects'] for name, values in splits.items()}
    validate_subject_groups(groups)
    validate_channel_order(scaler['channels'])
    if scaler['fit_split'] != 'train':
        raise ValueError('Scaler must be fitted on the final training split only')
    if list(scaler['fit_subject_ids']) != sorted(groups['train']):
        raise ValueError('Scaler fit subjects do not match final training subjects')
    excluded = sorted(set(groups['validation']) | set(groups['test']))
    if list(scaler['excluded_subject_ids']) != excluded:
        raise ValueError('Validation/test subjects must be excluded from fitting')
    windows = splits['train']['n_windows']
    if not _integer(windows) or windows <= 0 or scaler['fit_windows'] != windows:
        raise ValueError('Scaler fit window count must match final training windows')
    if scaler['fit_values_per_channel'] != windows * WINDOW_LENGTH:
        raise ValueError('Scaler fitting must reduce final train windows and time only')
    if scaler['reduction_axes'] != [0, 1] or not _integer(scaler['ddof']) or scaler['ddof'] != 0:
        raise ValueError('Expected per-channel population moments over N and time')
    manifest_hash = scaler['sample_manifest_sha256']
    if (not isinstance(manifest_hash, str) or not re.fullmatch('[0-9a-f]{64}', manifest_hash)
            or manifest_hash != split_metadata['sample_manifest_sha256']):
        raise ValueError('Scaler and split must identify the same sample manifest')
    if scaler['moment_dtype'] != 'float64' or scaler['output_dtype'] != 'float32':
        raise ValueError('Unexpected scaler/output precision')
    for name in ['mean', 'std']:
        values = list(scaler[name])
        if (len(values) != len(CHANNELS) or any(not isinstance(value, Real) or isinstance(value, bool)
                or not math.isfinite(value) for value in values)):
            raise ValueError('Scaler must contain nine finite numerical moments')
    if any(value <= 1e-12 for value in scaler['std']):
        raise ValueError('Zero/near-zero channel standard deviation is not accepted')
