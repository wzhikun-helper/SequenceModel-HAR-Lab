"""UCI HAR classifier using the official original Mamba block."""
from mamba_ssm.modules.mamba_simple import Mamba
from torch import nn


class MambaBaselineD(nn.Module):
    def __init__(self, d_model=64, d_state=16, d_conv=4, expand=2):
        super().__init__()
        self.projection = nn.Linear(9, d_model)
        self.block = Mamba(d_model=d_model, d_state=d_state, d_conv=d_conv,
                           expand=expand, use_fast_path=False)
        self.classifier = nn.Linear(d_model, 6)

    def forward(self, windows):
        sequence = self.block(self.projection(windows))
        return self.classifier(sequence.mean(dim=1))
