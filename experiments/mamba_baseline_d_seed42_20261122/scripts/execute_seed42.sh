#!/usr/bin/env bash
# All three commands use fresh outputs. Run from the standalone project root.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
python=environment/runtime/bin/python
project=environment/repository
official=environment/mamba-d7b1ceb3c367ec9022925e812f507bcf706937c6
mkdir -p logs
run_stage() {
    local name=$1
    shift
    local status=0 start
    start=$(date +%s)
    (
        set -o noclobber
        printf 'UTC start %s\n' "$(date -u +%FT%TZ)"
        printf 'Command'
        printf ' %q' "$@"
        printf '\n'
        "$@" || status=$?
        printf 'Exit code %s\nElapsed seconds %s\n' "$status" "$(( $(date +%s) - start ))"
        exit "$status"
    ) > "logs/$name.log" 2>&1
}
run_stage L0-cuda "$python" -B -u scripts/check_cuda.py data/frozen "$official" audit/cuda_runtime.json
run_stage L1-L2-seed42 "$python" -B -u scripts/run_mamba.py --project "$project" --data data/frozen
run_stage L3-compare "$python" -B -u scripts/verify_and_compare.py "$project" data/frozen .
