#!/usr/bin/env python3
"""Recompute the headline numbers from the committed per-slide CSVs (stdlib only).

usage: python3 results/summarize.py [RESULT_SET]
RESULT_SET defaults to v45-font195 (release 1.1.0); v45 gives release 1.0.0.
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def summary(path: Path) -> dict:
    rows = list(csv.DictReader(path.open()))
    scored = [r for r in rows if r["status"] != "invalid"]
    rust = [float(r["rust_ssim"]) for r in scored]
    lo = [float(r["lo_ssim"]) for r in scored]
    wins = sum(a >= b for a, b in zip(rust, lo))
    return {
        "positions": len(rows),
        "decks": len({r["deck"] for r in rows}),
        "scored_slides": len(scored),
        "invalid_slides": len(rows) - len(scored),
        "rust_ge_lo": wins,
        "rust_lt_lo": [f'{r["deck"]}/{r["slide"]}' for r in scored if float(r["rust_ssim"]) < float(r["lo_ssim"])],
        "mean_rust_ssim": round(sum(rust) / len(rust), 4),
        "mean_lo_ssim": round(sum(lo) / len(lo), 4),
        "min_delta": round(min(a - b for a, b in zip(rust, lo)), 5),
        "status_counts": {s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})},
    }


if __name__ == "__main__":
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else "v45-font195"
    print(json.dumps({"result_set": tag, "pptarena": summary(HERE / f"pptarena-{tag}.csv"),
                      "hf50": summary(HERE / f"hf50-{tag}.csv")}, indent=1))
