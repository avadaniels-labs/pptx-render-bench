#!/usr/bin/env python3
"""The v45 slide score, as a standalone function, plus a CLI.

Both lanes call skimage.metrics.structural_similarity on RGB uint8 arrays with
channel_axis=2, data_range=255, win_size=7, gaussian_weights=False, use_sample_covariance=True
(the skimage defaults, written out). Images must already have the PowerPoint reference's exact
pixel size: each arm is rasterized directly to that canvas, there is no resampling, registration,
cropping or masking. Every raster must be fully opaque.

Versions pinned in the v45 runs: Python 3.13, numpy 2.5.3, pillow 12.3.0, scikit-image 0.26.0.
This function is equivalent to the scorers that produced results/: same call, same parameters, and the
same exact-canvas and opacity preconditions.

usage: python3 scoring/ssim.py POWERPOINT.png CANDIDATE.png
"""
import math
import sys

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity


def load_rgb(path):
    with Image.open(path) as im:
        im.load()
        if im.convert("RGBA").getchannel("A").getextrema() != (255, 255):
            raise ValueError(f"{path}: non-opaque raster cannot enter the RGB scorer")
        return im.convert("RGB")


def score(reference_png, candidate_png) -> float:
    ref, cand = load_rgb(reference_png), load_rgb(candidate_png)
    if ref.size != cand.size:
        raise ValueError(f"canvas mismatch {cand.size} != reference {ref.size}; render to the reference size")
    value = float(structural_similarity(np.asarray(ref, dtype=np.uint8), np.asarray(cand, dtype=np.uint8),
                                        channel_axis=2, data_range=255, win_size=7,
                                        gaussian_weights=False, use_sample_covariance=True))
    if not (math.isfinite(value) and -1 <= value <= 1):
        raise ValueError("invalid SSIM")
    return value


if __name__ == "__main__":
    print(f"{score(sys.argv[1], sys.argv[2]):.10f}")
