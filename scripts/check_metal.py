"""Check that TensorFlow on the Metal GPU gives correct results in AviaNZ's setup.

    uv run python scripts/check_metal.py

It runs the minimal reproduction of the tensorflow-metal fused-Dense bug twice: once
without the metal_compat shim (to show whether the bug still exists in the installed
tensorflow-metal) and once with it (what AviaNZ actually uses). Exit code 0 means
AviaNZ's configuration is correct. If the "without shim" run starts passing after an
upgrade, the shim in metal_compat.py may no longer be needed.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 1e-3


def run_case():
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    sys.path.insert(0, ROOT)
    import numpy as np
    import tensorflow as tf
    import metal_compat
    metal_compat.apply(verbose=False)

    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        print("  no GPU visible to TensorFlow - nothing to check (CPU only)")
        return 0
    rng = np.random.default_rng(0)
    worst = 0.0
    for k, n in [(512, 256), (3136, 256), (6912, 256)]:  # sizes used by AviaNZ CNNs
        w = rng.standard_normal((k, n)).astype("f4") * 0.05
        b = rng.standard_normal(n).astype("f4")
        x = rng.random((16, k)).astype("f4")
        want = np.maximum(x @ w + b, 0)
        f = tf.function(lambda t: tf.nn.relu(tf.nn.bias_add(tf.matmul(t, w), b)))
        with tf.device("/GPU:0"):
            got = f(tf.constant(x)).numpy()
        worst = max(worst, float(np.abs(got - want).max()))
    print(f"  max error of graph-mode Dense+ReLU on Metal: {worst:.1e} -> {'OK' if worst < TOL else 'WRONG'}")
    return 0 if worst < TOL else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--case":
        sys.exit(run_case())

    sys.stdout.reconfigure(line_buffering=True)
    import tensorflow as tf
    print(f"python {sys.version.split()[0]}  tensorflow {tf.__version__}  keras {tf.keras.__version__}")
    try:
        from importlib.metadata import version
        print(f"tensorflow-metal {version('tensorflow-metal')}")
    except Exception:
        print("tensorflow-metal not installed")

    results = {}
    for label, flag in [("without shim", "0"), ("with shim (AviaNZ default)", "1")]:
        print(f"{label}:", flush=True)
        env = dict(os.environ, AVIANZ_METAL_WORKAROUND=flag)
        results[label] = subprocess.call([sys.executable, __file__, "--case"], env=env)

    if results["with shim (AviaNZ default)"] != 0:
        print("FAIL: Metal results are wrong even with the shim. Run AviaNZ with AVIANZ_DISABLE_GPU=1.")
        sys.exit(1)
    if results["without shim"] == 0:
        print("NOTE: the tensorflow-metal bug appears fixed in this version; the shim may be removable.")
    print("PASS")


if __name__ == "__main__":
    main()
