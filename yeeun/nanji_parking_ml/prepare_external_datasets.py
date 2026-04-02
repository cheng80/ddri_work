from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DATE_CANDIDATES = [
    "timestamp",
    "date",
    "datetime",
    "기준일자",
    "영업시작일자",
    "공연시작일자",
    "공연종료일자",
    "start_date",
    "end_date",
]

START_DATE_CANDIDATES = ["timestamp", "date", "datetime", "영업시작일자", "공연시작일자", "start_date"]
END_DATE_CANDIDATES = ["공연종료일자", "end_date"]


@dataclass
class CleanResult:
    cleaned_df: pd.DataFrame
    summary: dict[str, object]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean Nanji external datasets for 2023-2025 modeling use.")
    parser.add_argument(
        "--input-dir",
        default="yeeun/nanji_parking_ml/external_data_plan/data/raw",
        help="Directory containing raw CSV/XLS/XLSX files.",
    )
    parser.add_argument(
        "--output-dir",
        default="yeeun/nanji_parking_ml/external_data_plan/data/processed",
        help="Directory where cleaned outputs will be saved.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="Years to keep when date columns are available.",
    )
    return parser.parse_args()


def normalize_column_name(name: str) -> str:
    out = str(name).strip().lower()
    replacements = {
        " ": "_",
        "-": "_",
        "/": "_",
        "(": "",
        ")": "",
        "[": "",
        "]": "",
    }
    for before, after in replacements.items():
        out = out.replace(before, after)
    return out


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "cp949", "utf-8"):
            try:
                return pd.read_csv(path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("csv", b"", 0, 1, f"Unable to decode {path.name}")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def detect_category(df: pd.DataFrame, path: Path) -> str:
    cols = set(df.columns)
    name = path.stem.lower()
    if {"parking_lot_id", "parking_lot_name", "total_spaces"} <= cols or {"available_spaces", "occupied_spaces"} & cols:
        return "parking"
    if {"공연명", "공연시설명"} & cols or {"performance_name", "venue_name"} <= cols:
        return "performance"
    if "holiday_name" in cols or "is_holiday" in cols:
        return "calendar"
    if "temperature_2m" in cols or "weather_temp_c" in cols:
        return "weather"
    if "camping_site_count" in cols or "캠핑사이트수" in cols or "camp" in name:
        return "camping"
    return "generic"


def coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in set(START_DATE_CANDIDATES + END_DATE_CANDIDATES):
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def add_year_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in START_DATE_CANDIDATES:
        if col in out.columns and pd.api.types.is_datetime64_any_dtype(out[col]):
            out["source_year"] = out[col].dt.year
            return out
    return out


def filter_years(df: pd.DataFrame, years: set[int]) -> pd.DataFrame:
    out = df.copy()
    start_col = next((col for col in START_DATE_CANDIDATES if col in out.columns and pd.api.types.is_datetime64_any_dtype(out[col])), None)
    end_col = next((col for col in END_DATE_CANDIDATES if col in out.columns and pd.api.types.is_datetime64_any_dtype(out[col])), None)

    if start_col is None:
        return out

    start_year = out[start_col].dt.year
    if end_col is None:
        return out[start_year.isin(years) | out[start_col].isna()].copy()

    end_year = out[end_col].dt.year.fillna(start_year)
    keep_mask = start_year.isin(years) | end_year.isin(years)
    return out[keep_mask | out[start_col].isna()].copy()


def infer_critical_columns(df: pd.DataFrame, category: str) -> list[str]:
    category_candidates = {
        "parking": ["timestamp", "total_spaces", "available_spaces"],
        "camping": ["campground_name", "road_address", "business_start_date", "camping_site_count"],
        "performance": ["performance_name", "venue_name", "performance_start_date"],
        "weather": ["timestamp", "temperature_2m", "weather_temp_c"],
        "calendar": ["date", "holiday_name", "is_holiday"],
        "generic": ["timestamp", "date"],
    }
    cols = []
    for col in category_candidates.get(category, []):
        if col in df.columns:
            cols.append(col)
    if not cols:
        cols = [col for col in DATE_CANDIDATES if col in df.columns][:1]
    return cols


def infer_numeric_targets(df: pd.DataFrame, category: str) -> list[str]:
    category_candidates = {
        "parking": ["total_spaces", "available_spaces", "occupied_spaces", "weather_temp_c", "weather_precip_mm", "weather_humidity"],
        "camping": ["camping_site_count"],
        "weather": ["temperature_2m", "precipitation", "relative_humidity_2m", "wind_speed_10m", "weather_temp_c", "weather_precip_mm", "weather_humidity", "weather_wind_speed"],
        "generic": [],
    }
    preferred = [col for col in category_candidates.get(category, []) if col in df.columns]
    if preferred:
        return preferred
    return [col for col in df.select_dtypes(include=[np.number]).columns if df[col].notna().sum() >= 4]


def remove_missing_rows(df: pd.DataFrame, critical_columns: list[str]) -> tuple[pd.DataFrame, int]:
    if not critical_columns:
        return df.copy(), 0
    before = len(df)
    cleaned = df.dropna(subset=critical_columns, how="any").copy()
    return cleaned, before - len(cleaned)


def remove_iqr_outliers(df: pd.DataFrame, numeric_columns: list[str]) -> tuple[pd.DataFrame, int, list[str]]:
    if df.empty or not numeric_columns:
        return df.copy(), 0, []

    bounds = {}
    used_columns: list[str] = []
    for col in numeric_columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 4:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        bounds[col] = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        used_columns.append(col)

    if not bounds:
        return df.copy(), 0, []

    mask = pd.Series(True, index=df.index)
    for col, (lower, upper) in bounds.items():
        numeric = pd.to_numeric(df[col], errors="coerce")
        mask &= numeric.isna() | numeric.between(lower, upper)

    cleaned = df.loc[mask].copy()
    return cleaned, len(df) - len(cleaned), used_columns


def clean_dataset(df: pd.DataFrame, path: Path, years: set[int]) -> CleanResult:
    out = df.copy()
    out.columns = [normalize_column_name(col) for col in out.columns]
    out = coerce_dates(out)
    out = add_year_columns(out)

    category = detect_category(out, path)
    initial_rows = len(out)
    out = filter_years(out, years)
    after_year_filter = len(out)

    critical_columns = infer_critical_columns(out, category)
    out, missing_removed = remove_missing_rows(out, critical_columns)

    numeric_columns = infer_numeric_targets(out, category)
    outlier_cleaned, outliers_removed, outlier_columns = remove_iqr_outliers(out, numeric_columns)

    summary = {
        "source_file": path.name,
        "category": category,
        "initial_rows": initial_rows,
        "rows_after_year_filter": after_year_filter,
        "rows_after_cleaning": len(outlier_cleaned),
        "removed_missing_rows": missing_removed,
        "removed_outlier_rows": outliers_removed,
        "critical_columns": critical_columns,
        "outlier_columns": outlier_columns,
        "years_requested": sorted(years),
    }
    return CleanResult(cleaned_df=outlier_cleaned.reset_index(drop=True), summary=summary)


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_paths = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls"}
    )
    if not raw_paths:
        raise FileNotFoundError(f"No raw CSV/XLS/XLSX files found in {input_dir}")

    summary_rows = []
    for raw_path in raw_paths:
        df = read_table(raw_path)
        result = clean_dataset(df, raw_path, set(args.years))

        cleaned_name = f"{raw_path.stem}_cleaned.csv"
        result.cleaned_df.to_csv(output_dir / cleaned_name, index=False, encoding="utf-8-sig")
        summary_rows.append(result.summary)

    summary_df = pd.DataFrame(summary_rows).sort_values(["category", "source_file"]).reset_index(drop=True)
    summary_df.to_csv(output_dir / "cleaning_summary.csv", index=False, encoding="utf-8-sig")
    (output_dir / "cleaning_summary.json").write_text(
        json.dumps(summary_rows, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"Cleaned {len(summary_rows)} file(s).")
    print(f"Processed data saved to: {output_dir}")


if __name__ == "__main__":
    main()
