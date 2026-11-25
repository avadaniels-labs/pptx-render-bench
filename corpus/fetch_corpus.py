#!/usr/bin/env python3
"""Download the benchmark decks at their pinned Hugging Face revisions and verify SHA-256 (stdlib only).

usage: python3 corpus/fetch_corpus.py {pptarena,hf50,all} OUT_DIR [--github]

Writes OUT_DIR/<corpus>/<deck id>.pptx. Existing files with the right hash are kept. Any mismatch is
fatal. Decks are third-party files without a per-deck redistribution license: keep them local.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, expected: str) -> None:
    if dest.exists() and sha256(dest) == expected:
        return
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "pptx-render-benchmark-fetch/1"})
    if os.environ.get("HF_TOKEN") and "huggingface.co" in url:
        req.add_header("Authorization", "Bearer " + os.environ["HF_TOKEN"])
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    got = sha256(tmp)
    if got != expected:
        tmp.unlink()
        sys.exit(f"sha256 mismatch for {url}: {got} != {expected}")
    tmp.replace(dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", choices=["pptarena", "hf50", "all"])
    ap.add_argument("out", type=Path)
    ap.add_argument("--github", action="store_true", help="PPTArena: use the pinned GitHub mirror instead of HF")
    a = ap.parse_args()
    for name in (["pptarena", "hf50"] if a.corpus == "all" else [a.corpus]):
        meta = json.loads((HERE / f"{name}-decks.json").read_text())
        out = a.out / name
        out.mkdir(parents=True, exist_ok=True)
        seen = set()
        for d in meta["decks"]:
            if d["sha256"] in seen:  # published duplicates: same bytes, scored once
                continue
            seen.add(d["sha256"])
            url = d.get("github_download_url") if a.github and d.get("github_download_url") else d["download_url"]
            fetch(url, out / f'{d["id"]}.pptx', d["sha256"])
            print(name, d["id"], "ok", flush=True)
        print(f"{name}: {len(seen)} distinct decks verified in {out}")


if __name__ == "__main__":
    main()
