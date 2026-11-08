# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for a self-contained, Apple-silicon AviaNZ.app.
# Build with scripts/build_app.sh (do not run pyinstaller on this directly).
import glob
import importlib.util
import os
import tomllib

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
    VERSION = tomllib.load(f)["project"]["version"]

# Read-only resources that AviaNZ opens relative to its own directory.
datas = [
    (os.path.join(ROOT, "Config"), "Config"),
    (os.path.join(ROOT, "Filters"), "Filters"),
    (os.path.join(ROOT, "Wavelets"), "Wavelets"),
    (os.path.join(ROOT, "img"), "img"),
]

# Compiled C/Cython extensions (scripts/build_ext.sh). dpss.py loads mydpss via ctypes from ./ext.
ext_libs = glob.glob(os.path.join(ROOT, "ext", "*.so"))
if len(ext_libs) < 4:
    raise SystemExit("ext/ extensions missing - run scripts/build_ext.sh first")
binaries = [(p, "ext") for p in ext_libs]

# Apple Metal plugin for TensorFlow. TensorFlow does not auto-load it inside a bundle;
# metal_compat.apply() loads it from <bundle>/tensorflow-plugins.
site_packages = os.path.dirname(os.path.dirname(importlib.util.find_spec("tensorflow").origin))
metal = os.path.join(site_packages, "tensorflow-plugins", "libmetal_plugin.dylib")
if not os.path.isfile(metal):
    raise SystemExit("tensorflow-metal not installed in the build environment")
binaries.append((metal, "tensorflow-plugins"))

a = Analysis(
    [os.path.join(ROOT, "AviaNZ.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=["metal_compat"],
    excludes=["tkinter", "IPython", "jupyter", "notebook", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AviaNZ",
    console=False,          # GUI app; CLI still works when the binary is run from a terminal
    target_arch="arm64",
    codesign_identity=None,  # ad-hoc signature (local use); set a Developer ID to distribute
)
coll = COLLECT(exe, a.binaries, a.datas, name="AviaNZ")
app = BUNDLE(
    coll,
    name="AviaNZ.app",
    icon=os.path.join(ROOT, "img", "avianz.icns"),
    bundle_identifier="com.blatherdicer.avianz",
    version=VERSION,
    info_plist={
        "CFBundleName": "AviaNZ",
        "CFBundleDisplayName": "AviaNZ",
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "LSMinimumSystemVersion": "12.0",   # tensorflow-metal requirement
        "LSArchitecturePriority": ["arm64"],
        "NSHighResolutionCapable": True,
    },
)
