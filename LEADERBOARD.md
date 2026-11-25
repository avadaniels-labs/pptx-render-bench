# Leaderboard

SSIM against PowerPoint for Mac 16.113.3 PNG exports (see [README](README.md#method)). "W / T / L" counts
slides where the renderer scores above, equal to, or below LibreOffice 26.8.3.1 on the same slide. Means are
over scored slides. Higher is better.

| Renderer | PPTArena scored | PPTArena W / T / L vs LO | PPTArena mean SSIM | HF50 scored | HF50 W / T / L vs LO | HF50 mean SSIM | Results |
|---|---:|---:|---:|---:|---:|---:|---|
| Rust renderer v45 | 971 (+8 invalid) | 969 / 1 / 1 | 0.9439 | 895 | 895 / 0 / 0 | 0.9697 | `results/pptarena-v45.csv`, `results/hf50-v45.csv` |
| LibreOffice 26.8.3.1 (baseline) | 971 (+8 invalid) | n/a | 0.8884 | 895 | n/a | 0.9085 | `lo_ssim` columns of the same files |

Release v1.0.0. The eight PPTArena deck-013 slides are invalid in this release (the Wingdings 2 bullet U+F096
has no freely licensed font in the v45 font set; see `results/invalid.json`) and are not scored. A follow-up
release will score them.
The single loss is the accepted exception pptarena-080 slide 7 (`results/exceptions.json`). The tie is
pptarena-006 slide 13, where both engines score 1.0.

To add a renderer, see [SUBMITTING.md](SUBMITTING.md).
