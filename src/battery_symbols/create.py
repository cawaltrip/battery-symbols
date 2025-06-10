import xml.etree.ElementTree as Et
from pathlib import Path
from re import compile

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import SVGPath
from fontTools.ttLib import TTFont
from mistletoe import Document
from mistletoe.block_token import Heading
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText
from svgwrite import Drawing

from battery_symbols.config import (
    PROJECT_ROOT,
    EXAMPLES_DIR,
    RAW_DIR,
)

EM_SIZE = 1000  # units per em
# ADV_WIDTH = 600  # default advance‐width
ADV_WIDTH = 900
LSB = 50  # default left‐side bearing
BASE_CODEPOINT = 0xF2000  # starting codepoint


def get_viewbox(
    svg_file: Path,
) -> tuple[int | float, int | float, int | float, int | float]:
    root = Et.parse(svg_file).getroot()
    vb = root.attrib.get("viewBox", None)
    if vb:
        x0, y0, w, h = map(float, vb.split())
        return x0, y0, w, h
    pen = BoundsPen(None)
    SVGPath(str(svg_file)).draw(pen)
    if pen.bounds:
        x0, y0, x1, y1 = pen.bounds
        w = x1 - x0
        h = y1 - y0
        return x0, y0, w, h
    # fallback: hardcode or measure via a pen
    return 0, 0, 142, 66


def draw_scaled(
    svg_file: Path, pen: BasePen | TTGlyphPen, margin: float = 0.9
) -> int | float:
    x0, y0, w, h = get_viewbox(svg_file)
    scale = EM_SIZE * margin / max(w, h)
    glyph_width = w * scale
    extra_space: int | float = EM_SIZE - glyph_width
    tx = -x0 * scale + extra_space / 2
    ty = (h + y0) * scale
    t_pen = TransformPen(pen, (scale, 0, 0, scale, tx, -ty))
    SVGPath(str(svg_file)).draw(t_pen)
    return extra_space


def gather_svgs(raw_dir: Path) -> list[Path]:
    svg_paths = sorted(raw_dir.glob("**/*.svg"))
    return svg_paths


def build_font(
    svg_paths: list[Path], starting_codepoint: int, output_file: Path
) -> None:
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

    for cp, name, svg in zip(codepoints, names, svg_paths, strict=False):
        tt_pen = TTGlyphPen(None)
        # quad_pen = Cu2QuPen(tt_pen, max_err=1.0, all_quadratic=True)
        # extra_space = draw_scaled(svg, quad_pen)
        extra_space = draw_scaled(svg, tt_pen)
        # SVGPath(str(svg)).draw(quad_pen)
        glyf[name] = tt_pen.glyph()
        hmtx[name] = (ADV_WIDTH, int(extra_space / 2))
        # hmtx[name] = (ADV_WIDTH, 0)
        cmap[cp] = name

    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(
        ascent=800, descent=-200, lineGap=0, numberOfHMetrics=len(hmtx)
    )

    namestrings = {
        "copyright": "Copyright (c) 2025 Chris Waltrip",
        "familyName": "Battery Symbols",
        "styleName": "Regular",
        "uniqueFontIdentifier": "BatterySymbols-Regular",
        "fullName": "BatterySymbols-Regular",
        "version": "1.0",
        "psName": "BatterySymbols-Regular",
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


def extract_and_save_sample_glyphs(font_path: Path, output_path: Path) -> list[str]:
    """
    Extract sample glyphs from the font we've created.  Probably good to have
    the charged and discharged glyphs for charge_level % 10 == 0.  We know
    the order of the glyphs, so given the starting codepoint we can grab those.
    :return:
    List of glyphs that can be converted to SVGs.
    """

    font = TTFont(str(font_path))
    glyph_set = font.getGlyphSet()
    glyph_order = font.getGlyphOrder()
    battery_name_dict: dict[str, int] = {}

    pattern = compile(r"_(\d{3})$")
    battery_name_pattern = compile(r"battery_([^_]+)_(charge|discharge)_(\d{3})$")

    for name in glyph_order:
        match = pattern.search(name)
        if not match:
            continue
        percent = int(match.group(1))
        if percent % 10:
            continue

        try:
            # glyph = glyph_set[name]
            glyph = glyph_set.glyfTable.glyphs[name]
            position = glyph_order.index(name)
            try:
                battery_name = battery_name_pattern.search(name).group(1)  # type: ignore
            except AttributeError:
                print(f"Glyph {name} does not match expected pattern.")
                continue
            if battery_name not in battery_name_dict.keys():
                battery_name_dict[battery_name] = position

            if battery_name_dict[battery_name] > position:
                battery_name_dict[battery_name] = position
        except KeyError:
            print(f"Glyph {name} not found in glyfTable.")
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

    return sorted(battery_name_dict, key=battery_name_dict.__getitem__)


def write_cheatsheet(
    examples_path: Path, readme_dir: Path, battery_list: list[str]
) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    width_px = 60  # tweak to taste
    for battery_name in battery_list:
        files: dict[int, dict[str, Path]] = {}
        pattern = compile(
            r"battery_" + battery_name + r"_(charge|discharge)_(\d{3})\.svg$"
        )  # noqa: E501

        filelist = sorted(examples_path.glob("**/*.svg"))
        for file_ in filelist:
            match = pattern.match(file_.name)
            if not match:
                continue
            kind, num_str = match.groups()  # e.g. kind="charge", num_str="010"
            pct = int(num_str)  # 10
            files.setdefault(pct, {})[kind] = file_.relative_to(readme_dir)
        files = {k: files[k] for k in sorted(files)}

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
        result.append((battery_name, "\n".join(lines)))

    return result


def _get_section_heading(token: Heading) -> str:
    """Flatten a Heading node’s RawText children into a single string."""
    return "".join(
        child.content for child in token.children if isinstance(child, RawText)
    )


def replace_cheatsheet(
    readme_path: Path,
    new_content: list[tuple[str, str]],
    cheatsheet_heading: str = "Examples",
) -> None:
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

            if capture and node.level <= heading_level:
                capture_end = i
                break

    if capture_start is None:
        return

    final_content = ""
    for subheading, content in new_content:
        final_content += (
            f"{'#' * (heading_level + 1)} {subheading.title()} Style\n{content}\n"
        )

    frag_doc = Document(final_content.splitlines(keepends=True))
    new_tokens = frag_doc.children

    new_readme = doc.children[0 : capture_start + 1]
    new_readme += new_tokens

    if capture_end is not None:
        new_readme += doc.children[capture_end:]

    doc.children = new_readme

    with open(readme_path, "w") as f:
        with MarkdownRenderer() as renderer:
            f.write(renderer.render(doc))


def main() -> None:
    output_font_file = PROJECT_ROOT / "BatterySymbols-Regular.ttf"
    readme_file = PROJECT_ROOT / "README.md"

    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    svgs = gather_svgs(RAW_DIR)

    build_font(svgs, BASE_CODEPOINT, output_font_file)
    battery_name_list = extract_and_save_sample_glyphs(output_font_file, EXAMPLES_DIR)
    cheatsheet_content = write_cheatsheet(EXAMPLES_DIR, PROJECT_ROOT, battery_name_list)
    replace_cheatsheet(readme_file, cheatsheet_content)


if __name__ == "__main__":
    main()
