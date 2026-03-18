from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"

TRAIN_PATH = DATA_DIR / "station_hour_bike_change_deseason_reduced_train_2023.csv.gz"
VALID_PATH = DATA_DIR / "station_hour_bike_change_deseason_reduced_valid_2024.csv.gz"
TEST_PATH = DATA_DIR / "station_hour_bike_change_deseason_reduced_test_2025.csv.gz"


def resolve_split_path(path: Path) -> Path:
    parquet = path.with_suffix("").with_suffix(".parquet")
    if parquet.exists():
        return parquet
    return path


def load_split(path: Path) -> pd.DataFrame:
    resolved = resolve_split_path(path)
    if resolved.suffix == ".parquet":
        df = pd.read_parquet(resolved)
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
    else:
        df = pd.read_csv(resolved, parse_dates=["time"])
    df = df.sort_values(["station_id", "time"]).reset_index(drop=True)
    return df


def month_profile_matrix(train_df: pd.DataFrame) -> pd.DataFrame:
    profile = (
        train_df.groupby(["month", "weekday", "hour"])["bike_change"]
        .mean()
        .unstack(["weekday", "hour"])
        .fillna(0.0)
        .sort_index()
    )
    return profile


def build_month_similarity_map(train_df: pd.DataFrame, corr_threshold: float = 0.78) -> pd.DataFrame:
    profile = month_profile_matrix(train_df)
    month_mean_abs = train_df.groupby("month")["bike_change"].apply(lambda s: float(np.mean(np.abs(s))) + 1e-6)
    corr = profile.T.corr().fillna(0.0)

    remaining = list(profile.index)
    groups: list[dict[str, float | int]] = []
    group_id = 1

    while remaining:
        rep = remaining[0]
        current = [month for month in remaining if corr.loc[rep, month] >= corr_threshold]
        current = sorted(current)
        for month in current:
            scale = float(month_mean_abs.loc[month] / month_mean_abs.loc[rep])
            groups.append(
                {
                    "month": int(month),
                    "month_pattern_group": int(group_id),
                    "representative_month": int(rep),
                    "month_pattern_corr": float(corr.loc[rep, month]),
                    "month_scale_weight": scale,
                    "is_representative_month": int(month == rep),
                }
            )
        remaining = [month for month in remaining if month not in current]
        group_id += 1

    mapping = pd.DataFrame(groups).sort_values("month").reset_index(drop=True)
    return mapping


