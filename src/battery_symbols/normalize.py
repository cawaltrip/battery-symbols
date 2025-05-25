from pathlib import Path
from subprocess import run, CalledProcessError, DEVNULL
from .config import (
    RAW_DIR,
    RAW_CHARGE_DIR,
    PROCESSED_CHARGE_DIR,
    PROCESSED_DISCHARGE_DIR,
)
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _generate_svg_actions(svg_file: Path) -> str:
    charge_level = int(svg_file.stem.split("_")[2])
    if svg_file.is_relative_to(RAW_CHARGE_DIR):
        final_dir = PROCESSED_CHARGE_DIR
    else:
        final_dir = PROCESSED_DISCHARGE_DIR
    processed_filename = final_dir.joinpath(svg_file.name)
    try:
        actions_commands = [
            f"file-open:{svg_file.relative_to(PROJECT_ROOT)}",
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

        if svg_file.is_relative_to(RAW_CHARGE_DIR):
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
        print(f"cannot find path for: {svg_file.name}")
        actions_commands = []

    actions = ";".join(actions_commands)
    return actions


def _run_inkscape(actions: str) -> None:
    """
    Invoke Inkscape on a single file.
    Adjust the args list to your actual command-line flags.
    """
    run(
        ["inkscape", "--batch-process", f"--actions={actions}"],
        check=True,
        stdout=DEVNULL,
        stderr=DEVNULL,
    )


def _batch_process_svg(svg_files: list[Path]) -> None:
    """
    Process a list of input files through Inkscape in parallel.
    """
    with ThreadPoolExecutor() as executor:
        futures = {}
        for f in svg_files:
            action = _generate_svg_actions(f)
            svg_file = f.relative_to(RAW_DIR)
            futures[executor.submit(_run_inkscape, action)] = svg_file

        for fut in as_completed(futures):
            inp = futures[fut]
            try:
                fut.result()
                print(f"[OK]  {inp.name}")
            except CalledProcessError as e:
                print(f"[ERR] {inp.name} → {e}")


def main() -> None:
    PROCESSED_CHARGE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DISCHARGE_DIR.mkdir(parents=True, exist_ok=True)

    svg_files = [x for x in RAW_DIR.glob("**/*.svg") if x.is_file()]
    _batch_process_svg(svg_files)


if __name__ == "__main__":
    main()
