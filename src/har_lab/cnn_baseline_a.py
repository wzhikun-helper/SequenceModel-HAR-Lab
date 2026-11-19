"""Approved Baseline A; preserves the earlier no-MaxPool teaching model."""
import torch
from torch import nn
from .cnn import MinimalHARConvNet


class CNNBaselineA(MinimalHARConvNet):
    def __init__(self):
        super().__init__()
        self.maxpool = nn.MaxPool1d(kernel_size=2, stride=2)

    def forward(self, x):
        if x.ndim != 3 or x.shape[0] < 1 or tuple(x.shape[1:]) != (9, 128):
            raise ValueError('Expected nonempty [B,9,128]')
        if not x.is_floating_point() or not torch.isfinite(x).all():
            raise ValueError('Expected finite floating-point input')
        x = self.maxpool(self.relu1(self.conv1(x)))
        x = self.relu2(self.conv2(x))
        return self.classifier(self.flatten(self.pool(x)))