def apply_month_similarity_map(df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    out = df.merge(mapping, on="month", how="left")
    out["month_pattern_group"] = out["month_pattern_group"].fillna(out["month"]).astype(int)
    out["representative_month"] = out["representative_month"].fillna(out["month"]).astype(int)
    out["month_pattern_corr"] = out["month_pattern_corr"].fillna(1.0).astype(float)
    out["month_scale_weight"] = out["month_scale_weight"].fillna(1.0).astype(float)
    out["is_representative_month"] = out["is_representative_month"].fillna(1).astype(int)
    return out


def choose_columns_by_correlation(
    train_df: pd.DataFrame,
    candidate_cols: list[str],
    threshold: float = 0.92,
) -> tuple[list[str], list[str], list[dict[str, float | str]]]:
    corr = train_df[candidate_cols].corr().abs().fillna(0.0)
    priority = [
        "bike_change_deseasonalized",
        "bike_change_seasonal_expected",
        "seasonality_strength",
        "bike_change_resid_lag_1",
        "bike_change_resid_lag_24",
        "bike_change_resid_lag_168",
        "bike_change_resid_rollmean_24",
        "bike_change_resid_rollstd_24",
        "bike_change_resid_rollmean_168",
        "bike_change_resid_rollstd_168",
        "bike_change_resid_trend_1_24",
        "bike_change_resid_trend_24_168",
        "station_activity_total",
        "rental_count_deseasonalized",
        "return_count_deseasonalized",
        "month_pattern_group",
        "month_scale_weight",
        "hour",
        "weekday",
        "is_weekend_or_holiday",
        "is_commute_hour",
        "is_night_hour",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "is_rainy",
        "heavy_rain",
        "dock_total",
        "qr_ratio",
        "lat",
        "lon",
    ]
    rank = {col: idx for idx, col in enumerate(priority)}
    ordered = sorted(candidate_cols, key=lambda col: rank.get(col, len(priority)))

    keep: list[str] = []
    dropped: list[str] = []
    dropped_pairs: list[dict[str, float | str]] = []

    for col in ordered:
        matched = None
        for kept in keep:
            if corr.loc[col, kept] >= threshold:
                matched = kept
                break
        if matched is None:
            keep.append(col)
        else:
            dropped.append(col)
            dropped_pairs.append(
                {
                    "dropped_column": col,
                    "kept_column": matched,
                    "correlation": float(corr.loc[col, matched]),
                }
            )
    return keep, dropped, dropped_pairs


def build_compact_dataset(df: pd.DataFrame, keep_features: list[str]) -> pd.DataFrame:
    id_cols = ["station_id", "time", "bike_change"]
    cols = id_cols + [col for col in keep_features if col not in id_cols]
    return df[cols].copy()


def build_representative_train_dataset(df: pd.DataFrame, keep_features: list[str]) -> pd.DataFrame:
    sampled = df[df["is_representative_month"] == 1].copy()
    return build_compact_dataset(sampled, keep_features)


def save(df: pd.DataFrame, filename: str) -> Path:
    path = DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig", compression="gzip")
    return path


def main():
    train_df = load_split(TRAIN_PATH)
    valid_df = load_split(VALID_PATH)
    test_df = load_split(TEST_PATH)

    month_map = build_month_similarity_map(train_df, corr_threshold=0.78)
    train_df = apply_month_similarity_map(train_df, month_map)
    valid_df = apply_month_similarity_map(valid_df, month_map)
    test_df = apply_month_similarity_map(test_df, month_map)

    representative_train_df = train_df[train_df["is_representative_month"] == 1].copy()

    feature_candidates = [
        "station_activity_total",
        "bike_change_seasonal_expected",
        "bike_change_deseasonalized",
        "rental_count_deseasonalized",
        "return_count_deseasonalized",
        "bike_change_resid_lag_1",
        "bike_change_resid_lag_24",
        "bike_change_resid_lag_168",
        "bike_change_resid_rollmean_24",
        "bike_change_resid_rollstd_24",
        "bike_change_resid_rollmean_168",
        "bike_change_resid_rollstd_168",
        "bike_change_resid_trend_1_24",
        "bike_change_resid_trend_24_168",
        "weekday",
        "hour",
        "is_weekend_or_holiday",
        "is_commute_hour",
        "is_night_hour",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "is_rainy",
        "heavy_rain",
        "lat",
        "lon",
        "dock_total",
        "qr_ratio",
        "seasonality_strength",
        "month_pattern_group",
        "month_pattern_corr",
        "month_scale_weight",
        "is_representative_month",
    ]
    feature_candidates = [col for col in feature_candidates if col in train_df.columns]

    keep_features, dropped_features, dropped_pairs = choose_columns_by_correlation(
        representative_train_df,
        feature_candidates,
        threshold=0.92,
    )

    compact_train = build_compact_dataset(train_df, keep_features)
    compact_valid = build_compact_dataset(valid_df, keep_features)
    compact_test = build_compact_dataset(test_df, keep_features)
    sampled_train = build_representative_train_dataset(train_df, keep_features)

    train_path = save(compact_train, "station_hour_bike_change_deseason_compact_train_2023.csv.gz")
    valid_path = save(compact_valid, "station_hour_bike_change_deseason_compact_valid_2024.csv.gz")
    test_path = save(compact_test, "station_hour_bike_change_deseason_compact_test_2025.csv.gz")
    sampled_train_path = save(sampled_train, "station_hour_bike_change_deseason_compact_sampled_train_2023.csv.gz")
    month_map_path = DATA_DIR / "station_hour_bike_change_month_pattern_map.csv"
    dropped_path = DATA_DIR / "station_hour_bike_change_compact_dropped_correlations.csv"

    month_map.to_csv(month_map_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(dropped_pairs).to_csv(dropped_path, index=False, encoding="utf-8-sig")

    meta = {
        "target": "bike_change",
        "source": {
            "train": TRAIN_PATH.name,
            "valid": VALID_PATH.name,
            "test": TEST_PATH.name,
        },
        "outputs": {
            "compact_train": train_path.name,
            "compact_valid": valid_path.name,
            "compact_test": test_path.name,
            "compact_sampled_train": sampled_train_path.name,
            "month_pattern_map": month_map_path.name,
            "dropped_correlations": dropped_path.name,
        },
        "row_counts": {
            "train": int(len(compact_train)),
            "valid": int(len(compact_valid)),
            "test": int(len(compact_test)),
            "sampled_train": int(len(sampled_train)),
        },
        "column_counts": {
            "before": int(len(train_df.columns)),
            "after": int(len(compact_train.columns)),
            "feature_after": int(len(compact_train.columns) - 3),
        },
        "month_pattern_strategy": {
            "correlation_threshold": 0.78,
            "group_count": int(month_map["month_pattern_group"].nunique()),
            "representative_months": month_map.loc[month_map["is_representative_month"] == 1, "month"].astype(int).tolist(),
        },
        "correlation_pruning": {
            "threshold": 0.92,
            "kept_features": keep_features,
            "dropped_features": dropped_features,
        },
    }
    meta_path = DATA_DIR / "station_hour_bike_change_compact_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
