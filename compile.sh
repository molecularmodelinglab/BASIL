#!/usr/bin/env bash
# Cross-platform wrapper: delegates to the Python build script.
# On Windows PowerShell, prefer running:  py -3 build.py [options]
# On macOS/Linux bash:                    python3 build.py [options]

set -euo pipefail

if command -v python >/dev/null 2>&1; then
	python3 build.py "$@"
elif command -v py >/dev/null 2>&1; then
	py -3 build.py "$@"
else
	python build.py "$@"
fi
