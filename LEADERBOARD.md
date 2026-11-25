# Leaderboard

SSIM against PowerPoint for Mac 16.113.3 PNG exports (see [README](README.md#method)). "W / T / L" counts
slides where the renderer scores above, equal to, or below LibreOffice 26.8.3.1 on the same slide. Means are
over scored slides. Higher is better. Release 1.1.0, font profile `fonts/font-profile-195.json`.

| Renderer | PPTArena scored | PPTArena W / T / L vs LO | PPTArena mean SSIM | HF50 scored | HF50 W / T / L vs LO | HF50 mean SSIM | Results |
|---|---:|---:|---:|---:|---:|---:|---|
| Rust renderer v45 | 979 | 977 / 1 / 1 | 0.9438 | 895 | 895 / 0 / 0 | 0.9697 | `results/pptarena-v45-font195.csv`, `results/hf50-v45-font195.csv` |
| LibreOffice 26.8.3.1 (baseline) | 979 | n/a | 0.8881 | 895 | n/a | 0.9085 | `lo_ssim` columns of the same files |

There are no invalid slides in this release. The single loss is the accepted exception pptarena-080 slide 7
(`results/exceptions.json`). The tie is pptarena-006 slide 13, where both engines score 1.0.

Release 1.0.0 (194-font profile, 8 invalid deck-013 slides) scored Rust 969 / 1 / 1 of 971 with mean 0.9439
against LibreOffice's 0.8884 on PPTArena, and the same HF50 numbers; see `results/*-v45.csv`.

To add a renderer, see [SUBMITTING.md](SUBMITTING.md).
