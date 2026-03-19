from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"

SOURCE_PATHS = {
    "train": DATA_DIR / "station_hour_bike_change_deseason_train_2023.parquet",
    "valid": DATA_DIR / "station_hour_bike_change_deseason_valid_2024.parquet",
    "test": DATA_DIR / "station_hour_bike_change_deseason_test_2025.parquet",
}

CLUSTER_PATH = DATA_DIR / "clustering" / "ddri_second_cluster_train_with_labels.csv"

OUTPUT_PATHS = {
    "train": DATA_DIR / "station_hour_bike_change_tplus1_pure_train_2023.parquet",
    "valid": DATA_DIR / "station_hour_bike_change_tplus1_pure_valid_2024.parquet",
    "test": DATA_DIR / "station_hour_bike_change_tplus1_pure_test_2025.parquet",
}

FINAL_FEATURE_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_features.csv"
CORR_DROP_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_corr_drops.csv"
CORR_TARGET_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_feature_target_correlation.csv"
META_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_meta.json"

RANDOM_STATE = 42


def load_cluster_features() -> pd.DataFrame:
    labels = pd.read_csv(CLUSTER_PATH, encoding="utf-8-sig")
    keep_cols = [
        "station_id",
        "cluster",
        "mapped_dong_code",
        "total_return_count",
        "return_7_10_count",
        "return_11_14_count",
        "return_17_20_count",
        "dominant_ratio",
        "life_pop_7_10_mean",
        "life_pop_11_14_mean",
        "life_pop_17_20_mean",
        "arrival_7_10_ratio",
        "arrival_11_14_ratio",
        "arrival_17_20_ratio",
        "morning_net_inflow",
        "evening_net_inflow",
        "subway_distance_m",
        "bus_stop_count_300m",
    ]
    out = labels[keep_cols].drop_duplicates("station_id").copy()
    out["station_id"] = pd.to_numeric(out["station_id"], errors="coerce").astype("Int64")
    for col in keep_cols:
        if col != "station_id":
            out[col] = pd.to_numeric(out[col], errors="coerce")
    out["cluster"] = out["cluster"].fillna(-1).astype(int)
    out["mapped_dong_code"] = out["mapped_dong_code"].fillna(-1).astype(int)
    return out


def cyclical_encode(series: pd.Series, period: int, prefix: str) -> pd.DataFrame:
    angle = 2.0 * math.pi * series.astype(float) / period
    return pd.DataFrame(
        {
            f"{prefix}_sin": np.sin(angle),
            f"{prefix}_cos": np.cos(angle),
        },
        index=series.index,
    )


def add_known_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    next_time = out["time"] + pd.Timedelta(hours=1)
    out["feature_hour"] = out["time"].dt.hour.astype(int)
    out["feature_weekday"] = out["time"].dt.weekday.astype(int)
    out["feature_month"] = out["time"].dt.month.astype(int)
    out["target_time"] = next_time
    out["target_hour"] = next_time.dt.hour.astype(int)
    out["target_weekday"] = next_time.dt.weekday.astype(int)
    out["target_month"] = next_time.dt.month.astype(int)
    out["target_dayofyear"] = next_time.dt.dayofyear.astype(int)
    out["target_weekofyear"] = next_time.dt.isocalendar().week.astype(int)
    out["target_is_weekend"] = (out["target_weekday"] >= 5).astype(int)
    out["target_is_commute_hour"] = out["target_hour"].isin([7, 8, 9, 17, 18, 19]).astype(int)
    out["target_is_night_hour"] = out["target_hour"].isin([22, 23, 0, 1, 2, 3, 4, 5]).astype(int)
    out["target_is_lunch_hour"] = out["target_hour"].isin([11, 12, 13]).astype(int)
    out = pd.concat(
        [
            out,
            cyclical_encode(out["target_hour"], 24, "target_hour"),
            cyclical_encode(out["target_weekday"], 7, "target_weekday"),
            cyclical_encode(out["target_month"], 12, "target_month"),
        ],
        axis=1,
    )
    return out


def create_tplus1_rows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["station_id", "time"]).reset_index(drop=True).copy()
    out = add_known_calendar_features(out)
    out["target_bike_change_t_plus_1"] = out.groupby("station_id")["bike_change"].shift(-1)
    out["observed_next_time"] = out.groupby("station_id")["time"].shift(-1)
    valid_gap = out["observed_next_time"].eq(out["time"] + pd.Timedelta(hours=1))
    out = out.loc[valid_gap].copy()
    out = out.drop(columns=["observed_next_time"])
    return out


