"""CPU synthetic checks for the approved MaxPool architecture and selection rules."""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'scripts')]
from har_lab.cnn_baseline_a import CNNBaselineA
from cnn_metrics import classification_metrics, improves


class BaselineATests(unittest.TestCase):
    def test_pool_shape_and_unchanged_parameter_count(self):
        torch.set_num_threads(1)
        model=CNNBaselineA(); seen=[]
        h=model.maxpool.register_forward_hook(lambda m,i,o:seen.append(tuple(o.shape)))
        self.assertEqual(tuple(model(torch.randn(3,9,128)).shape),(3,6))
        h.remove(); self.assertEqual(seen,[(3,64,64)])
        self.assertEqual(sum(p.numel() for p in model.parameters()),27270)
        self.assertEqual(sum(p.numel() for p in model.maxpool.parameters()),0)

    def test_metrics_orientation_and_zero_division(self):
        result=classification_metrics(np.array([0,0,1]),np.array([0,1,1]))
        self.assertEqual(result['confusion_matrix'][0][:2],[1,1])
        self.assertEqual(result['confusion_matrix'][1][:2],[0,1])
        self.assertAlmostEqual(result['accuracy'],2/3)
        self.assertAlmostEqual(result['macro_f1'],(2/3+2/3)/6)
        self.assertEqual(result['f1'][5],0.0)

    def test_selection_uses_f1_before_loss_and_exact_tie(self):
        self.assertTrue(improves(.9,.5,.8,.1))
        self.assertFalse(improves(.8,.1,.9,.5))
        self.assertTrue(improves(.9,.4,.9,.5))
        self.assertFalse(improves(.9,.5,.9,.5))
        self.assertFalse(improves(.9,.6,.9,.5))


if __name__=='__main__': unittest.main()
