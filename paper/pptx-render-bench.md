---
title: "pptx-render-bench: Measuring Offline PPTX Rendering Fidelity against PowerPoint"
author: "Velislava Yanchina (avadaniels-labs)"
date: "November 2026 — release 1.2.0"
---

## Abstract

We present **pptx-render-bench**, a benchmark of how closely offline PPTX renderers reproduce Microsoft
PowerPoint's own slide images. It uses two public deck corpora: PPTArena (99 distinct decks, 979 slides)
and HF50 (45 decks, 895 slides). Each slide is compared, with RGB SSIM on an exact pixel canvas, against a
PNG exported by PowerPoint for Mac. Both engines receive the same hash-pinned 195-file font set. A PDF font
proof rejects LibreOffice slides whose embedded fonts are not drawn from that set. The release contains
metadata only: per-slide scores, reference-image digests, pinned corpus and font manifests, and the scorer.
Decks and images are excluded because the corpora carry no per-deck redistribution licence. Folio, an
experimental PPTX renderer written in Rust (frozen build v45), scores at least as high as LibreOffice 26.8.3.1 on 978 of 979 PPTArena slides,
with mean SSIM 0.9438 against 0.8881. On HF50 it does so on all 895 slides, 0.9697 against 0.9085. That per-slide
claim holds against LibreOffice only. Two extra open-source baselines ran under the same protocol. ONLYOFFICE x2t
10.0.0 outperforms LibreOffice, with means of 0.9120 and 0.9267, and beats Folio on 201 PPTArena
slides and 15 HF50 slides. Apache POI 5.4.1 scores below LibreOffice. The author develops Folio;
Section 10 states this conflict of interest.

## 1. Motivation

Server-side tools that edit or preview presentations usually rasterize PPTX through LibreOffice. When the
rendering is wrong, the error is hard to see in an automated pipeline. A missing font, a misplaced line
break or a dropped effect changes what a reader sees, but nothing fails. Most published comparisons use a
handful of hand-picked slides, or a second open-source engine, as the reference. We wanted three things
instead: (i) PowerPoint itself as the reference, (ii) a frozen, hash-pinned protocol that anyone can audit,
and (iii) per-slide results with no silent exclusions.

## 2. Corpora and licensing

| Corpus | Source (pinned revision) | Files | Slides |
|---|---|---:|---:|
| PPTArena | HF `mofengenden/PPTArena` `20fb8902…` (`Original/*.pptx`), mirrored on GitHub at `7072dc9b…` | 100 cases, 99 distinct | 979 |
| HF50 | HF `noxneural/pptx_collection_templates` `748f5b04…` | 48 rows, 45 distinct | 895 |

Decks are identified by SHA-256. Byte-identical duplicates (PPTArena 034/035, and three HF50 rows) are
scored once. Hidden slides are included. PPTArena's edited GroundTruth decks are not used. The PPTArena
dataset card declares MIT, but its decks are third-party presentations with no per-file provenance or
licence. HF50 has no per-deck licence either. We therefore publish only pinned URLs and hashes, and a fetch
script that verifies every byte.

## 3. Reference generation

The references come from PowerPoint for Mac 16.113.3 (build 16.113.26092714) on macOS 27.0, using File >
Export > PNG > Save Every Slide. They are exported at a nominal 150 dpi with the long edge capped at 4000 px:
`width = round_half_up(width_emu/914400 · min(150, 4000·914400/max(width_emu, height_emu)))`. The height is
PowerPoint's own and must lie within one pixel of the source aspect ratio. Reference bytes are never
resized, cropped or aligned. The SHA-256 of each of the 1,874 PNGs is published, so a third party can check
that its own exports match before comparing scores.

## 4. Scoring

Each engine renders directly to the reference canvas. LibreOffice converts to PDF, which is rasterized to the
target size. Folio draws SVG at that size. Nothing is resampled or registered. The score is
`skimage.metrics.structural_similarity` on RGB uint8 arrays, with `channel_axis=2`, `data_range=255`,
`win_size=7`, a uniform window (`gaussian_weights=False`) and `use_sample_covariance=True`. Versions are
scikit-image 0.26.0, numpy 2.5.3 and pillow 12.3.0. Every raster must be fully opaque, and the whole slide is
scored with no masks. A slide is a win when `rust_ssim ≥ lo_ssim`; ties count as wins and no epsilon is
applied. Means are taken over distinct (deck hash, slide) pairs. Runs use GitHub-hosted `ubuntu-24.04`
aarch64 runners, 8 shards per corpus. Each shard independently recomputes hashes, dimensions and SSIM from
the bytes it produced.

