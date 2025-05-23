# battery-symbols
This repo will generate glyphs for representing a battery at all stages of charge from 0-100%.  Glyphs are generated using `svg-py`, and then cleaned up using the `inkscape` CLI.  Glyphs are fed to `fonttools` to create the font.

I should note that I'm not a font expert, and there's some work that this font needs, but for now it's working well enough.

## Examples
| 0% | 10% | 20% | 30% | 40% | 50% | 60% | 70% | 80% | 90% | 100% |
| :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
| <img src="examples/battery_discharge_000.svg" width="60" alt="Discharge 0%"><br><img src="examples/battery_charge_000.svg"   width="60" alt="Charge 0%"> | <img src="examples/battery_discharge_010.svg" width="60" alt="Discharge 10%"><br><img src="examples/battery_charge_010.svg"   width="60" alt="Charge 10%"> | <img src="examples/battery_discharge_020.svg" width="60" alt="Discharge 20%"><br><img src="examples/battery_charge_020.svg"   width="60" alt="Charge 20%"> | <img src="examples/battery_discharge_030.svg" width="60" alt="Discharge 30%"><br><img src="examples/battery_charge_030.svg"   width="60" alt="Charge 30%"> | <img src="examples/battery_discharge_040.svg" width="60" alt="Discharge 40%"><br><img src="examples/battery_charge_040.svg"   width="60" alt="Charge 40%"> | <img src="examples/battery_discharge_050.svg" width="60" alt="Discharge 50%"><br><img src="examples/battery_charge_050.svg"   width="60" alt="Charge 50%"> | <img src="examples/battery_discharge_060.svg" width="60" alt="Discharge 60%"><br><img src="examples/battery_charge_060.svg"   width="60" alt="Charge 60%"> | <img src="examples/battery_discharge_070.svg" width="60" alt="Discharge 70%"><br><img src="examples/battery_charge_070.svg"   width="60" alt="Charge 70%"> | <img src="examples/battery_discharge_080.svg" width="60" alt="Discharge 80%"><br><img src="examples/battery_charge_080.svg"   width="60" alt="Charge 80%"> | <img src="examples/battery_discharge_090.svg" width="60" alt="Discharge 90%"><br><img src="examples/battery_charge_090.svg"   width="60" alt="Charge 90%"> | <img src="examples/battery_discharge_100.svg" width="60" alt="Discharge 100%"><br><img src="examples/battery_charge_100.svg"   width="60" alt="Charge 100%"> |


## TODO
* Figure out the best way to scale and make glyphs properly fit.
* ~~Clean up the 0% glyphs; the glyphs themselves don't have a "charge level", but the final glyph has an artifact there.  Not sure what's causing it yet.~~ This may just be an artifact in macOS Font Book. 