"""SE and equal-parameter residual MLP variants of historical CNN A."""
import torch
from torch import nn

from .cnn_baseline_a import CNNBaselineA


class CNNAblation(CNNBaselineA):
    """Construct shared layers first, then allocate the added module."""

    def __init__(self, variant):
        if variant not in {'B', 'C'}:
            raise ValueError('Expected B (SE) or C (residual MLP)')
        super().__init__()
        self.variant = variant
        self.extra = nn.Sequential(nn.Linear(128, 16), nn.ReLU(), nn.Linear(16, 128))

    def forward(self, x):
        if x.ndim != 3 or x.shape[0] < 1 or tuple(x.shape[1:]) != (9, 128):
            raise ValueError('Expected nonempty [B,9,128]')
        if not x.is_floating_point() or not torch.isfinite(x).all():
            raise ValueError('Expected finite floating-point input')
        features = self.relu2(self.conv2(self.maxpool(self.relu1(self.conv1(x)))))
        if self.variant == 'B':
            gates = self.extra(features.mean(dim=2)).sigmoid().unsqueeze(2)
            features = features * gates
        pooled = self.flatten(self.pool(features))
        if self.variant == 'C':
            pooled = pooled + self.extra(pooled)
        return self.classifier(pooled)


def build_model(variant):
    return CNNBaselineA() if variant == 'A' else CNNAblation(variant)