## 5. Font profile

Font availability affects these scores more than any other single factor, so both engines get the same
font set. It holds 195 files: 127 base files, which are the fonts bundled with the pinned LibreOffice
tarball (hashes in `fonts/lo-bundled-font-inventory-26.8.3.json`) plus the Liberation family, and 68
supplemental faces. The supplemental faces are:

- open fonts fetched at pinned revisions: Open Sans, DM Sans, Roboto, Source Sans Pro, URW Gothic, STIX Two
  Math, Noto Sans Bamum and Twemoji;
- Noto Sans SC Regular and Bold, instanced deterministically from the pinned variable font with
  fontTools 4.66.1;
- the 30 Microsoft core fonts, extracted from their original `corefonts` installers;
- four proprietary faces (Section 9).

Fontconfig 2.15.0 runs with Ubuntu 24.04's standard rules, with system font paths isolated. A LibreOffice
slide is valid only if a PDF font proof shows that every embedded subset comes from a font in this set.

**The CC0 bullet font.** Release 1.0.0 declared eight PPTArena deck-013 slides invalid. That deck's master
gives body bullets Wingdings 2 U+F096 (a filled circle). LibreOffice recodes the slot to OpenSymbol U+E56F,
which OpenSymbol lacks, so the font proof failed. Release 1.1.0 adds a generated face whose family name is
"Wingdings 2". It covers only eight slots whose Wingdings 2 glyphs are plain geometry: filled circles
F095–F098 and filled squares F09F–F0A2. Each outline is computed from that slot's advance width and bounding
box, and no outline data is copied. The build is deterministic (2,688 bytes, SHA-256 `74db0932…`) and the
face is dedicated to the public domain. Both engines resolve it by family name, and no renderer code
changed. All eight slides now pass the proof. Only decks 010 and 013 use Wingdings 2. Of deck 010's 65
slides, 17 changed score: Folio improved on 16, and on 010/28 it fell from 0.8688 to 0.8625, still above
LibreOffice's 0.7874. No HF50 score changed.

## 6. Results (release 1.1.0)

| Corpus | Scored | Folio W / T / L vs LibreOffice | Mean SSIM, Folio | Mean SSIM, LibreOffice | Median Δ | 10th pct Δ |
|---|---:|---:|---:|---:|---:|---:|
| PPTArena | 979 (0 invalid) | 977 / 1 / 1 | **0.9438** | 0.8881 | +0.041 | +0.012 |
| HF50 | 895 | 895 / 0 / 0 | **0.9697** | 0.9085 | +0.051 | +0.017 |

There were no render failures, missing references or unattempted slides. The tie is PPTArena 006/13, where
both engines score 1.0. The smallest HF50 margin is +0.00024. On 79 PPTArena slides and 28 HF50 slides the
margin is below 0.01, so the aggregate win counts overstate how decisively Folio wins on a
typical slide. Folio's lowest slide scores are 0.554 (PPTArena) and 0.758 (HF50). LibreOffice's
are 0.475 and 0.559.

## 7. Extra baselines (release 1.2.0)

Two more open-source renderers ran on the same references, with the same scorer, exact canvas and 195-file
font set, on the same `ubuntu-24.04` aarch64 runners:

- **ONLYOFFICE `x2t`** from DocumentBuilder 10.0.0, linux-aarch64 release asset, AGPL-3.0. It writes one PNG
  thumbnail per slide at the reference size. The shared files were the only system fonts, and the package's
  own bundled fonts were removed. Its font index covered 192 of the 195 files.
- **Apache POI XSLF 5.4.1**, Apache-2.0, on Java 21. It draws each slide with Java2D onto the reference
  canvas, with fontconfig isolated to the shared set. Its zip-bomb heuristics are lifted, because they
  rejected 39 legitimate, hash-pinned PPTArena decks before rendering.

