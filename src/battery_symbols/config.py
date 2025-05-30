from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILD_DIR = PROJECT_ROOT / "build"
EXAMPLES_DIR = PROJECT_ROOT / "examples"

RAW_DIR = BUILD_DIR / "raw"
RAW_CHARGE_DIR = RAW_DIR / "charging"
RAW_DISCHARGE_DIR = RAW_DIR / "discharging"

PROCESSED_DIR = BUILD_DIR / "processed"
PROCESSED_CHARGE_DIR = PROCESSED_DIR / "charging"
PROCESSED_DISCHARGE_DIR = PROCESSED_DIR / "discharging"
