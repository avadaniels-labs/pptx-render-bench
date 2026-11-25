# Leaderboard

SSIM against PowerPoint for Mac 16.113.3 PNG exports (see [README](README.md#method)). "W / T / L" counts
slides where the renderer scores above, equal to, or below LibreOffice 26.8.3.1 on the same slide. Means are
over scored slides. Higher is better. Release 1.1.0, font profile `fonts/font-profile-195.json`.

| Renderer | PPTArena scored | PPTArena W / T / L vs LO | PPTArena mean SSIM | HF50 scored | HF50 W / T / L vs LO | HF50 mean SSIM | Results |
|---|---:|---:|---:|---:|---:|---:|---|
| Folio (build v45) | 979 | 977 / 1 / 1 | 0.9438 | 895 | 895 / 0 / 0 | 0.9697 | `results/pptarena-v45-font195.csv`, `results/hf50-v45-font195.csv` |
| LibreOffice 26.8.3.1 (baseline) | 979 | n/a | 0.8881 | 895 | n/a | 0.9085 | `lo_ssim` columns of the same files |
| ONLYOFFICE x2t 10.0.0 (AGPL-3.0) | 979 | 791 / 1 / 187 | 0.9120 | 895 | 639 / 0 / 256 | 0.9267 | `results/baselines/*-onlyoffice-x2t-10.0.0.csv` |
| Apache POI XSLF 5.4.1 (Apache-2.0) | 978 + 1 failure | 163 / 1 / 815\* | 0.8368 | 891 + 4 failures | 305 / 0 / 590\* | 0.8977 | `results/baselines/*-apache-poi-5.4.1.csv` |

\* Render failures count as losses against LibreOffice and are excluded from the mean (PPTArena: 1; HF50: 4).

The baselines use the same references, scorer, canvas policy and 195-file font set (isolated through
fontconfig for POI, and as the only system fonts for ONLYOFFICE, whose font index covered 192 of the 195 files).
Output with alpha is composited on white before scoring. Settings: POI with its zip-bomb heuristics lifted
(the hash-pinned decks are trusted); ONLYOFFICE `x2t` thumbnails at the exact canvas. On the same slides Folio scores at least as high as ONLYOFFICE on 778 / 979 PPTArena and 880 / 895 HF50 slides, and at least as
high as POI on 959 / 978 and 887 / 891.

There are no invalid slides in this release. Folio's single loss is the accepted exception pptarena-080 slide 7
(`results/exceptions.json`). Its tie is pptarena-006 slide 13, where it and LibreOffice both score 1.0.

Release 1.0.0 (194-font profile, 8 invalid deck-013 slides) scored Folio 969 / 1 / 1 of 971 with mean 0.9439
against LibreOffice's 0.8884 on PPTArena, and the same HF50 numbers; see `results/*-v45.csv`.

To add a renderer, see [SUBMITTING.md](SUBMITTING.md).