Output with alpha is composited on white before scoring. A slide a renderer cannot produce counts as a loss
against LibreOffice and is excluded from that renderer's mean.

| Renderer | PPTArena W / T / L vs LO | PPTArena mean | HF50 W / T / L vs LO | HF50 mean | Failures |
|---|---:|---:|---:|---:|---:|
| Folio (build v45) | 977 / 1 / 1 | 0.9438 | 895 / 0 / 0 | 0.9697 | 0 / 0 |
| ONLYOFFICE x2t 10.0.0 | 791 / 1 / 187 | 0.9120 | 639 / 0 / 256 | 0.9267 | 0 / 0 |
| LibreOffice 26.8.3.1 | — | 0.8881 | — | 0.9085 | 0 / 0 |
| Apache POI 5.4.1 | 163 / 1 / 815 | 0.8368 | 305 / 0 / 590 | 0.8977 | 1 / 4 |

ONLYOFFICE is the strongest open-source baseline measured here. Folio scores at least as high as
ONLYOFFICE on 778 of 979 PPTArena slides and 880 of 895 HF50 slides, so ONLYOFFICE wins 201 and 15 slides.
The paper's per-slide claim therefore holds against LibreOffice only, not against every open-source renderer.
POI's failures are a missing-relationship exception (PPTArena, 1 slide) and a null colour lookup (HF50,
4 slides). Folio scores at least as high as POI on 959 of 978 and 887 of 891 scored slides.
Neither baseline went through the LibreOffice PDF font proof, which is specific to LibreOffice's PDF path. Their
font isolation rests on the system font configuration described above.

## 8. The 080/7 exception

The one loss is PPTArena 080 slide 7: Folio 0.8741, LibreOffice 0.8761, Δ = −0.0020. The slide body is an
`mc:AlternateContent` equation. PowerPoint renders the live OMML (`a14`) branch with Cambria Math, and that
font's glyph-specific ink increases the line height. We measured this on 17 PowerPoint variants in 0.24 pt
steps. LibreOffice and Folio both draw the stored fallback picture. No freely licensed font
reproduces Cambria Math's metrics, and a minimal OMML renderer with STIX Two Math scored lower (0.854). The
slide stays in every count as a reported loss rather than being excluded or relabelled.

## 9. Limitations

- **Proprietary fonts.** Tahoma Regular and Bold, Sagona Book and Gill Sans Nova Light were in the measured
  set. They came from a licensed Office/macOS installation and cannot be redistributed or fetched. Their
  hashes are published, but exact reproduction requires licensed copies.
- **Single reference platform.** All references come from one PowerPoint build on one macOS version.
  PowerPoint for Windows, or other builds, may lay out text differently, and the reference hashes will
  differ.
- **SSIM limits.** SSIM is a structural proxy. It rewards large flat areas, under-weights small text errors,
  and does not capture whether a slide is legible or correct. A blank slide can score well against a sparse
  reference. Margins below 0.01 are within the range where a human might not see a difference.
- **Corpus scope and overfitting.** The renderer was developed while measuring on these same two corpora.
  They are not a held-out test set. Improvements may not carry over to other decks.
- **Baseline settings.** Each extra baseline was run once with stock settings and the changes noted in
  Section 7. Better-tuned configurations of these renderers may score higher.

## 10. Reproducibility and conflict of interest

`corpus/fetch_corpus.py` restores the decks with SHA-256 checks. `fonts/fetch_fonts.py` restores 75 of the
supplemental and fallback fonts from pinned public sources, extracts the Microsoft core fonts and builds the
CC0 face, verifying every hash. Twemoji must be built from source, and the four proprietary fonts must be
supplied by the user. `scoring/check_reference.py` verifies PowerPoint exports, and `scoring/ssim.py` is the
scorer. The LibreOffice arm can be reproduced end to end. Folio is not published; its scores
are reported with the binary's SHA-256. Code is Apache-2.0; results and manifests are CC-BY-4.0.

**Conflict of interest.** The author develops Folio evaluated here. Its development used these
corpora and this protocol. LibreOffice, ONLYOFFICE and Apache POI are included as independent baselines. The protocol, references
and per-slide results are published so that others can audit the numbers and submit their own renderers
(`SUBMITTING.md`).
