from pathlib import Path
from .models import Battery

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main():
    build_dir = PROJECT_ROOT / "build"
    raw_dir = build_dir / "raw"
    charge_dir = raw_dir / "charging"
    discharge_dir = raw_dir / "discharging"
    raw_dir.mkdir(parents=True, exist_ok=True)
    charge_dir.mkdir(parents=True, exist_ok=True)
    discharge_dir.mkdir(parents=True, exist_ok=True)

    for charge in [True, False]:
        for i in range(101):
            glyph_name = f"battery_{'charge' if charge else 'discharge'}_{i:0>3}.svg"
            out_dir = charge_dir if charge else discharge_dir
            glyph_path = out_dir.joinpath(glyph_name)

            glyph = Battery(width=120, charging=charge, level=i)
            svg_doc = glyph.build_svg()

            with glyph_path.open('w') as f:
                f.write(str(svg_doc))

if __name__ == "__main__":
    main()