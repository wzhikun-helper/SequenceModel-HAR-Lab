from pathlib import Path
import sys
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from har_lab.cnn_ablation import build_model


class AblationTests(unittest.TestCase):
    def test_counts_and_paired_initialization(self):
        for seed in (42, 43, 44):
            torch.manual_seed(seed)
            base = build_model('A')
            self.assertEqual(sum(p.numel() for p in base.parameters()), 27270)
            for variant in 'BC':
                torch.manual_seed(seed)
                model = build_model(variant)
                self.assertEqual(sum(p.numel() for p in model.parameters()), 31510)
                self.assertTrue(all(torch.equal(value, model.state_dict()[key])
                                    for key, value in base.state_dict().items()))

    def test_extra_module_changes_logits_and_receives_gradient(self):
        torch.set_num_threads(2)
        for variant in 'BC':
            torch.manual_seed(42)
            model = build_model(variant)
            X = torch.randn(3, 9, 128)
            actual = model(X)
            actual.square().mean().backward()
            self.assertTrue(all(torch.count_nonzero(p.grad) for p in model.extra.parameters()))
            with torch.no_grad():
                model.extra[-1].bias.add_(0.5)
                self.assertFalse(torch.equal(actual, model(X)))


if __name__ == '__main__':
    unittest.main()
