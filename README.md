# PPTX rendering fidelity benchmark, v1.1.0 (frozen build v45, 195-font profile)

This benchmark asks how closely an offline renderer reproduces Microsoft PowerPoint's own slide images.
Each slide of each deck is rendered by two engines on Linux:

- **Rust**: an experimental PPTX renderer (DrawingML to SVG to raster). Frozen build v45, binary SHA-256
  `e23610171a6a6635af26369f1e065b55122d29e6cd364324d2cc276c29bf623d`. Its source is not part of this package.
- **LibreOffice 26.8.3.1** (`861effc5289d539f15c4c18d1ba8579ffd78728b`), the official Linux aarch64 deb tarball
  (SHA-256 `378a0766e4a815a5a96fb7473f346d072e23e3cc28606bdc8cd6f834cfaa14db`).

Both renders are scored with SSIM against PowerPoint's PNG export of the same slide. A slide counts as a
Rust win when `rust_ssim >= lo_ssim`. Exact ties count as wins, and no epsilon is applied.

This package holds **metadata only**: per-slide scores, hashes, fetch scripts, the font profile and the scorer.
It contains no decks and no images (see [What is not included and why](#what-is-not-included-and-why)).

## Headline results (release 1.1.0)

The numbers below are the output of `python3 results/summarize.py`, which reads only the committed CSVs
(`results/*-v45-font195.csv`).

| Corpus | Decks | Slides scored | Rust >= LibreOffice | Mean SSIM, Rust | Mean SSIM, LibreOffice | Smallest margin |
|---|---:|---:|---:|---:|---:|---:|
| PPTArena | 99 | 979 (0 invalid) | **978 / 979** | **0.9438** | 0.8881 | -0.00199 (080/7) |
| HF50 | 45 | 895 | **895 / 895** | **0.9697** | 0.9085 | +0.00024 |

- **One exception, PPTArena 080 slide 7** (Rust 0.8741, LibreOffice 0.8761). It is scored and reported as a
  loss, not excluded. The slide body is an `mc:AlternateContent` equation. PowerPoint draws the live OMML
  branch with Cambria Math, whose glyph ink grows the line height. LibreOffice and the Rust renderer both
  draw the stored fallback picture. No freely licensed font reproduces Cambria Math's metrics. See
  `results/exceptions.json`.
- **No invalid slides.** In release 1.0.0, eight PPTArena deck-013 slides (12, 18, 19, 20, 22, 23, 27, 30) were
  invalid: they use the Wingdings 2 bullet U+F096, which no font in the 194-font set covered, so the LibreOffice
  PDF font proof could not pass. Release 1.1.0 adds one generated CC0 font, "Wingdings 2" geometric bullets
  (`fonts/build_wingdings2_geometric.py`), to the shared set. All eight slides now prove and are scored, and
  Rust beats LibreOffice on each (smallest margin +0.046). The renderer binary is unchanged. See
  `results/invalid.json` and [CHANGELOG.md](CHANGELOG.md).
- Means are arithmetic means over the scored (distinct deck SHA-256, slide index) pairs. The PPTArena means
  moved from 0.9439 / 0.8884 to 0.9438 / 0.8881 because the eight new slides are now included.
- Release 1.0.0's results remain in `results/*-v45.csv` (`python3 results/summarize.py v45`).

### How these numbers were measured

| | PPTArena | HF50 |
|---|---|---|
| CI run | 45587503935 | 45587509588 |
| Shards | 8 (`e01`–`e08`) | 8 (`s01`–`s08`) |
| Runner | GitHub-hosted `ubuntu-24.04` aarch64 | same |

Every shard rendered, scored and passed its own independent verification step, which recomputes dimensions,
hashes and SSIM from the produced bytes. Both runs completed successfully. The per-slide rows were read from the
verified shard artifacts. Every HF50 deck reports `pass_complete_deck` with the same binary hash. Compared with
release 1.0.0 (runs 45544908167 and 45544912297), no HF50 score changed. In PPTArena, only decks 010 and 013
changed, because they are the only decks that use Wingdings 2. 16 of deck 010's changed slides went up for Rust
and one went down (010/28: 0.8688 to 0.8625, against LibreOffice's 0.7874).

## Leaderboard

| Renderer | PPTArena W / T / L vs LibreOffice | PPTArena mean SSIM | HF50 W / T / L vs LibreOffice | HF50 mean SSIM |
|---|---:|---:|---:|---:|
| Rust renderer v45 | 977 / 1 / 1 of 979 | 0.9438 | 895 / 0 / 0 of 895 | 0.9697 |
| LibreOffice 26.8.3.1 | baseline | 0.8881 | baseline | 0.9085 |

See [LEADERBOARD.md](LEADERBOARD.md). To add a renderer, see [SUBMITTING.md](SUBMITTING.md).

## Method

**Reference images.** Microsoft PowerPoint for Mac 16.113.3 (build 16.113.26092714) on macOS 27.0
(26A428), using File > Export > PNG > Save Every Slide, at a nominal 150 dpi with the long edge capped at
4000 px:

    width_px = round_half_up(width_emu / 914400 * min(150, 4000 * 914400 / max(width_emu, height_emu)))

The height is PowerPoint's own and must be within one pixel of the source aspect ratio. The PNG bytes are
kept exactly as exported, with no resizing, cropping or alignment. Slide order follows `presentation.xml`
`sldIdLst` and includes hidden slides. One HF50 poster deck is 3000 x 4000 px, about 83.3 dpi. The SHA-256 of
every reference PNG is in the `powerpoint_png_sha256` column of the results.

**Canvas.** Each engine renders directly to the reference's exact pixel size. LibreOffice exports a PDF
(`soffice --headless --convert-to pdf`), which is rasterized straight to the target canvas. Rust renders at
that size. No image is resampled or registered, and no region is masked.

**Score.** `skimage.metrics.structural_similarity` on RGB uint8 arrays with `channel_axis=2`, `data_range=255`,
`win_size=7`, `gaussian_weights=False` (uniform window) and `use_sample_covariance=True`. The whole slide
is scored, and any raster that is not fully opaque is rejected. The pinned versions are Python 3.13,
numpy 2.5.3, pillow 12.3.0, scikit-image 0.26.0 and pymupdf 1.28.2. The scorer is `scoring/ssim.py`.

**Fonts.** Both engines get the same frozen font set (`fonts/font-profile-195.json`, profile
`shared_195_office_open_cjk_wd2_v1`; release 1.0.0 used `fonts/font-profile-v45.json`, the same set without
the generated Wingdings 2 face). The system font paths are isolated and fontconfig 2.15.0 uses Ubuntu
24.04's standard rules (`fonts/fontconfig/`, hash-pinned). Fonts embedded in a deck are used where present.
A LibreOffice slide counts only if a PDF font proof shows that every embedded font subset comes from a
font in the frozen set. A slide that fails the proof is a validation failure, never a silent pass.

**Rust renderer settings** used for every slide: `PPTX_TEXT_EXPERIMENT_DEVICE_MATTE=opaque_solid`,
`PPTX_TEXT_EXPERIMENT_METRICS=os2_points`, `PPTX_TEXT_EXPERIMENT_PICTURE_JPEG=native_raster`.

## Corpora

| Corpus | Source | Revision | Files |
|---|---|---|---|
| PPTArena | Hugging Face `mofengenden/PPTArena`, `Original/*.pptx` (mirror: GitHub `michaelofengenden/PPTArena@7072dc9b`) | `20fb8902c74df2e97a2c31d288e4fa7f23405157` | 100 cases, 99 distinct files, 979 slides |
| HF50 | Hugging Face `noxneural/pptx_collection_templates` | `748f5b047e87c2bd6fdb0a898a68134453f15541` | 48 rows, 45 distinct files, 895 slides |

PPTArena 035 is byte-identical to 034 and is scored once, as 034. HF50 rows that share a SHA-256 are scored
once. The deck IDs `hf50-<first 12 hex of sha256>` come from the file hash. PPTArena's edited GroundTruth decks
and editing tasks are not used. Only the unchanged Original files are rendered.

## Layout

```
README.md
results/   pptarena-v45-font195.{csv,json}               release 1.1.0 per-slide rows: deck, slide, rust_ssim,
           hf50-v45-font195.{csv,json}                   lo_ssim, delta, status, powerpoint_png_sha256
           pptarena-v45.{csv,json}, hf50-v45.{csv,json}   release 1.0.0 rows (194-font profile)
           exceptions.json, invalid.json, summary.json, summarize.py
corpus/    pptarena-decks.json, hf50-decks.json          pinned download URL, sha256, size, slide count
           fetch_corpus.py                               download + sha256 check (stdlib only)
fonts/     font-profile-195.json                         every font: sha256, size, licence, how to obtain it
           font-profile-v45.json                         the 194-font profile of release 1.0.0
           fetch_fonts.py                                materialize + verify (MS core fonts from the original installers)
           build_wingdings2_geometric.py                 builds the CC0 "Wingdings 2" geometric bullets face
           vendor/                                       Open Sans (OFL-1.1) only
           licenses/                                     licence texts for the open fonts
           fontconfig/                                   pinned Ubuntu 24.04 fontconfig policy and rule files
           lo-bundled-font-inventory-26.8.3.json         fonts shipped inside the pinned LibreOffice
scoring/   ssim.py                                       the slide score
           check_reference.py                            compare your PowerPoint exports to the scored hashes
```

The `status` column holds `pass`, `loss` or `invalid`. `delta` is `rust_ssim - lo_ssim` and is empty when
the slide is invalid.

## Reproducing

1. **Decks.** `python3 corpus/fetch_corpus.py all decks/` downloads each deck at its pinned revision and
   aborts on any SHA-256 mismatch. Set `HF_TOKEN` if Hugging Face rate-limits you. `--github` takes PPTArena
   from the GitHub mirror instead.
2. **PowerPoint references.** Export every slide from PowerPoint for Mac as described under Method, save it
   as `refs/<deck>/slide-NN.png`, then run `python3 scoring/check_reference.py pptarena refs/` (or `hf50`).
   Other PowerPoint builds may not produce identical bytes. The check tells you whether your references are
   the ones that were scored.
3. **Fonts.** `pip install fonttools==4.66.1` and install `cabextract`, then run
   `python3 fonts/fetch_fonts.py fonts-out/`. The script verifies every file against the profile. It fetches
   the Liberation, Open Sans, DM Sans, Roboto, Source Sans Pro, URW Gothic, STIX Two Math and Noto Sans Bamum
   fonts at pinned revisions. It derives Noto Sans SC Regular and Bold from the pinned variable font. It
   extracts the 30 Microsoft core fonts from the original `corefonts` installers. It builds the CC0 "Wingdings 2"
   geometric bullets face with `fonts/build_wingdings2_geometric.py`. Fonts bundled with LibreOffice
   come from installing the pinned LibreOffice tarball. Two groups are not fetched:
   - Twemoji Mozilla (Apache-2.0 / CC-BY-4.0) must be built from source at the listed revision.
   - Four proprietary fonts cannot be obtained here (see below).

   A run of this script on 2026-11-25 materialized 75 fonts, and every hash matched.
4. **LibreOffice arm.** Install LibreOffice 26.8.3.1 from the pinned tarball. Point fontconfig at the
   materialized fonts with the pinned rules. Convert each deck to PDF and rasterize each page to the
   reference canvas.
5. **Score.** `python3 scoring/ssim.py refs/<deck>/slide-NN.png candidate.png` for each slide, then compare
   with `lo_ssim` / `rust_ssim` in `results/`. `python3 results/summarize.py` recomputes the headline table.

The Rust arm cannot be reproduced from this package, because the renderer is not published here. Its
per-slide scores and the hashes of the references they were measured against are recorded in `results/`.

## What is not included and why

- **Decks.** Neither dataset grants a per-deck redistribution licence. The PPTArena dataset card declares
  MIT, but its decks are third-party presentations with no per-file source or licence metadata.
  `noxneural/pptx_collection_templates` at the pinned revision has no per-deck licence either. Decks are
  referenced by pinned URL and SHA-256 only.
- **PowerPoint reference PNGs, Rust and LibreOffice renders, and diff images.** They are derived from those
  decks, so the same restriction applies. Only their SHA-256 digests are published.
- **Microsoft core fonts** (Arial, Times New Roman, Courier New, Georgia, Verdana, Trebuchet MS, Comic Sans
  MS, Impact, Andale Mono, Webdings, Arial Black). Their EULA does not allow redistribution outside the
  original installers. `fonts/fetch_fonts.py` extracts them from those installers and checks hashes.
- **Proprietary fonts that were in the measured set**: Tahoma Regular, Tahoma Bold, Sagona Book and Gill
  Sans Nova Light, taken from a licensed Microsoft Office / macOS installation. They are listed with their
  SHA-256 in the profile, but they cannot be redistributed or fetched. A bit-exact reproduction needs your
  own licensed copies with matching hashes. Without them, slides that use these families may score
  differently.
- **Fonts that are open but not OFL/Apache-only**, and the large CJK files: URW Gothic (AGPL-3.0 with font
  exception), Twemoji Mozilla, and Noto Sans SC (OFL, about 21 MB of derived instances). They are fetched
  by script or derived, not vendored, to keep this package small.
- **Renderer and evaluation-harness code.** These are not published with this release.

## License

- **Code** (`scoring/`, `corpus/*.py`, `fonts/*.py`, `results/*.py`): Apache License 2.0, see [LICENSE](LICENSE).
- **Results and manifests** (`results/*.csv|json`, `corpus/*.json`, `fonts/*.json`, `fonts/fontconfig/*.json`,
  this documentation): Creative Commons Attribution 4.0 International, see [LICENSE-DATA](LICENSE-DATA).
- **Third-party files keep their own licences:** `fonts/vendor/` (Open Sans, OFL-1.1), `fonts/licenses/` (the
  licence texts themselves) and `fonts/fontconfig/rules/` (fontconfig and DejaVu configuration files from
  Ubuntu 24.04's fontconfig packages, under their upstream licences).
- The font built by `fonts/build_wingdings2_geometric.py` is dedicated to the public domain (CC0-1.0,
  `fonts/licenses/Wingdings2-Geometric-CC0-1.0.txt`). It is not Microsoft's Wingdings 2.
- The decks, reference images and fonts referenced by the fetch scripts are not covered by these licences.

To cite, see [CITATION.cff](CITATION.cff).
