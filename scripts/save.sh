#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v python >/dev/null 2>&1; then
    exec python -B -X utf8 scripts/maintain.py save "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 -B -X utf8 scripts/maintain.py save "$@"
else
    echo 'ERROR: Python 3.9+ is required.' >&2
    exit 1
fi
