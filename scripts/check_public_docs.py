"""Read-only checks for public entry points; standard library only.

Historical transcripts/reports intentionally retain execution-machine paths.
This checks curated entry pages, their assets, and published metadata, not those archives.
"""
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    'README.md', 'README.en.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
    'PROGRESS.md', 'docs/README.md', 'docs/data_protocol.md',
    'docs/reproducing_day01.md', 'docs/day01/README.md',
    'learning_notes/day01/README.md', 'scripts/README.md', 'reports/README.md',
]


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            if not attrs.get('alt'):
                self.errors.append('image is missing alt text')
            if attrs.get('src'):
                self.links.append(attrs['src'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def main():
    errors = []
    link_count = 0
    for name in PAGES:
        page = ROOT / name
        if not page.is_file():
            errors.append('missing entry page: ' + name)
            continue
        text = page.read_text(encoding='utf-8')
        require(text.count('```') % 2 == 0, name + ': unclosed code fence', errors)
        require(text.count('<details>') == text.count('</details>'), name + ': unclosed details block', errors)
        visible = re.sub(r'```.*?```', '', text, flags=re.S)
        html = HTMLLinks()
        html.feed(visible)
        errors.extend(name + ': ' + error for error in html.errors)
        links = re.findall(r'!?\[[^\]\n]*\]\(([^\s)]+)\)', visible) + html.links
        for target in links:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = (page.parent / unquote(parsed.path)).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(name + ': link escapes repository: ' + target)
                continue
            require(resolved.exists(), name + ': missing local target: ' + target, errors)
            link_count += 1
    for script in sorted((ROOT / 'scripts').glob('*.py')):
        try:
            ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
        except SyntaxError as exc:
            errors.append(script.name + ': ' + str(exc))

    meta = json.loads((ROOT / 'docs/day01/split_metadata.json').read_text(encoding='utf-8'))
    scaler = json.loads((ROOT / 'docs/day01/standardization_train_only.json').read_text(encoding='utf-8'))
    splits = meta['splits']
    groups = {name: set(values['subjects']) for name, values in splits.items()}
    require(groups['validation'] == {1, 3, 5, 6}, 'validation metadata changed', errors)
    require(not (groups['train'] & groups['validation'] or groups['train'] & groups['test'] or
                 groups['validation'] & groups['test']), 'published subject sets overlap', errors)
    for name, expected in [('train', 6037), ('validation', 1315), ('test', 2947)]:
        require(splits[name]['n_windows'] == expected, name + ': window count mismatch', errors)
        require(sum(splits[name]['class_counts'].values()) == expected, name + ': class counts mismatch', errors)
    require(scaler['fit_subject_ids'] == splits['train']['subjects'], 'scaler provenance mismatch', errors)
    require(scaler['sample_manifest_sha256'] == meta['sample_manifest_sha256'], 'split/scaler hash mismatch', errors)
    require(len(scaler['channels']) == len(scaler['mean']) == len(scaler['std']) == 9,
            'scaler channel dimension mismatch', errors)
    require(scaler['fit_values_per_channel'] == 6037 * 128 and scaler['ddof'] == 0,
            'scaler fitting definition mismatch', errors)

    assets = json.loads((ROOT / 'docs/day01/asset_provenance.json').read_text(encoding='utf-8'))
    for asset in assets:
        path = ROOT / asset['documentation_copy']
        content = path.read_bytes()
        require(hashlib.sha256(content).hexdigest() == asset['sha256'],
                path.name + ': published asset hash mismatch', errors)
        require(len(content) == asset['bytes'], path.name + ': asset size mismatch', errors)
        if path.suffix == '.png':
            require(content[:8] == b'\x89PNG\r\n\x1a\n', path.name + ': invalid PNG signature', errors)
            require(struct.unpack('>II', content[16:24]) == (2460, 3450), path.name + ': PNG dimensions changed', errors)
    if errors:
        for error in errors:
            print('FAIL:', error)
        raise SystemExit(1)
    print(f'PASS: {len(PAGES)} public entry pages, {link_count} local references, Python syntax and published metadata/assets.')
    print('Scope: offline documentation checks; no raw data, preprocessing, model training or external-link requests.')


if __name__ == '__main__':
    main()
