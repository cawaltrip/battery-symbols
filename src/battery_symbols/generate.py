from battery_symbols.models import SimpleBattery, NumberBattery
from battery_symbols.config import (
    RAW_DIR,
    FONTS_DIR,
)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    font_path = FONTS_DIR / "OpenSans-Variable.ttf"

    batteries = [(SimpleBattery, "simple"), (NumberBattery, "number")]  # type: ignore
    for battery_order_index, battery in enumerate(batteries):
        for charge in [True, False]:
            for i in range(101):
                out_dir = RAW_DIR / f"style_{battery_order_index}"
                out_dir.mkdir(parents=True, exist_ok=True)
                glyph_name = f"battery_{battery[1]}_{'charge' if charge else 'discharge'}_{i:0>3}.svg"
                glyph_path = out_dir / glyph_name

                glyph = battery[0](
                    width=120, charging=charge, level=i, font_path=font_path
                )
                glyph.build_svg(glyph_path)


if __name__ == "__main__":
    main()
