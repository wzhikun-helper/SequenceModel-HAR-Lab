"""Download only UCI's official archive; validate and extract into fresh directories."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import traceback
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://archive.ics.uci.edu/static/public/240/human%2Bactivity%2Brecognition%2Busing%2Bsmartphones.zip'
PAGE = 'https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones'
RUN = sys.argv[1]
if not RUN.replace('_', '').replace('-', '').isalnum():
    raise ValueError('Unsafe run ID')
RAW = ROOT / 'data' / 'raw' / RUN
REPORT = ROOT / 'reports' / RUN
LOG = ROOT / 'logs' / (RUN + '_download.log')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def ensure_safe(path):
    path = Path(os.path.abspath(path))
    path.relative_to(ROOT)
    for p in [path, *path.parents]:
        if p.exists() and (p.is_symlink() or (getattr(p.lstat(), 'st_file_attributes', 0) & 1024)):
            raise ValueError('Linked/reparse output component: ' + str(p))
        if p == ROOT:
            break


def extract_checked(archive, target):
    ensure_safe(target)
    target.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        if bad is not None:
            raise ValueError('ZIP CRC failure: ' + bad)
        members = []
        seen = set()
        for item in z.infolist():
            name = PurePosixPath(item.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in item.filename or ':' in item.filename:
                raise ValueError('Unsafe ZIP member: ' + item.filename)
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('ZIP symlink rejected')
            if item.is_dir():
                continue
            destination = target.joinpath(*name.parts)
            key = str(destination).lower()
            if key in seen:
                raise ValueError('Duplicate ZIP member')
            seen.add(key)
            ensure_safe(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with z.open(item) as source, destination.open('xb') as out:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    out.write(block)
            members.append({'path': destination.relative_to(ROOT).as_posix(),
                            'size': item.file_size, 'crc32': format(item.CRC, '08x'),
                            'sha256': sha256(destination)})
    return {'archive': archive.relative_to(ROOT).as_posix(), 'crc_all_members': 'PASS',
            'files': members}


for path in [RAW, REPORT, LOG]:
    ensure_safe(path)
RAW.mkdir(parents=True, exist_ok=False)
REPORT.mkdir(parents=True, exist_ok=False)
record = {'run_id': RUN, 'source_page': PAGE, 'download_url': URL,
          'started_at': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
          'status': 'STARTED', 'official_published_sha256': None,
          'checksum_scope': 'Local SHA256 + HTTP Content-Length + ZIP CRC; no publisher checksum was supplied by the official page.'}
with LOG.open('x', encoding='utf-8', buffering=1) as log:
    def say(message):
        print(message, flush=True)
        log.write(message + '\n')
    try:
        baseline = {p.relative_to(ROOT).as_posix(): sha256(p) for p in [
            ROOT / '.gitignore', ROOT / 'README.md', ROOT / 'reports/day01_startup_check.md',
            ROOT / 'scripts/check_day01.ps1']}
        write_json(REPORT / 'existing_files_baseline.json', baseline)
        archive = RAW / 'human_activity_recognition_using_smartphones.zip'
        say('GET ' + URL)
        request = urllib.request.Request(URL, headers={'User-Agent': 'SequenceModel-HAR-Lab-Day01/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response, archive.open('xb') as out:
            if urllib.parse.urlparse(response.geturl()).hostname != 'archive.ics.uci.edu':
                raise ValueError('Download redirected outside official UCI host')
            record['http_status'] = response.status
            record['final_url'] = response.geturl()
            record['headers'] = {k: response.headers.get(k) for k in ['Content-Length', 'Content-Type', 'ETag', 'Last-Modified']}
            total = 0
            last_progress = 0
            for block in iter(lambda: response.read(1024 * 1024), b''):
                out.write(block)
                total += len(block)
                if total - last_progress >= 10 * 1024 * 1024:
                    say('Downloaded bytes: ' + str(total))
                    last_progress = total
        record['downloaded_bytes'] = archive.stat().st_size
        record['sha256'] = sha256(archive)
        record['filename'] = archive.name
        record['relative_path'] = archive.relative_to(ROOT).as_posix()
        length = record['headers']['Content-Length']
        if length is not None and int(length) != record['downloaded_bytes']:
            raise ValueError('HTTP Content-Length mismatch')
        say('Download complete: ' + str(record['downloaded_bytes']) + ' bytes; SHA256=' + record['sha256'])
        outer_dir = RAW / 'official_bundle'
        checks = [extract_checked(archive, outer_dir)]
        candidates = list(outer_dir.rglob('UCI HAR Dataset.zip'))
        if len(candidates) == 1:
            inner = candidates[0]
            record['inner_archive'] = {'path': inner.relative_to(ROOT).as_posix(),
                                       'bytes': inner.stat().st_size, 'sha256': sha256(inner)}
            checks.append(extract_checked(inner, RAW / 'extracted'))
            roots = list((RAW / 'extracted').rglob('activity_labels.txt'))
        else:
            roots = list(outer_dir.rglob('activity_labels.txt'))
        if len(roots) != 1:
            raise ValueError('Expected exactly one UCI HAR dataset root')
        record['dataset_root'] = roots[0].parent.relative_to(ROOT).as_posix()
        write_json(REPORT / 'archive_integrity.json', checks)
        record['status'] = 'COMPLETE'
        say('All ZIP member CRC checks passed. Dataset root: ' + record['dataset_root'])
    except Exception as exc:
        record['status'] = 'FAILED'
        record['error_type'] = type(exc).__name__
        record['error'] = str(exc)
        say(traceback.format_exc())
    finally:
        record['finished_at'] = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
        write_json(REPORT / 'download_provenance.json', record)
    if record['status'] != 'COMPLETE':
        say('Download/extraction failed; no alternative source attempted. Subsequent data steps NOT RUN.')
        sys.exit(1)
