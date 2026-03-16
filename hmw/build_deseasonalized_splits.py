from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
import pandas as pd

import run_station_hour_regression as base


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
OUTPUT_DIR = DATA_DIR


def find_shared_dir() -> Path | None:
    for path in ROOT.parent.iterdir():
        if path.is_dir() and "공유" in path.name:
            return path
    return None


def resolve_data_file(name: str) -> Path:
    local = DATA_DIR / name
    if local.exists():
        return local
    shared_dir = find_shared_dir()
    if shared_dir is not None:
        shared = shared_dir / name
        if shared.exists():
            return shared
    raise FileNotFoundError(f"Missing required source file: {name}")


def load_flow() -> pd.DataFrame:
    path = resolve_data_file("station_hour_bike_flow_2023_2025.csv")
    df = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["time"])
    int_cols = [
        "station_id",
        "rental_count",
        "return_count",
        "bike_change",
        "bike_count_index",
        "year",
        "month",
        "day",
        "weekday",
        "hour",
    ]
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce", downcast="integer")
    return df


def build_base_dataset() -> pd.DataFrame:
    flow = load_flow()
    weather = base.load_weather()
    station_meta = base.load_station_meta()

    df = flow.merge(weather, on="time", how="left")
    df = df.merge(station_meta, on="station_id", how="left")
    df = base.add_calendar_features(df)
    df = base.add_weather_features(df)

    numeric_fill_zero = ["lat", "lon", "lcd_count", "qr_count", "dock_total", "is_qr_mixed"]
    for col in numeric_fill_zero:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.drop(columns=["date"])
    return df.sort_values(["station_id", "time"]).reset_index(drop=True)


def build_train_seasonal_tables(train_df: pd.DataFrame) -> dict[str, pd.DataFrame | pd.Series]:
    tables: dict[str, pd.DataFrame | pd.Series] = {}
    tables["hour_mean"] = train_df.groupby("hour")["bike_change"].mean()
    tables["weekday_hour_mean"] = train_df.groupby(["weekday", "hour"])["bike_change"].mean().reset_index(name="weekday_hour_mean")
    station_weekday_hour = train_df.groupby(["station_id", "weekday", "hour"])["bike_change"].agg(["mean", "count"]).reset_index()
    station_weekday_hour = station_weekday_hour.rename(columns={"mean": "station_weekday_hour_mean", "count": "station_weekday_hour_count"})
    tables["station_weekday_hour"] = station_weekday_hour

    tables["rental_weekday_hour_mean"] = train_df.groupby(["weekday", "hour"])["rental_count"].mean().reset_index(name="rental_weekday_hour_mean")
    tables["return_weekday_hour_mean"] = train_df.groupby(["weekday", "hour"])["return_count"].mean().reset_index(name="return_weekday_hour_mean")
    return tables


def apply_deseasonalization(df: pd.DataFrame, tables: dict[str, pd.DataFrame | pd.Series], min_count: int = 24) -> pd.DataFrame:
    out = df.copy()
    out["hour_mean"] = out["hour"].map(tables["hour_mean"])
    out = out.merge(tables["weekday_hour_mean"], on=["weekday", "hour"], how="left")
    out = out.merge(tables["station_weekday_hour"], on=["station_id", "weekday", "hour"], how="left")
    out = out.merge(tables["rental_weekday_hour_mean"], on=["weekday", "hour"], how="left")
    out = out.merge(tables["return_weekday_hour_mean"], on=["weekday", "hour"], how="left")

    weight = (out["station_weekday_hour_count"].fillna(0) / (out["station_weekday_hour_count"].fillna(0) + min_count)).clip(0, 1)
    station_component = out["station_weekday_hour_mean"].fillna(out["weekday_hour_mean"])
    fallback_component = out["weekday_hour_mean"].fillna(out["hour_mean"]).fillna(0)
    out["bike_change_seasonal_expected"] = weight * station_component + (1 - weight) * fallback_component
    out["bike_change_deseasonalized"] = out["bike_change"] - out["bike_change_seasonal_expected"]

    out["rental_count_deseasonalized"] = out["rental_count"] - out["rental_weekday_hour_mean"].fillna(0)
    out["return_count_deseasonalized"] = out["return_count"] - out["return_weekday_hour_mean"].fillna(0)
    out["seasonality_removed_flag"] = 1
    return out


def add_residual_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["station_id", "time"]).copy()
    group = out.groupby("station_id", sort=False)

    for lag in [1, 2, 24, 168]:
        out[f"bike_change_resid_lag_{lag}"] = group["bike_change_deseasonalized"].shift(lag).astype("float32")

    shifted = group["bike_change_deseasonalized"].shift(1)
    for window in [3, 24, 168]:
        out[f"bike_change_resid_rollmean_{window}"] = (
            shifted.groupby(out["station_id"]).rolling(window).mean().reset_index(level=0, drop=True).astype("float32")
        )
        out[f"bike_change_resid_rollstd_{window}"] = (
            shifted.groupby(out["station_id"]).rolling(window).std().reset_index(level=0, drop=True).fillna(0).astype("float32")
        )

    out["bike_change_resid_trend_1_24"] = out["bike_change_resid_lag_1"] - out["bike_change_resid_lag_24"]
    out["bike_change_resid_trend_24_168"] = out["bike_change_resid_lag_24"] - out["bike_change_resid_lag_168"]
    return out


def save_split(df: pd.DataFrame, filename: str):
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig", compression="gzip")
    return path


def main():
    df = build_base_dataset()
    train_df = df[df["year"] == 2023].copy()
    valid_df = df[df["year"] == 2024].copy()
    test_df = df[df["year"] == 2025].copy()

    seasonal_tables = build_train_seasonal_tables(train_df)
    train_out = add_residual_lag_features(apply_deseasonalization(train_df, seasonal_tables))
    valid_out = add_residual_lag_features(apply_deseasonalization(valid_df, seasonal_tables))
    test_out = add_residual_lag_features(apply_deseasonalization(test_df, seasonal_tables))

    train_out = train_out.dropna().reset_index(drop=True)
    valid_out = valid_out.dropna().reset_index(drop=True)
    test_out = test_out.dropna().reset_index(drop=True)

    train_path = save_split(train_out, "station_hour_bike_change_deseason_train_2023.csv.gz")
    valid_path = save_split(valid_out, "station_hour_bike_change_deseason_valid_2024.csv.gz")
    test_path = save_split(test_out, "station_hour_bike_change_deseason_test_2025.csv.gz")

    meta = {
        "target": "bike_change",
        "split_protocol": {"train": "2023", "valid": "2024", "test": "2025"},
        "deseasonalization": {
            "hour_mean_removed": True,
            "weekday_hour_mean_removed": True,
            "station_weekday_hour_smoothed_removed": True,
            "residual_lag_features_added": [1, 2, 24, 168],
            "residual_rolling_windows_added": [3, 24, 168],
        },
        "outputs": {
            "train": train_path.name,
            "valid": valid_path.name,
            "test": test_path.name,
        },
        "shapes": {
            "train_rows": len(train_out),
            "valid_rows": len(valid_out),
            "test_rows": len(test_out),
            "columns": len(train_out.columns),
        },
    }
    (OUTPUT_DIR / "station_hour_bike_change_deseason_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
