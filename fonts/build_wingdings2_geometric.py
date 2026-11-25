#!/usr/bin/env python3
"""Build "Wingdings 2" geometric bullets: a freely licensed (CC0-1.0) substitute font.

It covers only the Wingdings 2 slots whose glyphs are plain geometric shapes: the filled circles
circle1/3/5/7 (F095-F098) and the filled squares square1/3/5/7 (F09F-F0A2). Each glyph is generated
from numbers alone: a circle inscribed in, or a square filling, the bounding box the slot has in
Microsoft's Wingdings 2, with the same advance width. Font-wide vertical metrics use the same
published values. No outline data is copied from any other font.

The family is named "Wingdings 2" so that a renderer requesting that family finds a face that covers
these slots. It is not Microsoft's font and covers no other slot.

Deterministic: fontTools 4.66.1, fixed timestamps.

usage: python3 build_wingdings2_geometric.py OUT.ttf
"""
import math
import sys

import fontTools
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4, cmap_format_6

if fontTools.version != "4.66.1":
    sys.exit(f"fontTools {fontTools.version}; the pinned build needs 4.66.1")

UPM = 2048
# slot: (glyph name, shape, advance, (xMin, yMin, xMax, yMax)), metrics of the Wingdings 2 slot
GLYPHS = {
    0xF095: ("circle1", "circle", 542, (173, 641, 370, 839)),
    0xF096: ("circle3", "circle", 740, (173, 543, 568, 937)),
    0xF097: ("circle5", "circle", 1135, (173, 345, 962, 1135)),
    0xF098: ("circle7", "circle", 1825, (173, 0, 1653, 1480)),
    0xF09F: ("square1", "square", 542, (173, 641, 370, 839)),
    0xF0A0: ("square3", "square", 740, (173, 543, 568, 937)),
    0xF0A1: ("square5", "square", 1135, (173, 345, 962, 1135)),
    0xF0A2: ("square7", "square", 1825, (173, 0, 1653, 1480)),
}
TIMESTAMP = 3786825600  # 2024-01-01T00:00:00Z in the 1904 epoch


def circle(pen, box, segments=16):
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    k = 1 / math.cos(math.pi / segments)
    pt = lambda a, s=1: (round(cx + s * rx * math.cos(a)), round(cy + s * ry * math.sin(a)))
    step = 2 * math.pi / segments
    pen.moveTo(pt(0))
    for i in range(segments):  # clockwise: decreasing angle
        a0 = -i * step
        pen.qCurveTo(pt(a0 - step / 2, k), pt(a0 - step))
    pen.closePath()


def square(pen, box):
    x0, y0, x1, y1 = box
    pen.moveTo((x0, y0))
    pen.lineTo((x0, y1))
    pen.lineTo((x1, y1))
    pen.lineTo((x1, y0))
    pen.closePath()


def main(out):
    order = [".notdef", "space"] + [g[0] for g in GLYPHS.values()]
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    glyphs, metrics = {}, {}
    pen = TTGlyphPen(None)
    square(pen, (100, 0, 900, 1400))
    glyphs[".notdef"] = pen.glyph(); metrics[".notdef"] = (1000, 100)
    glyphs["space"] = TTGlyphPen(None).glyph(); metrics["space"] = (1825, 0)
    for name, shape, adv, box in GLYPHS.values():
        pen = TTGlyphPen(None)
        (circle if shape == "circle" else square)(pen, box)
        glyphs[name] = pen.glyph(); metrics[name] = (adv, box[0])
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1727, descent=-432, lineGap=0)
    codes = {0xF020: "space", **{c: g[0] for c, g in GLYPHS.items()}}
    fb.setupCharacterMap(codes)
    sym = cmap_format_4(4); sym.platformID, sym.platEncID, sym.language, sym.cmap = 3, 0, 0, dict(codes)
    mac = cmap_format_6(6); mac.platformID, mac.platEncID, mac.language = 1, 0, 0
    mac.cmap = {c - 0xF000: g for c, g in codes.items()}
    fb.font["cmap"].tables = [sym, mac]
    fb.setupNameTable({
        "copyright": "Generated geometric shapes, dedicated to the public domain (CC0-1.0). Not Microsoft Wingdings 2.",
        "familyName": "Wingdings 2", "styleName": "Regular",
        "uniqueFontIdentifier": "Wingdings 2 geometric bullets 1.000",
        "fullName": "Wingdings 2", "psName": "Wingdings2-GeometricBullets", "version": "Version 1.000",
        "licenseDescription": "CC0-1.0", "licenseInfoURL": "https://creativecommons.org/publicdomain/zero/1.0/",
        "description": "Geometric substitute covering Wingdings 2 slots F095-F098 and F09F-F0A2 only.",
    })
    fb.setupOS2(sTypoAscender=1579, sTypoDescender=-420, sTypoLineGap=49, usWinAscent=1727, usWinDescent=432,
                achVendID="NONE", fsType=0, usWeightClass=400, fsSelection=0x40,
                ulCodePageRange1=1 << 31, ulCodePageRange2=0, usFirstCharIndex=0xF020, usLastCharIndex=0xF0A2,
                sxHeight=0, sCapHeight=0, usDefaultChar=0, usBreakChar=0xF020, usMaxContext=0)
    fb.setupPost(keepGlyphNames=True)
    fb.setupHead(unitsPerEm=UPM, created=TIMESTAMP, modified=TIMESTAMP, fontRevision=1.0)
    fb.font.recalcTimestamp = False
    fb.save(out)


if __name__ == "__main__":
    main(sys.argv[1])
