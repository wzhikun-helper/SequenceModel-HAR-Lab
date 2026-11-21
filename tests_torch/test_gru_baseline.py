"""No dataset needed: GRU shape/state/gradient and audited configuration contracts."""
from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from har_lab.gru_baseline_b import GRUBaselineB, parameter_calculation
from train_gru_baseline import make_config, optimizer, read, AUDIT


class GRUBaselineTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        torch.set_num_threads(2)
        self.model = GRUBaselineB()

    def test_shapes_and_final_hidden_classifier(self):
        for batch in [1, 5]:
            X = torch.randn(batch, 128, 9)
            sequence, hidden = self.model.gru(X)
            self.assertEqual(tuple(sequence.shape), (batch, 128, 64))
            self.assertEqual(tuple(hidden.shape), (1, batch, 64))
            self.assertTrue(torch.equal(hidden[-1], sequence[:, -1, :]))
            self.assertTrue(torch.equal(self.model(X), self.model.classifier(hidden[-1])))

    def test_invalid_input_and_parameter_count(self):
        for shape in [(1, 9, 128), (0, 128, 9), (2, 127, 9)]:
            with self.assertRaises(ValueError):
                self.model(torch.zeros(shape))
        with self.assertRaises(ValueError):
            self.model(torch.full((1, 128, 9), float('nan')))
        self.assertEqual(sum(p.numel() for p in self.model.parameters()), 14790)
        self.assertEqual(parameter_calculation()['total'], 14790)

    def test_gradient_and_optimizer_and_same_common_config(self):
        audit = read(AUDIT / 'audit_evidence.json')
        config = make_config(audit)
        for key, value in audit['cnn_config'].items():
            if key in config and key != 'input_shape':
                self.assertEqual(config[key], value)
        optim = optimizer(self.model, config)
        before = {k: p.clone() for k, p in self.model.state_dict().items()}
        loss = torch.nn.functional.cross_entropy(self.model(torch.randn(6, 128, 9)), torch.arange(6))
        loss.backward()
        for p in self.model.parameters():
            self.assertTrue(torch.isfinite(p.grad).all())
            self.assertGreater(int(torch.count_nonzero(p.grad)), 0)
        optim.step()
        self.assertTrue(all(not torch.equal(before[k], p) for k, p in self.model.state_dict().items()))


if __name__ == '__main__':
    unittest.main()
