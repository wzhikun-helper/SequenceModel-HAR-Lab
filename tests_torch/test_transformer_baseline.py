"""Synthetic tests for the exact approved Transformer C contract."""
import io
from pathlib import Path
import sys
import unittest

import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from har_lab.transformer_baseline_c import TransformerBaselineC, parameter_calculation


class TransformerTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)
        torch.manual_seed(42)
        self.model=TransformerBaselineC()

    def test_architecture_shapes_and_parameter_count(self):
        layer=self.model.encoder.layers[0]
        self.assertFalse(layer.norm_first)
        self.assertTrue(layer.self_attn.batch_first)
        self.assertEqual(layer.self_attn.num_heads,4)
        self.assertEqual(layer.linear1.out_features,128)
        self.assertEqual(layer.dropout.p,0.0)
        self.assertIsNone(self.model.encoder.norm)
        for batch in [1,3]:
            self.assertEqual(tuple(self.model(torch.zeros(batch,128,9)).shape),(batch,6))
        self.assertEqual(sum(p.numel() for p in self.model.parameters()),34502)
        self.assertEqual(parameter_calculation()['total'],34502)

    def test_fixed_sinusoid_buffer(self):
        encoding=self.model.position.encoding
        self.assertEqual(tuple(encoding.shape),(1,128,64))
        self.assertFalse(encoding.requires_grad)
        self.assertNotIn('position.encoding',dict(self.model.named_parameters()))
        self.assertIn('position.encoding',self.model.state_dict())
        self.assertTrue(torch.equal(encoding[0,0,0::2],torch.zeros(32)))
        self.assertTrue(torch.equal(encoding[0,0,1::2],torch.ones(32)))
        self.assertAlmostEqual(float(encoding[0,1,0]),float(torch.sin(torch.tensor(1.))),places=7)

    def test_backward_update_and_checkpoint(self):
        X=torch.randn(6,128,9)
        optim=torch.optim.Adam(self.model.parameters(),lr=.001)
        before={k:v.clone() for k,v in self.model.state_dict().items()}
        loss=torch.nn.functional.cross_entropy(self.model(X),torch.arange(6))
        loss.backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in self.model.parameters()))
        self.assertGreater(sum(int(torch.count_nonzero(p.grad)) for p in self.model.parameters()),0)
        optim.step()
        self.assertTrue(any(not torch.equal(before[k],p) for k,p in self.model.named_parameters()))
        self.assertTrue(torch.equal(before['position.encoding'],self.model.position.encoding))
        stream=io.BytesIO();torch.save(self.model.state_dict(),stream);stream.seek(0)
        other=TransformerBaselineC()
        other.load_state_dict(torch.load(stream,weights_only=True),strict=True)
        self.model.eval();other.eval()
        with torch.no_grad():self.assertTrue(torch.equal(self.model(X),other(X)))

    def test_invalid_layout_and_values(self):
        for shape in [(1,9,128),(0,128,9),(1,127,9)]:
            with self.assertRaises(ValueError):self.model(torch.zeros(shape))
        with self.assertRaises(ValueError):self.model(torch.full((1,128,9),float('nan')))


if __name__=='__main__':unittest.main()
