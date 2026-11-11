"""Day 02 two-layer 1D CNN. Returns logits, without softmax."""
import torch
from torch import nn


class MinimalHARConvNet(nn.Module):
    """[B, 9, 128] -> [B, 6]; fixed Day 02 acceptance architecture."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(9, 64, kernel_size=3, stride=1, padding=1, bias=True)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1, bias=True)
        self.relu2 = nn.ReLU()
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.flatten = nn.Flatten(1)
        self.classifier = nn.Linear(128, 6, bias=True)

    def forward(self, x):
        if x.ndim != 3 or x.shape[0] < 1 or tuple(x.shape[1:]) != (9, 128):
            raise ValueError('Expected nonempty [B, 9, 128] input')
        if not x.is_floating_point() or not torch.isfinite(x).all():
            raise ValueError('Expected finite floating-point input')
        x = self.relu1(self.conv1(x))
        x = self.relu2(self.conv2(x))
        return self.classifier(self.flatten(self.pool(x)))


def parameter_calculation():
    """Conv: Cout*(Cin*K + bias); Linear: out*(in + bias)."""
    layers = {'conv1': 64 * (9 * 3 + 1), 'conv2': 128 * (64 * 3 + 1),
              'classifier': 6 * (128 + 1)}
    return {'layers': layers, 'total': sum(layers.values())}


def targets_from_official(labels):
    """Map integer official IDs 1..6 to CrossEntropyLoss indices 0..5."""
    if (labels.ndim != 1 or labels.numel() == 0 or labels.dtype != torch.int64
            or not ((labels >= 1) & (labels <= 6)).all()):
        raise ValueError('Expected nonempty int64 official activity IDs 1..6')
    return labels - 1
