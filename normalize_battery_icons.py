from subprocess import run
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    build_dir = script_dir.joinpath("build")
    raw_dir = build_dir.joinpath("raw")
    raw_charge_dir = raw_dir.joinpath("charging")
    raw_discharge_dir = raw_dir.joinpath("discharging")
    processed_dir = build_dir.joinpath("processed")
    charge_dir = processed_dir.joinpath("charging")
    discharge_dir = processed_dir.joinpath("discharging")

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
                f"file-open:{f.relative_to(script_dir)}",
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
                actions_commands += [
                    "delete-selection"
                ]

            actions_commands += [
              "export-plain-svg",
              f"export-filename:{processed_filename.relative_to(script_dir)}",
              "export-do;"
            ]
        except ValueError:
            print(f"cannot find path for: {f.name}")
            continue

        actions = ';'.join(actions_commands)
        print(f"actions = {actions}")

        try:
            run([
                "inkscape",
                "--batch-process",
                f"--actions={actions}"
            ], check=True)
        except:
            print("something failed")


# 1) Run Inkscape in batch-mode to convert the stroke-to-path
# run([
#     "inkscape",
#     "--batch-process",                       # no interactive GUI
#     "--select=lightning-bolt-mask",          # choose your element
#     "--actions=ObjectToPath;FileSave;FileClose",
#     "battery.svg"
# ], check=True)
#
# # 2) Now load the updated file with pyinkscape
# canvas = Canvas("battery.svg")
# # … proceed to wrap the now-stroketopath element in a mask or clipPath …
# canvas.render("battery-stroked-masked.svg")
