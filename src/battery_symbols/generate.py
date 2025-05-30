from battery_symbols.models import Battery
from battery_symbols.config import (
    RAW_DIR,
    RAW_CHARGE_DIR,
    RAW_DISCHARGE_DIR,
)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RAW_CHARGE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DISCHARGE_DIR.mkdir(parents=True, exist_ok=True)

    for charge in [True, False]:
        for i in range(101):
            glyph_name = f"battery_{'charge' if charge else 'discharge'}_{i:0>3}.svg"
            out_dir = RAW_CHARGE_DIR if charge else RAW_DISCHARGE_DIR
            glyph_path = out_dir.joinpath(glyph_name)

            glyph = Battery(width=120, charging=charge, level=i)
            glyph.build_svg(glyph_path)


if __name__ == "__main__":
    main()
