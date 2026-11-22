#!/usr/bin/env bash
# Build the official v2.2.6 extension using preinstalled isolated prefixes.
set -euo pipefail
if [[ $# != 4 ]]; then
    echo "Usage: build_mamba.sh RUNTIME_PREFIX TOOLCHAIN_PREFIX SOURCE_TAR BUILD_DIR" >&2
    exit 2
fi
runtime="$(realpath "$1")"
export CUDA_HOME="$(realpath "$2")"
source_tar="$(realpath "$3")"
mkdir "$4"
build="$(realpath "$4")"
export PATH="$runtime/bin:$CUDA_HOME/bin:$PATH"
export CC="$CUDA_HOME/bin/x86_64-conda-linux-gnu-gcc"
export CXX="$CUDA_HOME/bin/x86_64-conda-linux-gnu-g++"
export MAMBA_FORCE_BUILD=TRUE
export MAX_JOBS=4
nvcc --version
"$CXX" --version
sha256sum "$source_tar"
tar --strip-components=1 -xzf "$source_tar" -C "$build"
cd "$build"
python - <<'PY'
from pathlib import Path
import difflib
import re

setup = Path('setup.py')
original = setup.read_text()
start = original.index('        if bare_metal_version <= Version("12.9"):')
finish = original.index('    # HACK:', start)
patched = original[:start] + '        cc_flag.extend(["-gencode", "arch=compute_86,code=sm_86"])\n\n' + original[finish:]
patched, matched = re.subn(r'\["--threads", "4"\]', '["--threads", "1"]', patched)
if matched != 1:
    raise RuntimeError('Unexpected upstream CUDA build settings')
setup.write_text(patched)
diff = difflib.unified_diff(original.splitlines(keepends=True), patched.splitlines(keepends=True),
                            fromfile='upstream/setup.py', tofile='build/setup.py')
Path('architecture_build.patch').write_text(''.join(diff))
PY
set -x
python -m pip --isolated wheel --no-build-isolation --no-deps --no-index -w wheels .
sha256sum wheels/*.whl
python -m pip --isolated install --no-index --no-deps wheels/*.whl
python -m pip check
