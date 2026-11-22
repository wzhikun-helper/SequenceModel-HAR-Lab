"""Reproduce historical Windows NPZ packaging from audited Linux UCI arrays."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np


def restore(project, rebuilt, output, evidence):
    historical = json.loads((project / 'reports/mamba_l0_20261122/project_audit.json').read_text())
    linux_audit = json.loads(evidence.read_text())
    if linux_audit['status'] != 'PASS':
        raise ValueError('Rebuilt UCI data audit must pass first')
    expected = {Path(k).name: v for k, v in historical['frozen_inputs'].items()
                if k.endswith('.npz') or k.endswith('/scaler_train_only.json')}
    payloads = {}
    for name, digest in expected.items():
        source = (rebuilt / name).read_bytes()
        if hashlib.sha256(source).hexdigest() != linux_audit['rebuilt_sha256'][name]:
            raise ValueError(f'Audited input changed: {name}')
        if name.endswith('.json'):
            payloads[name] = (project / 'docs/day01/standardization_train_only.json').read_bytes()
        else:
            packed = io.BytesIO()
            with np.load(io.BytesIO(source), allow_pickle=False) as arrays, \
                 zipfile.ZipFile(packed, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for key in arrays.files:
                    value = arrays[key]
                    if key == 'official_row_1based':
                        # NumPy 1.x used 32-bit native integers on 64-bit Windows.
                        value = value.astype('<i4')
                    entry = zipfile.ZipInfo(key + '.npy')
                    entry.create_system = 0
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    with archive.open(entry, 'w', force_zip64=True) as member:
                        np.lib.format.write_array(member, value, allow_pickle=False)
            payloads[name] = packed.getvalue()
        if hashlib.sha256(payloads[name]).hexdigest() != digest:
            raise ValueError(f'Recreated historical bytes do not match: {name}')
    output.mkdir()
    for name, payload in payloads.items():
        with (output / name).open('xb') as stream:
            stream.write(payload)
    print(json.dumps(dict(status='PASS', frozen_sha256=expected), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('rebuilt', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    restore(args.project, args.rebuilt, args.output, args.evidence)
