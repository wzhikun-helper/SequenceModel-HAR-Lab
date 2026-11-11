"""Optional CPU PyTorch tests; separate from the standard-library Day 01 CI."""
import io
from pathlib import Path
import sys
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from har_lab.cnn import MinimalHARConvNet, parameter_calculation, targets_from_official


class MinimalCNNTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        torch.manual_seed(31)
        self.model = MinimalHARConvNet()

    def test_batch_shapes_and_parameter_formula(self):
        for batch in (1, 4):
            self.assertEqual(tuple(self.model(torch.randn(batch, 9, 128)).shape), (batch, 6))
        self.assertEqual(sum(p.numel() for p in self.model.parameters()), 27270)
        self.assertEqual(parameter_calculation()['total'], 27270)

    def test_invalid_layout_and_values(self):
        for shape in ((2, 128, 9), (0, 9, 128), (2, 9, 127), (9, 128)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                self.model(torch.zeros(shape))
        for value in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                self.model(torch.full((1, 9, 128), value))
        with self.assertRaises(ValueError):
            self.model(torch.zeros(1, 9, 128, dtype=torch.int64))

    def test_explicit_label_conversion(self):
        labels = torch.arange(1, 7)
        self.assertTrue(torch.equal(targets_from_official(labels), torch.arange(6)))
        self.assertTrue(torch.equal(labels, torch.arange(1, 7)))
        for labels in (torch.tensor([0]), torch.tensor([7]), torch.tensor([1.0]),
                       torch.tensor([[1]]), torch.empty(0, dtype=torch.int64)):
            with self.assertRaises(ValueError):
                targets_from_official(labels)

    def test_backward_without_update_and_checkpoint_roundtrip(self):
        batch = torch.randn(6, 9, 128)
        initial = {k: v.clone() for k, v in self.model.state_dict().items()}
        loss = torch.nn.CrossEntropyLoss()(self.model(batch), torch.arange(6))
        loss.backward()
        for parameter in self.model.parameters():
            self.assertIsNotNone(parameter.grad)
            self.assertTrue(torch.isfinite(parameter.grad).all())
            self.assertGreater(int(torch.count_nonzero(parameter.grad)), 0)
        self.assertTrue(all(torch.equal(initial[k], v) for k, v in self.model.state_dict().items()))
        stream = io.BytesIO()
        torch.save(self.model.state_dict(), stream)
        stream.seek(0)
        other = MinimalHARConvNet()
        other.load_state_dict(torch.load(stream, weights_only=True), strict=True)
        self.model.eval()
        other.eval()
        with torch.no_grad():
            self.assertTrue(torch.equal(self.model(batch), other(batch)))


if __name__ == '__main__':
    unittest.main()
