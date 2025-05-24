from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import SVGPath
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from svgwrite import Drawing
import xml.etree.ElementTree as ET
from re import compile
from mistletoe import Document
from mistletoe.block_token import tokenize
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText
from mistletoe.block_token import Heading

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
    glyph_width = w * scale
    extra_space = EM_SIZE - glyph_width
    tx = -x0 * scale + extra_space / 2
    ty = -y0 * scale
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
    print(f"Wrote {output_file}.")


def extract_and_save_sample_glyphs(font_path: Path, output_path: Path):
    """
    Extract sample glyphs from the font we've created.  Probably good to have
    the charged and discharged glyphs for charge_level % 10 == 0.  We know
    the order of the glyphs, so given the starting codepoint we can grab those.
    :return:
    List of glyphs that can be converted to SVGs.
    """

    font = TTFont(str(font_path))
    glyph_set = font.getGlyphSet()

    icons = [f"battery_charge_{(10 * i):0>3}" for i in range(11)]
    icons += [f"battery_discharge_{(10 * i):0>3}" for i in range(11)]

    for name in icons:
        try:
            glyph = glyph_set.glyfTable.glyphs[name]
        except KeyError:
            print(f"Glyph {name} not found.")
            continue
        pen = SVGPathPen(glyph_set)
        glyph.draw(pen, glyph_set.glyfTable)
        x_min, y_min, x_max, y_max = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
        width = x_max - x_min
        height = y_max - y_min

        path = pen.getCommands()

        filename = output_path / f"{name}.svg"
        drawing = Drawing(str(filename), viewBox=f"{x_min} {y_min} {width} {height}")
        drawing.add(drawing.path(d=path))
        drawing.save()

def write_cheatsheet(svg_path: Path, root_dir: Path, readme_path: Path):
    filelist = svg_path.glob("**/*.svg")
    pattern = compile(r"battery_(charge|discharge)_(\d{3})\.svg$")
    files = {}

    for path in filelist:
        m = pattern.match(path.name)
        if not m:
            continue

        kind, num_str = m.groups()  # e.g. kind="charge", num_str="010"
        pct = int(num_str)  # 10
        # initialize sub-dict if needed, then assign
        files.setdefault(pct, {})[kind] = path.relative_to(root_dir)

    # if you want the keys sorted:
    files = {k: files[k] for k in sorted(files)}

    result = {"files": files}

    width_px = 60  # tweak to taste
    lines = []

    # 1) header row
    pct_list = sorted(files)
    header = "| " + " | ".join(f"{p}%" for p in pct_list) + " |"
    lines.append(header)

    # 2) alignment row (centered)
    align = "| " + " | ".join(":--:" for _ in pct_list) + " |"
    lines.append(align)

    # 3) content row
    cells = []
    for p in pct_list:
        fn = files[p]
        cell = (
            f'<img src="{fn["discharge"]}" width="{width_px}" alt="Discharge {p}%"><br>'
            f'<img src="{fn["charge"]}"   width="{width_px}" alt="Charge {p}%">'
        )
        cells.append(cell)

    lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def _get_section_heading(token):
    """Flatten a Heading node’s RawText children into a single string."""
    return ''.join(
        child.content
        for child in token.children
        if isinstance(child, RawText)
    )


def replace_cheatsheet(readme_path: Path, new_content: str, cheatsheet_heading: str = "Examples"):
    try:
        with open(readme_path) as f:
            doc = Document(f)
            # with MarkdownRenderer() as renderer:
            #     rendered = renderer.render(doc)
    except FileNotFoundError:
        print(f"{readme_path} not found.")
        return

    capture = False
    capture_start = None
    capture_end = None
    heading_level = -1
    for i, node in enumerate(doc.children):
        if isinstance(node, Heading):
            heading = _get_section_heading(node)
            if heading == cheatsheet_heading:
                # Found where we want to be.
                capture_start = i
                heading_level = node.level
                capture = True
                continue

            if capture and node.level >= heading_level:
                capture_end = i
                capture = False
                break

    if capture_start is None:
        return

    frag_doc = Document(new_content.splitlines(keepends=True))
    new_tokens = frag_doc.children

    new_readme = doc.children[0:capture_start + 1]
    new_readme += new_tokens

    if capture_end is not None:
        new_readme += doc.children[capture_end:]

    doc.children = new_readme

    with open(readme_path, "w") as f:
        with MarkdownRenderer() as renderer:
            f.write(renderer.render(doc))




def main():
    build_dir = PROJECT_ROOT / "build"
    processed_dir = build_dir / "processed"
    charge_dir = processed_dir / "charging"
    discharge_dir = processed_dir / "discharging"
    examples_dir = PROJECT_ROOT / "examples"
    output_font_file = PROJECT_ROOT / "BatterySymbols-Regular.ttf"
    readme_file = PROJECT_ROOT / "README.md"

    examples_dir.mkdir(parents=True, exist_ok=True)

    svgs = gather_svgs(discharge_dir, charge_dir)

    build_font(svgs, BASE_CODEPOINT, output_font_file)
    extract_and_save_sample_glyphs(output_font_file, examples_dir)
    cheatsheet_content = write_cheatsheet(examples_dir, PROJECT_ROOT, readme_file)
    replace_cheatsheet(readme_file, cheatsheet_content)

if __name__ == "__main__":
    main()
