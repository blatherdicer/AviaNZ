#!/usr/bin/env bash
# Build a self-contained AviaNZ.app for Apple-silicon Macs into dist/.
#   scripts/build_app.sh          build dist/AviaNZ.app
#   scripts/build_app.sh --dmg    also create dist/AviaNZ-<version>.dmg
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)/$(uname -m)" != "Darwin/arm64" ]]; then
    echo "This build targets Apple-silicon macOS only." >&2; exit 1
fi

uv sync --group bundle            # locked deps + PyInstaller
scripts/build_ext.sh              # C/Cython extensions for this Python

uv run --group bundle pyinstaller --noconfirm --clean \
    --distpath dist --workpath build/pyinstaller packaging/AviaNZ.spec

APP=dist/AviaNZ.app
codesign --verify --deep --strict "$APP"
echo "Built $APP ($(du -sh "$APP" | cut -f1))"

if [[ "${1:-}" == "--dmg" ]]; then
    VERSION=$(uv run --no-sync python -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
    STAGE=build/dmg; rm -rf "$STAGE"; mkdir -p "$STAGE"
    cp -R "$APP" "$STAGE/"; ln -s /Applications "$STAGE/Applications"
    hdiutil create -volname "AviaNZ $VERSION" -srcfolder "$STAGE" -ov -format UDZO "dist/AviaNZ-$VERSION.dmg"
    echo "Built dist/AviaNZ-$VERSION.dmg"
fi
