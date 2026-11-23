"""Synthetic fixtures for Task03 report validation; no models or official data."""
import csv
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import report_gru_task03 as report


class Task03ReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runs = self.root / 'runs'
        self.data = self.root / 'data'
        self.data.mkdir()
        self.out = self.root / 'report'
        self.ids = list(range(1, 2948))
        self.labels = [i % 6 for i in range(2947)]
        self.rows = [
            [i, label, label, *[2 if k == label else 0 for k in range(6)]]
            for i, label in zip(self.ids, self.labels)
        ]
        test_path = self.data / 'test_standardized.npz'
        np.savez(test_path, official_row_1based=self.ids, y=np.array(self.labels) + 1)
        for seed in report.SEEDS:
            order_sha = hashlib.sha256(f'order{seed}'.encode()).hexdigest()
            init_sha = hashlib.sha256(f'init{seed}'.encode()).hexdigest()
            folder = self.runs / f'seed{seed}'
            folder.mkdir(parents=True)
            (folder/'config.yaml').write_text(f'seed: {seed}\nbatch: 64\n', encoding='utf-8')
            (folder/'best.pt').write_bytes(b'fixture best')
            (folder/'last.pt').write_bytes(b'fixture last')
            (folder/'training.log').write_text('Synthetic fixture\nExit code 0\n', encoding='utf-8')
            (folder/'training_history.csv').write_text(
                'epoch,order_sha256,validation_macro_f1,validation_loss,training_loss,validation_accuracy\n'
                f'1,{order_sha},1,0.5,0.5,1\n', encoding='utf-8')
            result = dict(status='PASS', strict_reloads_equal=True, test_model_evaluation_passes=1,
                          best_epoch=1, epochs_completed=1, order_sha256=[order_sha],
                          initial_weight_sha256=init_sha, best_sha256=report.sha(folder/'best.pt'),
                          last_sha256=report.sha(folder/'last.pt'))
            (folder/'training_result.json').write_text(json.dumps(result), encoding='utf-8')
            counts = [self.labels.count(k) for k in range(6)]
            test = dict(accuracy=1, macro_f1=1, f1=[1]*6, precision=[1]*6, recall=[1]*6,
                        support=counts, confusion_matrix=np.diag(counts).tolist(),
                        loss=math.log1p(5 * math.exp(-2)), test_model_evaluation_passes=1,
                        best_epoch=1, selection_used_test=False, test_artifact_sha256=report.sha(test_path))
            (folder/'test_metrics.json').write_text(json.dumps(test), encoding='utf-8')
            self.write_classes(folder, [
                [i+1, activity, 1, 1, 1, counts[i]] for i, activity in enumerate(report.LABELS)
            ])
            self.write_predictions(folder, self.rows)

    def write_classes(self, folder, rows, fields=report.CLASS_FIELDS):
        with (folder/'classification_report.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(fields)
            writer.writerows(rows)

    def write_predictions(self, folder, rows):
        with (folder/'test_predictions.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['official_row_1based','true_label_0based','pred_label_0based',
                             *(f'logit_{k}' for k in range(6))])
            writer.writerows(rows)

    def snapshot(self):
        return {path.relative_to(self.root): report.sha(path)
                for folder in (self.runs, self.data) for path in folder.rglob('*') if path.is_file()}

    def cli(self):
        return subprocess.run([sys.executable, '-O', '-B', str(ROOT/'scripts/report_gru_task03.py'),
                               str(self.runs), str(self.data), str(self.out)],
                              cwd=ROOT, encoding='utf-8', capture_output=True, timeout=60)

    def test_optimized_cli_produces_report_without_writing_to_sources(self):
        before = self.snapshot()
        run = self.cli()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((self.out/'summary.json').is_file())
        self.assertEqual(report.read(self.out/'summary.json')['seeds']['42']['accuracy'], 1)
        self.assertEqual(self.snapshot(), before)

    def test_optimized_cli_rejects_late_bad_checkpoint_before_writing(self):
        (self.runs/'seed44/best.pt').write_bytes(b'bad checksum')
        before = self.snapshot()
        run = self.cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('checkpoint hash differs', run.stderr)
        self.assertFalse(self.out.exists())
        self.assertEqual(self.snapshot(), before)

    def test_prediction_contract_rejects_count_nan_and_bad_argmax(self):
        folder = self.runs/'seed42'
        for index,value,message in [(3,'nan','Nonfinite'),(2,5,'argmax'),(None,None,'row count')]:
            with self.subTest(message=message):
                rows = [row.copy() for row in self.rows]
                if index is None:
                    rows.pop()
                else:
                    rows[0][index] = value
                self.write_predictions(folder, rows)
                with self.assertRaisesRegex(ValueError, message):
                    report.compute_test(folder/'test_predictions.csv', self.ids, self.labels)

    def test_rejects_bad_log_metrics_and_seed_config(self):
        folder = self.runs/'seed44'
        log, metrics, config = [folder/name for name in ('training.log','test_metrics.json','config.yaml')]
        for path, replacement, message in [
            (log, 'not an Exit code 0\n', 'does not record exit code 0'),
            (metrics, json.dumps({**report.read(metrics), 'accuracy': 0.5}), 'recomputed accuracy differs'),
            (config, 'seed: 44\nbatch: 32\n', 'differ beyond the seed'),
        ]:
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_text(replacement, encoding='utf-8')
                try:
                    with self.assertRaisesRegex(ValueError, message):
                        report.verify_runs(self.runs, self.data)
                finally:
                    path.write_bytes(original)

    def test_classification_report_rejects_missing_field_and_missing_or_extra_rows(self):
        folder = self.runs/'seed42'
        path = folder/'classification_report.csv'
        with path.open(encoding='utf-8', newline='') as stream:
            _, *rows = csv.reader(stream)
        for fields, bad_rows, message in [
            (report.CLASS_FIELDS[:-1], [row[:-1] for row in rows], 'invalid classification report header'),
            (report.CLASS_FIELDS, rows[:-1], 'exactly six class rows'),
            (report.CLASS_FIELDS, rows + rows[:1], 'exactly six class rows'),
        ]:
            with self.subTest(message=message, rows=len(bad_rows)):
                self.write_classes(folder, bad_rows, fields)
                with self.assertRaisesRegex(ValueError, message):
                    report.verify_runs(self.runs, self.data)

    def test_classification_report_rejects_tampering_and_class_order(self):
        folder = self.runs/'seed42'
        with (folder/'classification_report.csv').open(encoding='utf-8', newline='') as stream:
            _, *rows = csv.reader(stream)
        for index, value, message in [
            (2, '0.5', 'precision differs'), (3, 'nan', 'recall differs'),
            (4, 'inf', 'f1 differs'), (5, '0', 'support differs'),
        ]:
            with self.subTest(field=report.CLASS_FIELDS[index]):
                modified = [row.copy() for row in rows]
                modified[0][index] = value
                self.write_classes(folder, modified)
                with self.assertRaisesRegex(ValueError, message):
                    report.verify_runs(self.runs, self.data)
        self.write_classes(folder, [rows[1], rows[0], *rows[2:]])
        with self.assertRaisesRegex(ValueError, 'class label or order differs'):
            report.verify_runs(self.runs, self.data)

    def test_history_rejects_missing_fields_invalid_metrics_and_epochs(self):
        path = self.runs/'seed42'/'training_history.csv'
        header, valid = path.read_text(encoding='utf-8').splitlines()
        for index, value, message in [
            (4, 'nan', 'training_loss'), (5, 'inf', 'validation_accuracy'),
            (2, '1.1', 'validation_macro_f1'), (3, '-0.1', 'validation_loss'),
            (0, '2', 'epochs must be continuous'),
        ]:
            with self.subTest(field=header.split(',')[index], value=value):
                invalid = valid.split(',')
                invalid[index] = value
                path.write_text(f'{header}\n{",".join(invalid)}\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, message):
                    report.verify_runs(self.runs, self.data)
        path.write_text(f'{header}\n{valid}\n{valid}\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'epochs must be continuous'):
            report.verify_runs(self.runs, self.data)
        path.write_text(f'{header.rsplit(",", 1)[0]}\n{valid.rsplit(",", 1)[0]}\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing or duplicate fields'):
            report.verify_runs(self.runs, self.data)

    def test_optimized_cli_rejects_late_bad_class_report_without_output(self):
        file = self.runs/'seed44'/'classification_report.csv'
        with file.open(encoding='utf-8', newline='') as stream:
            _, *rows = csv.reader(stream)
        rows[0][4] = '0.75'
        self.write_classes(file.parent, rows)
        before = self.snapshot()
        run = self.cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('f1 differs', run.stderr)
        self.assertFalse(self.out.exists())
        self.assertEqual(self.snapshot(), before)
