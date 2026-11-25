#!/usr/bin/env python3
"""Check your PowerPoint reference PNGs against the hashes the v45 run scored against (stdlib only).

usage: python3 scoring/check_reference.py {pptarena,hf50} DIR [RESULT_SET]   (default v45-font195)
DIR holds <deck>/slide-NN.png (NN zero-padded to two digits). Reports matches, mismatches and missing.
Byte-identical exports are not guaranteed across PowerPoint builds; the run used PowerPoint for Mac
16.113.3 (16.113.26092714) on macOS 27.0 (26A428), File > Export > PNG > Save Every Slide.
"""
import csv
import hashlib
import sys
from pathlib import Path

lane, root = sys.argv[1], Path(sys.argv[2])
tag = sys.argv[3] if len(sys.argv) > 3 else "v45-font195"
rows = csv.DictReader((Path(__file__).resolve().parents[1] / "results" / f"{lane}-{tag}.csv").open())
ok = bad = missing = 0
for r in rows:
    p = root / r["deck"] / f'slide-{int(r["slide"]):02d}.png'
    if not p.exists():
        missing += 1
        continue
    if hashlib.sha256(p.read_bytes()).hexdigest() == r["powerpoint_png_sha256"]:
        ok += 1
    else:
        bad += 1
        print("mismatch", p)
print(f"match {ok}, mismatch {bad}, missing {missing}")
