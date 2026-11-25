#!/usr/bin/env python3
"""Materialize the v45 supplemental + fallback fonts into one directory and verify every SHA-256.

usage: python3 fonts/fetch_fonts.py OUT_DIR [--skip-corefonts] [--skip-cjk]

Sources, per fonts/font-profile-v45.json:
  vendored                  copied from fonts/vendor/ (Open Sans, OFL-1.1)
  url / zip_member          downloaded from the pinned upstream revision or release asset
  cabextract                Microsoft Core Fonts extracted from the original corefonts installers
                            (needs `cabextract`). These fonts are never committed; their EULA travels
                            inside each installer (Licen.TXT).
  variable_instance         Noto Sans SC Regular/Bold, instanced from the pinned variable font with
                            fontTools 4.66.1 (pip install fonttools==4.66.1); byte-identical only on that release
  manual_build              Twemoji Mozilla: upstream ships no pinned binary; build it yourself
  not_included_proprietary  Tahoma Regular/Bold, Sagona Book, Gill Sans Nova Light: not obtainable here

Fonts bundled inside LibreOffice 26.8.3 come from installing the pinned LibreOffice tarball
(fonts/lo-bundled-font-inventory-26.8.3.json lists their hashes). Exit status is non-zero when any
font that this script is responsible for is missing or has the wrong hash.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
UA = {"User-Agent": "pptx-render-benchmark-fetch/1"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


_cache: dict[str, bytes] = {}


def get(url: str) -> bytes:
    if url not in _cache:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
            _cache[url] = r.read()
    return _cache[url]


def instance(source: bytes, location: dict) -> bytes:
    import fontTools
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    if fontTools.version != "4.66.1":
        raise RuntimeError(f"fontTools {fontTools.version}; the pinned derivation needs 4.66.1")
    font = TTFont(io.BytesIO(source), recalcTimestamp=False)
    out = instantiateVariableFont(font, location, updateFontNames=True)
    buf = io.BytesIO()
    out.save(buf)
    return buf.getvalue()


def cab_member(cabinet: bytes, member: str) -> bytes:
    if not shutil.which("cabextract"):
        raise RuntimeError("cabextract not installed")
    with tempfile.TemporaryDirectory() as d:
        exe = Path(d) / "installer.exe"
        exe.write_bytes(cabinet)
        subprocess.run(["cabextract", "-q", "-F", member, "-d", d, str(exe)], check=True)
        hits = [p for p in Path(d).rglob("*") if p.name.lower() == Path(member).name.lower()]
        if len(hits) != 1:
            raise RuntimeError(f"{member} not found in cabinet")
        return hits[0].read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--skip-corefonts", action="store_true")
    ap.add_argument("--skip-cjk", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    prof = json.loads((HERE / "font-profile-v45.json").read_text())
    failures, skipped = [], []

    # Liberation fallback fonts (the Rust base set and LibreOffice fallback)
    lib = prof["liberation_fallback"]
    try:
        archive = get(lib["archive_url"])
        if sha(archive) != lib["archive_sha256"]:
            raise RuntimeError("Liberation archive hash mismatch")
        with tarfile.open(fileobj=io.BytesIO(archive)) as t:
            members = {Path(m.name).name: m for m in t.getmembers() if m.isfile()}
            for name, digest in lib["fonts"].items():
                data = t.extractfile(members[name]).read()
                if sha(data) != digest:
                    raise RuntimeError(f"{name} hash mismatch")
                (a.out / name).write_bytes(data)
    except Exception as e:  # noqa: BLE001
        failures.append(f"liberation: {e}")

    for f in prof["supplemental_fonts"]:
        acq, name, want = f["acquisition"], f["name"], f["sha256"]
        dest = a.out / name
        if dest.exists() and sha(dest.read_bytes()) == want:
            continue
        m = acq["method"]
        try:
            if m == "not_included_proprietary" or m == "manual_build":
                skipped.append(f"{name} ({m})")
                continue
            if m == "cabextract" and a.skip_corefonts or m == "variable_instance" and a.skip_cjk:
                skipped.append(f"{name} (skipped by flag)")
                continue
            if m == "vendored":
                data = (PKG / acq["path"]).read_bytes()
            elif m == "url":
                data = get(acq["url"])
            elif m == "zip_member":
                with zipfile.ZipFile(io.BytesIO(get(acq["archive_url"]))) as z:
                    data = z.read(acq["member_path"])
            elif m == "cabextract":
                cab = get(acq["cabinet_url"])
                if sha(cab) != acq["cabinet_sha256"]:
                    raise RuntimeError("installer hash mismatch")
                data = cab_member(cab, acq["member_path"])
            elif m == "variable_instance":
                src = get(acq["source_url"])
                if sha(src) != acq["source_sha256"]:
                    raise RuntimeError("variable source hash mismatch")
                data = instance(src, acq["location"])
            else:
                raise RuntimeError(f"unknown method {m}")
            if sha(data) != want:
                raise RuntimeError(f"hash {sha(data)} != {want}")
            dest.write_bytes(data)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{name}: {e}")

    print(f"fonts in {a.out}: {len(list(a.out.iterdir()))}")
    for s in skipped:
        print("not materialized:", s)
    for fl in failures:
        print("FAILED:", fl, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
