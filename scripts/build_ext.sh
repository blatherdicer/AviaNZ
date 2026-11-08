#!/usr/bin/env bash
# Compile AviaNZ's Cython/C extensions (ext/) in place, inside the project's uv environment.
# Re-run after changing Python version or anything in ext/.
set -euo pipefail
cd "$(dirname "$0")/../ext"
uv run --group build python setup.py build_ext --inplace
echo "Built extensions:"
ls -1 ./*.so
