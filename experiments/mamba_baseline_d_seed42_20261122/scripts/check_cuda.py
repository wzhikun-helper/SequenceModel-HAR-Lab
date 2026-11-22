"""Verify official source, CUDA extension calls, and gradients for L0."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mamba_baseline_d import MambaBaselineD
import selective_scan_cuda


def check_cuda(data, original, report):
    if version('mamba-ssm') != '2.2.6' or not torch.cuda.is_available():
        raise RuntimeError('The original Mamba v2.2.6 and CUDA must be available')
    import mamba_ssm.modules.mamba_simple as installed
    source = Path(installed.__file__).read_bytes()
    if source != (original / 'mamba_ssm/modules/mamba_simple.py').read_bytes():
        raise ValueError('Installed original Mamba module differs from official source')
    with np.load(data / 'train_standardized.npz', allow_pickle=False) as frozen:
        windows = torch.from_numpy(frozen['X'][:1]).to('cuda:0')
    torch.manual_seed(42)
    model = MambaBaselineD().cuda()
    with patch.object(selective_scan_cuda, 'fwd', wraps=selective_scan_cuda.fwd) as fwd, \
         patch.object(selective_scan_cuda, 'bwd', wraps=selective_scan_cuda.bwd) as bwd:
        result = model(windows)
        result.square().mean().backward()
        torch.cuda.synchronize()
    grad = model.block.in_proj.weight.grad
    if result.shape != (1, 6) or not result.is_cuda or not torch.isfinite(result).all().item():
        raise RuntimeError('CUDA output failed')
    if not (fwd.call_count == bwd.call_count == 1 and fwd.call_args.args[0].is_cuda
            and bwd.call_args.args[0].is_cuda and grad.is_cuda and torch.isfinite(grad).all().item()
            and torch.count_nonzero(grad).item() > 0):
        raise RuntimeError('Original official CUDA forward/backward or gradients failed')
    evidence = dict(status='PASS', mamba=version('mamba-ssm'), python=sys.version.split()[0],
                    torch=torch.__version__, cuda_runtime=torch.version.cuda,
                    gpu=torch.cuda.get_device_name(), compute_capability=torch.cuda.get_device_capability(),
                    official_module_sha256=hashlib.sha256(source).hexdigest(),
                    cuda_extension_sha256=hashlib.sha256(Path(selective_scan_cuda.__file__).read_bytes()).hexdigest(),
                    fwd_calls=fwd.call_count, bwd_calls=bwd.call_count,
                    gradient_nonzero=torch.count_nonzero(grad).item())
    with report.open('x', encoding='utf-8') as stream:
        json.dump(evidence, stream, indent=2)
        stream.write('\n')
    print(json.dumps(evidence), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    parser.add_argument('official_source', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    check_cuda(args.data, args.official_source, args.report)
