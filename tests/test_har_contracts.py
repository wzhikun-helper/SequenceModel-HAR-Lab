"""Synthetic contract tests: standard library only, no UCI download or fitting."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from har_contracts import (CHANNELS, NAMES, activity_name, validate_activity_mapping,
                           validate_channel_order, validate_labels, validate_scaler_provenance,
                           validate_subject_groups, validate_window_shape, validation_subject_ids)


class ShapeAndLabels(unittest.TestCase):
    def test_real_window_layout(self):
        validate_window_shape((2, 128, 9), expected_windows=2)

    def test_reject_swapped_or_engineered_feature_layouts(self):
        for shape in [(2, 9, 128), (2, 561), (128, 9), (2, 127, 9), (2, 128, 8), (2, 128, 9, 1)]:
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                validate_window_shape(shape)

    def test_reject_empty_or_noninteger_dimensions(self):
        for shape in [(0, 128, 9), (-1, 128, 9), (2.0, 128, 9), (True, 128, 9)]:
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                validate_window_shape(shape)

    def test_manifest_window_count(self):
        with self.assertRaises(ValueError):
            validate_window_shape((3, 128, 9), expected_windows=2)

    def test_exact_nine_channel_order(self):
        self.assertEqual(CHANNELS, ['body_acc_x', 'body_acc_y', 'body_acc_z',
                                    'body_gyro_x', 'body_gyro_y', 'body_gyro_z',
                                    'total_acc_x', 'total_acc_y', 'total_acc_z'])
        validate_channel_order(CHANNELS)

    def test_channel_permutation_or_duplicates_fail(self):
        for channels in [CHANNELS[::-1], CHANNELS[:-1], [CHANNELS[0]] * 9]:
            with self.subTest(channels=channels), self.assertRaises(ValueError):
                validate_channel_order(channels)

    def test_official_mapping_and_subset(self):
        expected = {1: 'WALKING', 2: 'WALKING_UPSTAIRS', 3: 'WALKING_DOWNSTAIRS',
                    4: 'SITTING', 5: 'STANDING', 6: 'LAYING'}
        self.assertEqual(NAMES, expected)
        validate_activity_mapping(expected)
        validate_labels([1, 6, 1])
        validate_labels(range(1, 7), require_all=True)
        self.assertEqual(activity_name(6), 'LAYING')

    def test_no_silent_zero_based_or_unknown_labels(self):
        for labels in [[0, 1], [7], [1.0], [True], ['1'], []]:
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                validate_labels(labels)

    def test_require_all_classes(self):
        with self.assertRaises(ValueError):
            validate_labels([1, 2, 3], require_all=True)

    def test_wrong_label_name_mapping(self):
        wrong = dict(NAMES)
        wrong[6] = 'STANDING'
        with self.assertRaises(ValueError):
            validate_activity_mapping(wrong)


class SubjectSplits(unittest.TestCase):
    def test_fixed_sorted_rule_independent_of_order_duplicates(self):
        source = [30, 6, 1, 5, 3, 7, 1]
        before = source[:]
        self.assertEqual(validation_subject_ids(source), [1, 3, 5, 6])
        self.assertEqual(source, before)

    def test_rule_leaves_training_subjects(self):
        for source in [[], [1, 3, 5, 6]]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                validation_subject_ids(source)

    def test_valid_groups(self):
        validate_subject_groups({'train': [7, 8], 'validation': [1, 3, 5, 6], 'test': [2, 4]})

    def test_each_pairwise_overlap_rejected(self):
        for groups in [{'train': [7], 'validation': [7], 'test': [2]},
                       {'train': [7], 'validation': [1], 'test': [7]},
                       {'train': [7], 'validation': [1], 'test': [1]}]:
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                validate_subject_groups(groups)

    def test_empty_missing_or_invalid_groups(self):
        for groups in [{'train': [], 'validation': [1], 'test': [2]},
                       {'train': [7], 'validation': [1]},
                       {'train': [31], 'validation': [1], 'test': [2]}]:
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                validate_subject_groups(groups)


class ScalerProvenance(unittest.TestCase):
    def setUp(self):
        self.meta = {'sample_manifest_sha256': 'a' * 64, 'splits': {
            'train': {'subjects': [7, 8], 'n_windows': 3},
            'validation': {'subjects': [1, 3, 5, 6], 'n_windows': 2},
            'test': {'subjects': [2, 4], 'n_windows': 2}}}
        self.scaler = {'fit_split': 'train', 'fit_subject_ids': [7, 8],
                       'excluded_subject_ids': [1, 2, 3, 4, 5, 6], 'channels': CHANNELS[:],
                       'fit_windows': 3, 'fit_values_per_channel': 384, 'ddof': 0,
                       'reduction_axes': [0, 1], 'sample_manifest_sha256': 'a' * 64,
                       'moment_dtype': 'float64', 'output_dtype': 'float32',
                       'mean': [0.0] * 9, 'std': [1.0] * 9}

    def reject_change(self, key, value):
        changed = copy.deepcopy(self.scaler)
        changed[key] = value
        with self.assertRaises(ValueError):
            validate_scaler_provenance(changed, self.meta)

    def test_valid_training_provenance(self):
        validate_scaler_provenance(self.scaler, self.meta)

    def test_validation_or_test_fit_rejected(self):
        for split in ['validation', 'test', 'all']:
            with self.subTest(split=split):
                self.reject_change('fit_split', split)

    def test_leaking_missing_duplicate_fit_ids_rejected(self):
        for ids in [[1, 7, 8], [7], [7, 7, 8], [7, 8, 2]]:
            with self.subTest(ids=ids):
                self.reject_change('fit_subject_ids', ids)

    def test_excluded_subjects_must_be_complete(self):
        self.reject_change('excluded_subject_ids', [1, 3, 5, 6])

    def test_count_time_and_axes(self):
        for key, value in [('fit_windows', 7), ('fit_values_per_channel', 3 * 9),
                           ('reduction_axes', [0]), ('ddof', 1)]:
            with self.subTest(key=key):
                self.reject_change(key, value)

    def test_manifest_identity_and_format(self):
        for value in ['b' * 64, '', 'a']:
            with self.subTest(value=value):
                self.reject_change('sample_manifest_sha256', value)

    def test_channel_order_in_scaler(self):
        self.reject_change('channels', CHANNELS[::-1])

    def test_nine_finite_moments(self):
        for key, value in [('mean', [0.] * 8), ('mean', [float('nan')] * 9),
                           ('std', [float('inf')] * 9), ('std', [True] * 9)]:
            with self.subTest(key=key, value=value):
                self.reject_change(key, value)

    def test_zero_or_negative_scale(self):
        for value in [0.0, -1.0, 1e-14]:
            with self.subTest(value=value):
                self.reject_change('std', [value] * 9)

    def test_precision_is_recorded(self):
        self.reject_change('moment_dtype', 'float32')
        self.reject_change('output_dtype', 'float64')


if __name__ == '__main__':
    unittest.main()
