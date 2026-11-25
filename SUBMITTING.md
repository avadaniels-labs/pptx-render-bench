# Submitting a renderer

Any offline PPTX renderer can be scored. A submission is a pull request that adds one results file per corpus
and one row to [LEADERBOARD.md](LEADERBOARD.md).

## Steps

1. **Get the decks.** `python3 corpus/fetch_corpus.py all decks/` (pinned revisions, SHA-256 verified).
2. **Get the references.** Export every slide with PowerPoint for Mac as described in the README's Method
   section, store them as `refs/<corpus>/<deck>/slide-NN.png`, and run
   `python3 scoring/check_reference.py <corpus> refs/<corpus>/`. Only slides whose reference hash matches
   `powerpoint_png_sha256` are comparable with the published numbers; report the match count.
3. **Render.** Render every slide of every deck, in `presentation.xml` order including hidden slides, to a PNG
   with exactly the reference's pixel size. Do not resample afterwards. Rasters must be fully opaque.
4. **Score.** `python3 scoring/ssim.py refs/<corpus>/<deck>/slide-NN.png yours/<deck>/slide-NN.png` for every
   slide.
5. **Write results** as `results/<corpus>-<renderer>-<version>.csv` with the same columns as the published
   files: `deck, slide, rust_ssim, lo_ssim, delta, status, powerpoint_png_sha256`. Put your score in the
   `rust_ssim` column (it holds "the candidate renderer"), copy `lo_ssim` from the published file, set
   `delta = rust_ssim - lo_ssim`, and use `status` = `pass` (>= LibreOffice), `loss`, `failure` (no output or
   an error) or `invalid` (only the positions listed in `results/invalid.json`).
6. **Open a pull request** adding the results files, a LEADERBOARD row, and a short description: renderer
   name, version or commit, platform, and the exact fonts available to it.

## Rules

- **Frozen references.** Score against PowerPoint exports whose hashes match the published ones. Do not edit,
  re-export or align reference images.
- **No per-slide or per-deck tuning.** One renderer build and one configuration for the whole run. Nothing may
  key on deck names, hashes or slide numbers.
- **Report every slide.** Failures and crashes are rows with status `failure` and count as losses; nothing is
  dropped. Means are over all scored slides.
- **Disclose fonts.** List every font file available to the renderer (name and SHA-256). Using the published
  font profile (`fonts/font-profile-v45.json`) makes results directly comparable; anything else must be stated.
- `python3 results/summarize.py`-style counts in your PR description must be reproducible from your CSV.
