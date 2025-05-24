from pathlib import Path
from subprocess import run

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main():
    build_dir = PROJECT_ROOT / "build"
    raw_dir = build_dir / "raw"
    raw_charge_dir = raw_dir / "charging"
    # raw_discharge_dir = raw_dir / "discharging"
    processed_dir = build_dir / "processed"
    charge_dir = processed_dir / "charging"
    discharge_dir = processed_dir / "discharging"

    charge_dir.mkdir(parents=True, exist_ok=True)
    discharge_dir.mkdir(parents=True, exist_ok=True)

    svg_files = [x for x in raw_dir.glob("**/*.svg") if x.is_file()]

    for f in svg_files:
        charge_level = int(f.stem.split("_")[2])
        if f.is_relative_to(raw_charge_dir):
            processed_dir = charge_dir
        else:
            processed_dir = discharge_dir
        processed_filename = processed_dir.joinpath(f.name)

        try:
            actions_commands = [
                f"file-open:{f.relative_to(PROJECT_ROOT)}",
                "select-by-id:battery-case",
                "object-stroke-to-path",
                "unselect-by-id:battery-case",
                "select-by-id:charge-level",
            ]
            if charge_level == 0:
                actions_commands += ["delete-selection"]
            else:
                actions_commands += [
                    "object-to-path",
                    "unselect-by-id:charge-level",
                ]

            if f.is_relative_to(raw_charge_dir):
                actions_commands += [
                    "select-by-id:lightning-bolt-bc-mask",
                    "object-stroke-to-path",
                    "unselect-by-id:lightning-bolt-bc-mask",
                    "select-by-id:path1,path2",
                    "path-union",
                    "unselect-by-id:path1",
                    "select-by-id:battery-case,path1",
                    "path-difference",
                    "unselect-by-id:battery-case",
                    "select-by-id:lightning-bolt-bc-mask",
                    "delete-selection",
                    "select-by-id:lightning-bolt-cl-mask",
                ]
                if charge_level != 0:
                    actions_commands += [
                        "object-stroke-to-path",
                        "unselect-by-id:lightning-bolt-cl-mask",
                        "select-by-id:path2,path3",
                        "path-union",
                        "unselect-by-id:path2",
                        "select-by-id:charge-level,path2",
                        "path-difference",
                        "unselect-by-id:charge-level",
                        "select-by-id:lightning-bolt-cl-mask",
                    ]
                actions_commands += ["delete-selection"]

            actions_commands += [
                "export-plain-svg",
                f"export-filename:{processed_filename.relative_to(PROJECT_ROOT)}",
                "export-do;",
            ]
        except ValueError:
            print(f"cannot find path for: {f.name}")
            continue

        actions = ";".join(actions_commands)
        print(f"actions = {actions}")

        run(["inkscape", "--batch-process", f"--actions={actions}"], check=True)


if __name__ == "__main__":
    main()
