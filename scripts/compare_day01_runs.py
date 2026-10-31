"""Compare two completed real-data runs without changing either run."""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageChops

from day01_audit_uci import ROOT, safe, jwrite
from verify_day01_data import digest


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main(reference, candidate, output):
    for value in [reference, candidate]:
        if not value.replace('_', '').isalnum():
            raise ValueError('Run IDs must use letters, numbers and underscores')
    output = safe(ROOT / output)
    output.mkdir(parents=True, exist_ok=False)
    report = {'reference': reference, 'candidate': candidate, 'attempt': 'audit02', 'checks': {},
              'scope': 'Actual archived files and arrays, not model evaluation.'}
    for name in [reference, candidate]:
        assert read(ROOT / 'reports' / name / 'download_provenance.json')['status'] == 'COMPLETE'
        assert read(ROOT / 'reports' / name / 'audit02/audit_results.json')['status'] == 'COMPLETE'
        assert read(ROOT / 'reports' / name / 'independent_verification.json')['status'] == 'PASS'
    old = ROOT / 'data/processed' / (reference + '_audit02')
    new = ROOT / 'data/processed' / (candidate + '_audit02')
    p0 = read(ROOT / 'reports' / reference / 'download_provenance.json')
    p1 = read(ROOT / 'reports' / candidate / 'download_provenance.json')
    report['checks']['official_archive_sha256_equal'] = p0['sha256'] == p1['sha256']
    report['checks']['inner_archive_sha256_equal'] = p0['inner_archive']['sha256'] == p1['inner_archive']['sha256']
    report['checks']['sample_manifest_bytes_equal'] = digest(old / 'splits/sample_manifest.csv') == digest(new / 'splits/sample_manifest.csv')
    report['checks']['split_metadata_equal'] = read(old / 'splits/split_metadata.json') == read(new / 'splits/split_metadata.json')
    s0, s1 = read(old / 'scaler_train_only.json'), read(new / 'scaler_train_only.json')
    report['checks']['scaler_metadata_equal'] = s0 == s1
    report['scaler_max_mean_abs_difference'] = float(np.max(np.abs(np.array(s0['mean']) - s1['mean'])))
    report['scaler_max_std_abs_difference'] = float(np.max(np.abs(np.array(s0['std']) - s1['std'])))
    arrays = {}
    for split in ['train', 'validation', 'test']:
        filename = split + '_standardized.npz'
        with np.load(old / filename, allow_pickle=False) as a, np.load(new / filename, allow_pickle=False) as b:
            same_keys = set(a.files) == set(b.files)
            equal = same_keys and all(a[key].dtype == b[key].dtype and np.array_equal(a[key], b[key]) for key in a.files)
            arrays[split] = {'all_fields_equal': equal, 'shape': list(b['X'].shape),
                             'dtype': str(b['X'].dtype), 'container_sha256_equal': digest(old / filename) == digest(new / filename),
                             'max_X_abs_difference': float(np.max(np.abs(a['X'] - b['X'])))}
            report['checks'][split + '_arrays_exactly_equal'] = equal
    report['arrays'] = arrays
    figures = {}
    for activity in ['walking', 'standing']:
        a = ROOT / 'outputs/figures' / (reference + '_audit02') / ('fig01_' + activity + '_nine_channels')
        b = ROOT / 'outputs/figures' / (candidate + '_audit02') / ('fig01_' + activity + '_nine_channels')
        with Image.open(a.with_suffix('.png')) as ia, Image.open(b.with_suffix('.png')) as ib:
            same_pixels = ia.size == ib.size and ImageChops.difference(ia.convert('RGB'), ib.convert('RGB')).getbbox() is None
        report['checks'][activity + '_png_pixels_equal'] = same_pixels
        vectors = {}
        for extension in ['svg', 'pdf']:
            vectors[extension + '_bytes_equal'] = digest(a.with_suffix('.' + extension)) == digest(b.with_suffix('.' + extension))
        roots = [ET.parse(path.with_suffix('.svg')) for path in [a, b]]
        geometry = [[node.attrib['d'] for node in tree.iter() if node.tag.endswith('}path') and 'd' in node.attrib] for tree in roots]
        texts = [[node.text for node in tree.iter() if node.tag.endswith('}text')] for tree in roots]
        vectors['svg_path_geometry_equal'] = geometry[0] == geometry[1]
        vectors['svg_text_equal'] = texts[0] == texts[1]
        vectors['svg_dates'] = [[node.text for node in tree.iter() if node.tag.endswith('}date')] for tree in roots]
        vectors['pdf_creation_dates'] = [re.findall(rb'/CreationDate\s*\(([^)]*)\)', path.with_suffix('.pdf').read_bytes())[0].decode('ascii', errors='replace') for path in [a, b]]
        report['checks'][activity + '_svg_geometry_and_text_equal'] = vectors['svg_path_geometry_equal'] and vectors['svg_text_equal']
        figures[activity] = {'png_pixels_equal': same_pixels, **vectors}
    report['figures'] = figures
    report['status'] = 'PASS' if all(report['checks'].values()) else 'DIFFERENCES_FOUND'
    report['interpretation'] = ('Numerical and image checks are reported separately from file-byte equality. '
                                'PDF/SVG byte differences and observed creation dates are preserved, not hidden. '
                                'Matching SVG path geometry/text does not claim all vector metadata bytes match.')
    jwrite(output / 'comparison.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference')
    parser.add_argument('candidate')
    parser.add_argument('output_directory', help='New project-relative report directory')
    args = parser.parse_args()
    main(args.reference, args.candidate, args.output_directory)
