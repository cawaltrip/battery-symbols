from fontTools.ttLib import TTFont
from pathlib import Path
from battery_symbols.config import PROJECT_ROOT


def extract_glyphs(font_path: Path) -> dict[str, int]:
    """
    Extract a character from the font by its codepoint.

    Args:
        font_path: The location of the font to extract from.

    Returns:
        The glyphs and their names as a list of tuples.
    """
    font = TTFont(font_path)
    cmap = font["cmap"].getBestCmap()

    unsorted_glyphs = {
        glyph_name: codepoint
        for codepoint, glyph_name in cmap.items()
        if glyph_name != ".notdef"
    }
    glyphs = {}

    for glyph_name in font.glyphOrder:
        if glyph_name == ".notdef":
            continue
        if glyph_name in unsorted_glyphs:
            glyphs[glyph_name] = unsorted_glyphs[glyph_name]

    return glyphs


def print_output(glyphs: dict[str, int]) -> None:
    """
    Print the codepoints and names of the glyphs.

    Args:
        glyphs: A dictionary of all glyph names and their respective codepoints.
    """
    for name, glyph in glyphs.items():
        print(f"i='{chr(glyph)}' i_bs_{name}=$i")


def main() -> None:
    font = PROJECT_ROOT / "BatterySymbols-Regular.ttf"
    glyphs = extract_glyphs(font)

    print_output(glyphs)


if __name__ == "__main__":
    main()
