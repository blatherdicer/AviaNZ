# CLAUDE.md

AviaNZ is a PyQt6 desktop app for annotating and recognising bird and bat calls in field recordings. Recognisers are wavelet filters plus TensorFlow/Keras CNNs. This repo is a **personal fork** (`blatherdicer/AviaNZ`). Its purpose is to run upstream AviaNZ natively on Apple-silicon Macs, with Metal GPU acceleration and modern dependency management.

## Repo and remotes: rules
- `origin` = `fork` = `git@github.com:blatherdicer/AviaNZ.git` (the user's fork). `upstream` = `smarsland/AviaNZ`.
- **Never push to `upstream`.** Contributing upstream is a possible future option, and only the user decides it. Push to `origin` only when asked.
- Branches:
  - `mac-arm64`: the current work, based on `upstream/master`, with no upstream tracking set.
  - `legacy/pyqt5` and tag `pyqt5-legacy`: the 2023 PyQt5 / TF 2.12 / Miniforge port. Kept for history; don't build on it.
  - `master`: still points at the 2023 work, the same commit as `legacy/pyqt5`.
- Upstream's `refactoring_with_model_testing` branch is moving to PyTorch (MPS). The user has said this is future work; don't adopt it unless asked.

## Scope rule (from the user)
Keep changes to what makes AviaNZ run correctly on M-series Macs: dependencies, Metal, packaging, and breakage specific to macOS. Bugs that also happen on other platforms, or upstream behaviour changes, get **reported to the user, not fixed**, unless they agree first. The same goes for widening test scope. Known upstream issues are listed in README.md under "Known upstream issues".

## Environment
- uv only: `pyproject.toml` + `uv.lock` + `.python-version` (3.12). `python-preference = "only-managed"`: the machine has an Intel Homebrew Python in `/usr/local` that must never be used.
- Setup: `uv sync && scripts/build_ext.sh`. Run: `uv run python AviaNZ.py`. App: `scripts/build_app.sh [--dmg]`, which builds `dist/AviaNZ.app` from `packaging/AviaNZ.spec` (PyInstaller, in the `bundle` dependency group).
- Version constraints, each for a tested reason (see the README table): TF `<2.20` (tensorflow-metal 1.2.0 breaks on 2.20+), Python `<3.13` (no tensorflow-metal wheels), scipy `>=1.16.3` (the macOS 27 loader rejects 1.15), numpy `<2.2` (TF 2.19).
- Upstream's `requirements.txt` is left as upstream has it. `pyproject.toml` is the source of truth here.
- The user's shell may have a stale `VIRTUAL_ENV` (an old pipenv project). uv ignores it with a warning.

## Metal (do not remove without re-testing)
- `metal_compat.apply()` is called on import in `NNModels.py` and `NN.py`. On Apple silicon it disables Grappler's meta-optimizer, because tensorflow-metal >=1.0 computes the fused Dense+ReLU wrongly on the GPU.
- Inside the app bundle it also loads `<_MEIPASS>/tensorflow-plugins`, but only if no GPU is registered yet. Loading the plugin twice aborts with "platform is already registered".
- `uv run python scripts/check_metal.py` reports whether the bug still exists and whether the workaround fixes it. Run it after any TF or tensorflow-metal upgrade.
- App start-up: `packaging/AviaNZ.spec` removes PyInstaller's `pyi_rth_mplconfig` hook, which used a new temp `MPLCONFIGDIR` on every launch and so rebuilt matplotlib's font cache each time (about 20 s per start). In its place, `packaging/rthook_mplconfig.py` uses `~/Library/Caches/AviaNZ/matplotlib`. Only the first launch builds the cache.
- Environment variables: `AVIANZ_DISABLE_GPU=1` (CPU only), `AVIANZ_METAL_WORKAROUND=0` (testing only), `AVIANZ_CONFIG_DIR` (overrides `~/.avianz`).

## Testing approach that worked
- Headless batch: `QT_QPA_PLATFORM=offscreen AVIANZ_CONFIG_DIR=<scratch> sh -c 'yes y | uv run python AviaNZ.py -c -b -d <dir> -r "<Recogniser>"'`. Batch asks "Confirm? [y/n]" on stdin.
- Batch overwrites `.data` files in the target folder, so always work on copies of `Sound Files/`, never the originals.
- Validate GPU against CPU, and the new build against the old, by comparing the `.data` outputs. Metal and CPU gave identical detections for all bird recognisers in both the dev environment and the app.
- Never point tests at the real `~/.avianz`. It may contain 2023 filters in the old `"CNN"` format, whose neural-net stage is silently skipped. Use `AVIANZ_CONFIG_DIR`.
- Don't name scratch scripts after standard-library modules (for example `bisect.py`); they shadow the real module.
