# PyInstaller runtime hook: give matplotlib a persistent config/cache directory.
# PyInstaller's default hook (pyi_rth_mplconfig, removed in AviaNZ.spec) uses a new
# temporary directory on every launch, so matplotlib rebuilt its font cache each time
# (~20 s added to every start of AviaNZ.app).
import os
import sys

if getattr(sys, "frozen", False) and "MPLCONFIGDIR" not in os.environ:
    _d = os.path.join(os.path.expanduser("~"), "Library", "Caches", "AviaNZ", "matplotlib")
    try:
        os.makedirs(_d, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = _d
    except OSError:
        pass  # matplotlib falls back to its own temporary directory
