"""Approved post-norm Transformer C, fixed sinusoidal positions, time mean."""
import math
import torch
from torch import nn


class FixedSinusoidalPositions(nn.Module):
    def __init__(self):
        super().__init__()
        position = torch.arange(128, dtype=torch.float32).unsqueeze(1)
        scale = torch.exp(torch.arange(0, 64, 2, dtype=torch.float32) * (-math.log(10000.0) / 64))
        encoding = torch.zeros(1, 128, 64, dtype=torch.float32)
        encoding[0, :, 0::2] = torch.sin(position * scale)
        encoding[0, :, 1::2] = torch.cos(position * scale)
        self.register_buffer('encoding', encoding, persistent=True)

    def forward(self, x):
        return x + self.encoding


class TimeMean(nn.Module):
    def forward(self, x):
        return x.mean(dim=1)


class TransformerBaselineC(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(9, 64)
        self.position = FixedSinusoidalPositions()
        layer = nn.TransformerEncoderLayer(d_model=64, nhead=4, dim_feedforward=128,
                  dropout=0.0, activation='relu', layer_norm_eps=1e-5,
                  batch_first=True, norm_first=False)
        self.encoder = nn.TransformerEncoder(layer, num_layers=1)
        self.pool = TimeMean()
        self.classifier = nn.Linear(64, 6)

    def forward(self, x):
        if x.ndim != 3 or x.shape[0] < 1 or tuple(x.shape[1:]) != (128, 9):
            raise ValueError('Expected nonempty [B,128,9] input')
        if not x.is_floating_point() or not torch.isfinite(x).all():
            raise ValueError('Expected finite floating-point input')
        x = self.position(self.projection(x))
        return self.classifier(self.pool(self.encoder(x)))


def parameter_calculation():
    layers = dict(input_projection=64 * (9 + 1),
                  attention_qkv=3 * 64 * (64 + 1), attention_output=64 * (64 + 1),
                  feedforward_1=128 * (64 + 1), feedforward_2=64 * (128 + 1),
                  two_layer_norms=2 * 2 * 64, classifier=6 * (64 + 1))
    return dict(layers=layers, total=sum(layers.values()), positional_trainable_parameters=0,
                positional_buffer_values=128 * 64)
