from __future__ import annotations

import re
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
HMW3_DIR = ROOT / "hmw3"
DATA_DIR = HMW3_DIR / "Data"


DATA_SUBDIRS = [
    "station_raw",
    "holiday_reference",
    "formulas",
    "weights",
    "tuning",
    "metrics",
    "predictions",
    "coefficients",
    "feature_analysis",
    "comparisons",
    "summaries",
]


TEXT_FILE_SUFFIXES = {".py", ".md", ".ipynb"}


def classify_filename(filename: str) -> str | None:
    if filename in {
        "summaries/selected5_station_metrics_summary.csv",
        "summaries/top20_station_metrics_summary.csv",
        "summaries/top20_station_combined_test_r2_ranking.csv",
    }:
        return "summaries"

    if re.fullmatch(r"station_\d{4}\.csv", filename):
        return "station_raw"

    suffix_map = {
        "_holiday_reference.csv": "holiday_reference",
        "_offday_hour_formulas.csv": "formulas",
        "_month_weights.csv": "weights",
        "_offday_month_ridge_tuning.csv": "tuning",
        "_offday_month_ridge_metrics.csv": "metrics",
        "_offday_month_ridge_predictions_long.csv": "predictions",
        "_offday_month_ridge_coefficients.csv": "coefficients",
        "_feature_correlation_long.csv": "feature_analysis",
        "_feature_importance.csv": "feature_analysis",
        "_year_actual_vs_regression_vs_ml.csv": "comparisons",
        "_2025_high_error_points.csv": "comparisons",
    }

    for suffix, folder in suffix_map.items():
        if filename.endswith(suffix):
            return folder
    return None


def move_data_files() -> dict[str, str]:
    replacements: dict[str, str] = {}
    for subdir in DATA_SUBDIRS:
        (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)

    for path in DATA_DIR.iterdir():
        if not path.is_file():
            continue
        subdir = classify_filename(path.name)
        if not subdir:
            continue
        dest = DATA_DIR / subdir / path.name
        shutil.move(str(path), str(dest))
        replacements[path.name] = f"{subdir}/{path.name}"
    return replacements


def update_text_references(replacements: dict[str, str]) -> list[Path]:
    updated_files: list[Path] = []
    for path in HMW3_DIR.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_FILE_SUFFIXES:
            continue
        original = path.read_text(encoding="utf-8")
        updated = original
        for old_name, new_rel in replacements.items():
            updated = updated.replace(old_name, new_rel)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            updated_files.append(path)
    return updated_files


def main() -> None:
    replacements = move_data_files()
    updated_files = update_text_references(replacements)
    print("Moved files:")
    for old_name, new_rel in sorted(replacements.items()):
        print(f"- {old_name} -> {new_rel}")
    print("Updated files:")
    for path in updated_files:
        print(f"- {path}")


if __name__ == "__main__":
    main()
