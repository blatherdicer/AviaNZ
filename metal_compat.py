"""Apple-silicon (Metal) compatibility shims for TensorFlow.

Import and call apply() once, after importing tensorflow and before any model is built
or run. It does nothing on platforms other than Apple-silicon macOS.

Background
----------
With tensorflow-metal >= 1.0 (verified with 1.1.0 and 1.2.0 on TF 2.15 - 2.19), the
fused MatMul + BiasAdd + ReLU kernel that TensorFlow's graph optimizer (Grappler)
creates for Dense(..., activation='relu') returns wrong values on the Metal GPU. Eager
execution is correct, so only tf.function / model.predict / model.fit are affected.
Every AviaNZ CNN ends with Dense(256, activation='relu'), so without this shim the
recogniser outputs on the GPU are wrong (errors of up to 1.0 in class probability).

Disabling the Grappler meta-optimizer avoids the fused kernel. Measured on an M1 Max,
results then match the CPU to ~1e-7 and inference stays 7-12x faster than CPU (the
shim costs ~10%). The minimal reproduction is in scripts/check_metal.py.

Environment variables
---------------------
AVIANZ_DISABLE_GPU=1         run TensorFlow on the CPU only (troubleshooting).
AVIANZ_METAL_WORKAROUND=0    do not apply the shim (only for testing a future fixed
                             tensorflow-metal with scripts/check_metal.py).
"""
import os
import platform
import sys

_applied = False


def is_apple_silicon():
    return sys.platform == "darwin" and platform.machine() == "arm64"


def apply(verbose=True):
    global _applied
    if _applied:
        return
    _applied = True

    import tensorflow as tf

    if os.environ.get("AVIANZ_DISABLE_GPU") == "1":
        # must happen before the GPU is initialised
        tf.config.set_visible_devices([], "GPU")
        if verbose:
            print("TensorFlow: GPU disabled by AVIANZ_DISABLE_GPU=1, using CPU")
        return

    if not is_apple_silicon():
        return

    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        if verbose:
            print("TensorFlow: no Metal GPU found (is tensorflow-metal installed?), using CPU")
        return

    if os.environ.get("AVIANZ_METAL_WORKAROUND", "1") == "0":
        if verbose:
            print("TensorFlow: Metal GPU enabled WITHOUT fused-Dense workaround (AVIANZ_METAL_WORKAROUND=0)")
        return

    tf.config.optimizer.set_experimental_options({"disable_meta_optimizer": True})
    if verbose:
        print("TensorFlow: Metal GPU enabled (fused-Dense workaround active)")
