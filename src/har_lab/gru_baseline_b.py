"""Approved unidirectional GRU baseline; final hidden state -> six logits."""
import torch
from torch import nn


class GRUBaselineB(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(input_size=9, hidden_size=64, num_layers=1,
                          bias=True, batch_first=True, dropout=0.0, bidirectional=False)
        self.classifier = nn.Linear(64, 6, bias=True)

    def forward(self, x):
        if x.ndim != 3 or x.shape[0] < 1 or tuple(x.shape[1:]) != (128, 9):
            raise ValueError('Expected nonempty [B,128,9] input')
        if not x.is_floating_point() or not torch.isfinite(x).all():
            raise ValueError('Expected finite floating-point input')
        _, h_n = self.gru(x)
        return self.classifier(h_n[-1])


def parameter_calculation():
    # Three gates; PyTorch has separate input-hidden and hidden-hidden bias vectors.
    layers = dict(weight_ih=3 * 64 * 9, weight_hh=3 * 64 * 64,
                  bias_ih=3 * 64, bias_hh=3 * 64, classifier=6 * (64 + 1))
    return dict(layers=layers, total=sum(layers.values()))
