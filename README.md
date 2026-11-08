Welcome to AviaNZ, an open-source project for manual and automatic analysis of bio-acoustic recordings.

This software enables you to: 
* review and listen to wav files from acoustic field recorders, 
* segment and annotate the recordings, 
* train filters to recognise calls from particular species, 
* use filters that others have provided to batch process many files
* review annotations
* produce output in spreadsheet form, or as files ready for further statistical analyses

For more information about the project, see http://www.avianz.net

# Citation

If you use this software, please credit us in any papers that you write. An appropriate reference is:

```
@article{Marsland19,
  title = "AviaNZ: A future-proofed program for annotation and recognition of animal sounds in long-time field recordings",
  author = "{Marsland}, Stephen and {Priyadarshani}, Nirosha and {Juodakis}, Julius and {Castro}, Isabel",
  journal = "Methods in Ecology and Evolution",
  volume = 10,
  number = 8,
  pages = "1189--1195",
  year = 2019
}
```


# Installation

## Windows
Windows binaries are available at http://www.avianz.net.
To install from source, follow the Linux instructions.

## macOS
An installer script is available at http://www.avianz.net.
To install from source on an Apple-silicon Mac (M1 and later), see the next section. On Intel Macs, follow the Linux instructions.

## Apple-silicon Macs (fork: blatherdicer/AviaNZ, branch `mac-arm64`)
This branch runs AviaNZ natively on M-series Macs, with neural-net inference on the GPU through Apple's `tensorflow-metal`. It is based on upstream `smarsland/AviaNZ` `master`. No Miniforge, conda or Homebrew Python is needed: [uv](https://docs.astral.sh/uv/) manages Python and all dependencies from `pyproject.toml` and `uv.lock`.

### Run from source
```
brew install uv                  # or: curl -LsSf https://astral.sh/uv/install.sh | sh
xcode-select --install           # C compiler for the extensions, if not already installed
uv sync                          # installs Python 3.12 (arm64) and the locked dependencies into .venv
scripts/build_ext.sh             # compiles the Cython/C extensions in ext/
uv run python scripts/check_metal.py   # optional: confirms the GPU gives correct results
uv run python AviaNZ.py
```

### Build a standalone app
```
scripts/build_app.sh             # -> dist/AviaNZ.app (about 1.4 GB, ad-hoc signed, arm64 only)
scripts/build_app.sh --dmg       # also dist/AviaNZ-<version>.dmg
```
Copy `dist/AviaNZ.app` to `/Applications`. The app bundles Python, Qt, TensorFlow with the Metal plugin, the C extensions, and the default config and recognisers. It is ad-hoc signed, which is fine on the Mac that built it. To give it to other people, it would need to be signed with an Apple Developer ID and notarized. Batch mode also works from a terminal: `/Applications/AviaNZ.app/Contents/MacOS/AviaNZ -c -b -d <folder> -r "<recogniser>"`.

### Versions and why
| Component | Version | Reason |
|---|---|---|
| Python | 3.12 (uv-managed only) | `tensorflow-metal` 1.2.0 has no wheels for 3.13+. `python-preference = "only-managed"` stops uv from picking up an Intel Python on `PATH` |
| tensorflow | 2.19.x (`<2.20`) | `tensorflow-metal` 1.2.0 fails to load with TF 2.20 and 2.21 |
| tensorflow-metal | 1.2.0 | Latest release (Jan 2025). Installed only on macOS arm64 |
| scipy | 1.16.x | macOS 27's loader rejects SciPy 1.15 binaries (`__thread_bss ... offset field is not zero`) |
| PyQt6 | 6.12 | Qt comes bundled in the wheel; no Homebrew Qt needed |

### Metal GPU correctness workaround
With `tensorflow-metal` 1.0 and later (tested 1.1.0 and 1.2.0 on TF 2.15 to 2.19), the fused MatMul + BiasAdd + ReLU kernel that TensorFlow's graph optimizer builds for `Dense(..., activation='relu')` **returns wrong values on the GPU**. Every AviaNZ CNN ends in such a layer, so predictions were off by up to 1.0 in class probability. `metal_compat.py` disables the Grappler meta-optimizer on Apple silicon only. Results then match the CPU to about 1e-7, and the neural net runs 7 to 12 times faster than on the CPU. Note that in batch processing most of the time goes on wavelet segmentation, so whole runs are not much faster than CPU-only.
- `uv run python scripts/check_metal.py` shows whether the bug still exists in the installed plugin and that the workaround fixes it.
- `AVIANZ_DISABLE_GPU=1` runs TensorFlow on the CPU only. `AVIANZ_METAL_WORKAROUND=0` turns the workaround off (for testing only).

### Configuration folder
AviaNZ keeps settings and recognisers in `~/.avianz` and only copies in recognisers that are missing. Recogniser files from AviaNZ 3.2 or earlier use a `"CNN"` key, which current AviaNZ ignores: their neural-net stage is skipped **without any warning**. If you have an old `~/.avianz`, rename it so a fresh one is created. Set `AVIANZ_CONFIG_DIR=<folder>` to use a different folder (for example, to test side by side).

### Known upstream issues (not Mac-specific, left unfixed here)
- **NZ Bats does not work.** `Filters/NZ Bats.h5` is a Keras 2.2 full-model file that Keras 3 cannot load. Separately, batch mode marks zero segments for `.bmp` bat files, because the page count now uses the audio length, which is 0 for an image.
- Compared with AviaNZ 3.2, some results differ because upstream changed things: the Morepork thresholds were raised, Bittern segment boundaries shifted, the reported certainty for some kiwi detections changed from 90 to 50, and spectrogram preprocessing changed, which moves borderline neural-net scores.
- Upstream is moving to PyTorch on its `refactoring_with_model_testing` branch. The official AviaNZ 3.4 Mac app (Nov 2025) is built from that line and runs on the CPU only.

### History
The earlier PyQt5 / TF 2.12 / Miniforge port for M1 (2023) is kept on the `legacy/pyqt5` branch and the `pyqt5-legacy` tag.

## Linux
No binaries are available. Install from the source as follows:
1. Download the source .zip of the latest release.
2. Extract (`unzip v2.0.zip`) and navigate to the extracted directory.
3. Ensure Python (3.6 or higher), pip and git are available on your system. On Ubuntu, these can be installed by running:  
```
sudo apt-get install python3.6
sudo apt-get install python3-pip
sudo apt-get install git
```
4. Install the required packages by running `pip3 install -r requirements.txt --user` at the command line. (On Ubuntu and some other systems, `python` and `pip` refer to the Python 2 versions. If you are sure these refer to version 3 of the language, use `python` and `pip` in steps 4-6.)  
5. Build the Cython extensions by running `cd ext; python3 setup.py build_ext -i; cd..`  
6. Done! Launch the software with `python3 AviaNZ.py`  

# Acknowledgements

AviaNZ is based on PyQtGraph and PyQt, and uses Librosa and Scikit-learn amongst others.

Development of this software was supported by the RSNZ Marsden Fund, and the NZ Department of Conservation.