def base_feature_candidates(df: pd.DataFrame) -> list[str]:
    candidates = [
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "is_rainy",
        "heavy_rain",
        "lat",
        "lon",
        "lcd_count",
        "qr_count",
        "dock_total",
        "is_qr_mixed",
        "feature_hour",
        "feature_weekday",
        "feature_month",
        "target_hour",
        "target_weekday",
        "target_month",
        "target_dayofyear",
        "target_weekofyear",
        "target_is_weekend",
        "target_is_commute_hour",
        "target_is_night_hour",
        "target_is_lunch_hour",
        "target_hour_sin",
        "target_hour_cos",
        "target_weekday_sin",
        "target_weekday_cos",
        "target_month_sin",
        "target_month_cos",
        "cluster",
        "mapped_dong_code",
        "total_return_count",
        "return_7_10_count",
        "return_11_14_count",
        "return_17_20_count",
        "dominant_ratio",
        "life_pop_7_10_mean",
        "life_pop_11_14_mean",
        "life_pop_17_20_mean",
        "arrival_7_10_ratio",
        "arrival_11_14_ratio",
        "arrival_17_20_ratio",
        "morning_net_inflow",
        "evening_net_inflow",
        "subway_distance_m",
        "bus_stop_count_300m",
    ]
    return [col for col in candidates if col in df.columns]


def prune_correlated_features(df: pd.DataFrame, columns: list[str], threshold: float = 0.90) -> tuple[list[str], list[dict[str, float | str]]]:
    numeric = df[columns].apply(pd.to_numeric, errors="coerce")
    sample = numeric.sample(n=min(120_000, len(numeric)), random_state=RANDOM_STATE) if len(numeric) > 120_000 else numeric
    corr = sample.corr(numeric_only=True).abs().fillna(0.0)
    kept: list[str] = []
    dropped: list[dict[str, float | str]] = []
    for col in columns:
        match = None
        for kept_col in kept:
            if corr.loc[col, kept_col] >= threshold:
                match = kept_col
                break
        if match is None:
            kept.append(col)
        else:
            dropped.append(
                {
                    "dropped_feature": col,
                    "kept_feature": match,
                    "corr_abs": float(corr.loc[col, match]),
                }
            )
    return kept, dropped


def fill_missing(train_df: pd.DataFrame, valid_df: pd.DataFrame, test_df: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    medians = train_df[feature_cols].median(numeric_only=True)
    for frame in (train_df, valid_df, test_df):
        frame[feature_cols] = frame[feature_cols].apply(pd.to_numeric, errors="coerce")
        frame[feature_cols] = frame[feature_cols].fillna(medians)
    return train_df, valid_df, test_df


def main() -> None:
    cluster_df = load_cluster_features()
    prepared: dict[str, pd.DataFrame] = {}
    row_counts: dict[str, int] = {}

    for split_name, path in SOURCE_PATHS.items():
        df = pd.read_parquet(path)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
        df = df.merge(cluster_df, on="station_id", how="left")
        df["cluster"] = df["cluster"].fillna(-1).astype(int)
        df["mapped_dong_code"] = df["mapped_dong_code"].fillna(-1).astype(int)
        prepared[split_name] = create_tplus1_rows(df)
        row_counts[split_name] = len(prepared[split_name])

    train_df = prepared["train"]
    valid_df = prepared["valid"]
    test_df = prepared["test"]

    feature_cols = base_feature_candidates(train_df)
    feature_cols, corr_drops = prune_correlated_features(train_df, feature_cols, threshold=0.90)
    train_df, valid_df, test_df = fill_missing(train_df, valid_df, test_df, feature_cols)

    target_corr = (
        train_df[feature_cols + ["target_bike_change_t_plus_1"]]
        .corr(numeric_only=True)["target_bike_change_t_plus_1"]
        .drop("target_bike_change_t_plus_1")
        .sort_values(key=lambda s: s.abs(), ascending=False)
        .rename("pearson_corr_with_target")
        .reset_index()
        .rename(columns={"index": "feature"})
    )

    keep_output_cols = ["station_id", "time", "target_time", "target_bike_change_t_plus_1"] + feature_cols
    for split_name, df in [("train", train_df), ("valid", valid_df), ("test", test_df)]:
        out = df[keep_output_cols].copy()
        out.to_parquet(OUTPUT_PATHS[split_name], index=False)

    pd.DataFrame({"feature": feature_cols}).to_csv(FINAL_FEATURE_PATH, index=False, encoding="utf-8-sig")
    pd.DataFrame(corr_drops).to_csv(CORR_DROP_PATH, index=False, encoding="utf-8-sig")
    target_corr.to_csv(CORR_TARGET_PATH, index=False, encoding="utf-8-sig")

    meta = {
        "task_definition": "use information available at time t to predict bike_change at time t+1 hour",
        "source_paths": {k: str(v) for k, v in SOURCE_PATHS.items()},
        "output_paths": {k: str(v) for k, v in OUTPUT_PATHS.items()},
        "row_counts": row_counts,
        "feature_count": len(feature_cols),
        "corr_threshold": 0.90,
        "excluded_feature_principles": [
            "exclude target-hour observed values",
            "exclude bike_change direct transforms",
            "exclude hourly lag/rolling time-series features",
            "exclude hourly seasonal expectation features built from target variable",
        ],
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
