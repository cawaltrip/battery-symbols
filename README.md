# battery-symbols
This repo will generate glyphs for representing a battery at all stages of charge from 0-100%.  Glyphs are generated using `svg-py`, and then cleaned up using the `inkscape` CLI.  Glyphs are fed to `fonttools` to create the font.

I should note that I'm not a font expert, and there's some work that this font needs, but for now it's working well enough.



## TODO
* Figure out the best way to scale and make glyphs properly fit.
* Clean up the 0% glyphs; the glyphs themselves don't have a "charge level", but the final glyph has an artifact there.  Not sure what's causing it yet. 