from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import SVGPath
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
import xml.etree.ElementTree as ET


EM_SIZE = 1000  # units per em
# ADV_WIDTH = 600  # default advance‐width
ADV_WIDTH = 900
LSB = 50  # default left‐side bearing
BASE_CODEPOINT = 0xF2000  # starting codepoint


def get_viewbox(svg_file):
    root = ET.parse(svg_file).getroot()
    vb = root.attrib.get("viewBox", None)
    if vb:
        x0,y0,w,h = map(float, vb.split())
        return x0, y0, w, h
    # fallback: hardcode or measure via a pen
    return 0, 0, 142, 66



def draw_scaled(svg_file: Path, pen, margin=0.9):
    x0, y0, w, h = get_viewbox(svg_file)
    scale = EM_SIZE * margin / max(w, h)
    # scale = 5
    glyph_width = w * scale
    extra_space = EM_SIZE - glyph_width
    tx = -x0 * scale + extra_space / 2
    ty = -y0 * scale
    # tx, ty = -x0 * scale, -y0 * scale
    t_pen = TransformPen(pen, (scale, 0, 0, scale, tx, ty))
    SVGPath(str(svg_file)).draw(t_pen)
    return extra_space



def gather_svgs(discharge_glyphs_dir: Path, charge_glyphs_dir: Path):
    discharge_glyphs = sorted(discharge_glyphs_dir.glob("**/*.svg"))
    charge_glyphs = sorted(charge_glyphs_dir.glob("**/*.svg"))
    return discharge_glyphs + charge_glyphs


def build_font(svg_paths, starting_codepoint, output_file):
    """Create and save the TTF with each SVG mapped to a codepoint."""
    # glyph names from filenames
    names = [p.stem for p in svg_paths]
    # codepoints sequence
    codepoints = [starting_codepoint + i for i in range(len(svg_paths))]

    # prepare FontBuilder
    fb = FontBuilder(EM_SIZE, isTTF=True)
    glyph_order = [".notdef"] + names
    fb.setupGlyphOrder(glyph_order)

    # draw each glyph and set metrics & cmap
    glyf = {}
    hmtx = {}
    cmap = {}

    # .notdef (empty glyph)
    glyf[".notdef"] = TTGlyphPen(None).glyph()
    hmtx[".notdef"] = (ADV_WIDTH, LSB)

    # for cp, name, svg in zip(codepoints, names, svg_paths):
    #     pen = TTGlyphPen(None)
    #     draw_scaled(svg, pen)
    #     glyf[name] = pen.glyph()
    #     hmtx[name] = (ADV_WIDTH, LSB)
    #     cmap[cp] = name

    for cp, name, svg in zip(codepoints, names, svg_paths):
        tt_pen = TTGlyphPen(None)
        quad_pen = Cu2QuPen(tt_pen, max_err=1.0, all_quadratic=True)
        extra_space = draw_scaled(svg, quad_pen)
        # SVGPath(str(svg)).draw(quad_pen)
        glyf[name] = tt_pen.glyph()
        hmtx[name] = (ADV_WIDTH, (extra_space/2))
        # hmtx[name] = (ADV_WIDTH, 0)
        cmap[cp] = name

    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=800, descent=-200, lineGap=0, numberOfHMetrics=len(hmtx))

    namestrings = {
        "copyright": "Copyright (c) 2025 Chris Waltrip",
        "familyName": "Battery Symbols",
        "styleName": "Regular",
        "uniqueFontIdentifier": "BatterySymbols-Regular",
        "fullName": "BatterySymbols-Regular",
        "version": "1.0",
        "psName": "BatterySymbols-Regular"
    }

    # basic tables
    fb.setupNameTable(nameStrings=namestrings)

    # cmap with BMP (format 4) + full (format 12) sub-tables
    fb.setupCharacterMap(cmap, allowFallback=False)

    # OS/2 table must come after cmap table
    fb.setupOS2()
    fb.setupHead()
    fb.setupPost()

    # ensure output dir exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(output_file))
    print(f"✅ Saved font: {output_file}")

    glyph_set = set(glyph_order)
    metrics_set = set(hmtx)
    missing = set(glyph_order) - set(metrics_set)
    print(f"🔢 numOfLongMetrics will be {len(metrics_set)}")
    print(f"🔢 missing: {len(missing)}")

    print("GLYPH ORDER:", list(glyph_order))
    print("METRICS KEYS:", list(hmtx.keys()))
    print("num glyphs:", len(glyph_order))
    print("num metrics:", len(hmtx))


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    build_dir = script_dir.joinpath("build")
    raw_dir = build_dir.joinpath("raw")
    processed_dir = build_dir.joinpath("processed")
    charge_dir = processed_dir.joinpath("charging")
    discharge_dir = processed_dir.joinpath("discharging")

    output_font_file = build_dir.joinpath("BatterySymbols-Regular.ttf")

    svgs = gather_svgs(discharge_dir, charge_dir)

    build_font(svgs, BASE_CODEPOINT, output_font_file)
