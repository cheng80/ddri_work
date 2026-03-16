from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


ROOT = Path("/Users/cheng80/Desktop/ddri_work")
WORK_DIR = ROOT / "works/07_prediction_bike_change"
OUTPUT_DIR = WORK_DIR / "output/data"

TRAIN_PATH = OUTPUT_DIR / "ddri_prediction_bike_change_train_2023_2024.csv"
TEST_PATH = OUTPUT_DIR / "ddri_prediction_bike_change_test_2025.csv"

RAW_TRAIN_PATH = (
    ROOT
    / "3조 공유폴더/대표대여소_예측데이터_15개/second_round_data/ddri_prediction_long_train_2023_2024_second_round_feature_collection.csv"
)
RAW_TEST_PATH = (
    ROOT
    / "3조 공유폴더/대표대여소_예측데이터_15개/second_round_data/ddri_prediction_long_test_2025_second_round_feature_collection.csv"
)

METRICS_OUT = OUTPUT_DIR / "ddri_bike_change_rep15_augmented_feature_metrics.csv"
FEATURESET_OUT = OUTPUT_DIR / "ddri_bike_change_rep15_augmented_feature_sets.csv"

RANDOM_STATE = 42

BASE_FEATURES = [
    "station_id",
    "cluster",
    "mapped_dong_code",
    "hour",
    "weekday",
    "month",
    "holiday",
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "rolling_mean_24h",
    "rolling_std_24h",
    "rolling_mean_168h",
    "rolling_std_168h",
    "rolling_mean_6h",
    "is_weekend",
    "is_night_hour",
    "is_commute_hour",
    "hour_sin",
    "is_rainy",
    "hour_cos",
    "commute_morning_flag",
    "commute_evening_flag",
    "subway_distance_m",
    "distance_naturepark_m",
    "restaurant_count_300m",
    "convenience_store_count_300m",
    "bus_stop_count_300m",
    "cafe_count_300m",
    "elevation_diff_nearest_subway_m",
    "nearest_park_area_sqm",
]

BASE_CATEGORICAL = [
    "station_id",
    "cluster",
    "mapped_dong_code",
    "hour",
    "weekday",
    "month",
    "holiday",
]

RAW_EXTRA_COLUMNS = [
    "heavy_rain_flag",
    "is_lunch_hour",
    "is_holiday_eve",
    "is_after_holiday",
]

MERGE_KEYS = ["station_id", "date", "hour"]


def add_augmented_features(
    base_df: pd.DataFrame,
    raw_df: pd.DataFrame,
) -> pd.DataFrame:
    df = base_df.copy()
    raw_cols = [c for c in RAW_EXTRA_COLUMNS if c in raw_df.columns]
    extra_df = raw_df[MERGE_KEYS + raw_cols].copy()
    df = df.merge(extra_df, on=MERGE_KEYS, how="left")

    df = df.sort_values(["station_id", "date", "hour"]).reset_index(drop=True)
    grouped_change = df.groupby("station_id")["bike_change"]
    shifted_change = grouped_change.shift(1)

    df["bike_change_lag_1"] = grouped_change.shift(1).astype("float32")
    df["bike_change_lag_24"] = grouped_change.shift(24).astype("float32")
    df["bike_change_lag_168"] = grouped_change.shift(168).astype("float32")
    df["bike_change_rollmean_3"] = (
        shifted_change.rolling(3).mean().reset_index(level=0, drop=True).astype("float32")
    )
    df["bike_change_rollmean_24"] = (
        shifted_change.rolling(24).mean().reset_index(level=0, drop=True).astype("float32")
    )
    df["bike_change_rollstd_24"] = (
        shifted_change.rolling(24).std().reset_index(level=0, drop=True).astype("float32")
    )
    df["bike_change_rollstd_168"] = (
        shifted_change.rolling(168).std().reset_index(level=0, drop=True).astype("float32")
    )

    df["temp_x_commute"] = (df["temperature"] * df["is_commute_hour"]).astype("float32")
    df["rain_x_commute"] = (df["is_rainy"] * df["is_commute_hour"]).astype("float32")
    df["rain_x_night"] = (df["is_rainy"] * df["is_night_hour"]).astype("float32")

    for cluster_value in range(5):
        df[f"cluster_{cluster_value}"] = (df["cluster"] == cluster_value).astype("int8")

    if "heavy_rain_flag" in df.columns:
        df["heavy_rain_flag"] = df["heavy_rain_flag"].fillna(0).astype("int8")
    if "is_lunch_hour" in df.columns:
        df["is_lunch_hour"] = df["is_lunch_hour"].fillna(0).astype("int8")
    if "is_holiday_eve" in df.columns:
        df["is_holiday_eve"] = df["is_holiday_eve"].fillna(0).astype("int8")
    if "is_after_holiday" in df.columns:
        df["is_after_holiday"] = df["is_after_holiday"].fillna(0).astype("int8")

    return df


def build_feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    optional = [c for c in RAW_EXTRA_COLUMNS if c in df.columns]

    feature_sets: dict[str, list[str]] = {
        "base_full_36": BASE_FEATURES,
        "base_plus_cluster_onehot": [c for c in BASE_FEATURES if c != "cluster"]
        + [f"cluster_{i}" for i in range(5)],
        "base_plus_weather_interaction": BASE_FEATURES
        + ["temp_x_commute", "rain_x_commute", "rain_x_night"],
        "base_plus_bike_change_signal": BASE_FEATURES
        + [
            "bike_change_lag_1",
            "bike_change_lag_24",
            "bike_change_lag_168",
            "bike_change_rollmean_3",
            "bike_change_rollmean_24",
            "bike_change_rollstd_24",
            "bike_change_rollstd_168",
        ],
        "base_plus_context_extras": BASE_FEATURES + optional,
        "all_augmented": [c for c in BASE_FEATURES if c != "cluster"]
        + [f"cluster_{i}" for i in range(5)]
        + ["temp_x_commute", "rain_x_commute", "rain_x_night"]
        + [
            "bike_change_lag_1",
            "bike_change_lag_24",
            "bike_change_lag_168",
            "bike_change_rollmean_3",
            "bike_change_rollmean_24",
            "bike_change_rollstd_24",
            "bike_change_rollstd_168",
        ]
        + optional,
    }

    return feature_sets


def evaluate_predictions(model_name: str, split_name: str, y_true: pd.Series, y_pred) -> dict:
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    sign_accuracy = ((pd.Series(y_pred) >= 0) == (y_true.reset_index(drop=True) >= 0)).mean()
    return {
        "model": model_name,
        "split": split_name,
        "rmse": round(float(rmse), 4),
        "mae": round(float(mae), 4),
        "r2": round(float(r2), 4),
        "sign_accuracy": round(float(sign_accuracy), 4),
    }


def prepare_xy(df: pd.DataFrame, feature_cols: list[str]):
    subset = df[feature_cols + ["bike_change"]].dropna().reset_index(drop=True)
    X = subset[feature_cols].copy()
    categorical_cols = [c for c in feature_cols if c in BASE_CATEGORICAL]
    for col in categorical_cols:
        X[col] = X[col].astype("category")
    y = subset["bike_change"].copy()
    return X, y, categorical_cols, len(subset)


def build_model() -> LGBMRegressor:
    return LGBMRegressor(
        objective="regression",
        learning_rate=0.05,
        n_estimators=400,
        num_leaves=31,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=RANDOM_STATE,
        verbose=-1,
        n_jobs=1,
    )


def run_variant(
    name: str,
    feature_cols: list[str],
    train_2023: pd.DataFrame,
    valid_2024: pd.DataFrame,
    full_train: pd.DataFrame,
    test_2025: pd.DataFrame,
) -> list[dict]:
    X_train, y_train, train_cat, train_rows = prepare_xy(train_2023, feature_cols)
    X_valid, y_valid, _, valid_rows = prepare_xy(valid_2024, feature_cols)
    X_full, y_full, full_cat, full_rows = prepare_xy(full_train, feature_cols)
    X_test, y_test, _, test_rows = prepare_xy(test_2025, feature_cols)

    results = []

    model = build_model()
    model.fit(X_train, y_train, categorical_feature=train_cat)
    train_result = evaluate_predictions(name, "train_2023", y_train, model.predict(X_train))
    train_result["rows"] = train_rows
    train_result["train_rows"] = train_rows
    results.append(train_result)
    validation_result = evaluate_predictions(name, "validation_2024", y_valid, model.predict(X_valid))
    validation_result["rows"] = valid_rows
    validation_result["train_rows"] = train_rows
    results.append(validation_result)

    model = build_model()
    model.fit(X_full, y_full, categorical_feature=full_cat)
    train_refit_result = evaluate_predictions(name, "train_full_refit", y_full, model.predict(X_full))
    train_refit_result["rows"] = full_rows
    train_refit_result["train_rows"] = full_rows
    results.append(train_refit_result)
    test_result = evaluate_predictions(name, "test_2025_refit", y_test, model.predict(X_test))
    test_result["rows"] = test_rows
    test_result["train_rows"] = full_rows
    results.append(test_result)
    return results


def main() -> None:
    train_base = pd.read_csv(TRAIN_PATH)
    test_base = pd.read_csv(TEST_PATH)
    raw_train = pd.read_csv(RAW_TRAIN_PATH)
    raw_test = pd.read_csv(RAW_TEST_PATH)

    train_aug = add_augmented_features(train_base, raw_train)
    test_aug = add_augmented_features(test_base, raw_test)

    train_2023 = train_aug.loc[train_aug["date"] < "2024-01-01"].copy()
    valid_2024 = train_aug.loc[train_aug["date"] >= "2024-01-01"].copy()
    full_train = train_aug.copy()
    test_2025 = test_aug.copy()

    feature_sets = build_feature_sets(train_aug)
    feature_summary = pd.DataFrame(
        {
            "model": list(feature_sets.keys()),
            "feature_count": [len(cols) for cols in feature_sets.values()],
            "feature_list": [" | ".join(cols) for cols in feature_sets.values()],
        }
    )
    feature_summary.to_csv(FEATURESET_OUT, index=False, encoding="utf-8-sig")

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=min(4, len(feature_sets))) as executor:
        future_map = {
            executor.submit(
                run_variant, name, cols, train_2023, valid_2024, full_train, test_2025
            ): name
            for name, cols in feature_sets.items()
        }
        for future in as_completed(future_map):
            results.extend(future.result())

    results_df = pd.DataFrame(results).sort_values(["split", "rmse", "model"]).reset_index(
        drop=True
    )
    results_df.to_csv(METRICS_OUT, index=False, encoding="utf-8-sig")

    print(f"saved: {METRICS_OUT}")
    print(f"saved: {FEATURESET_OUT}")
    print(results_df.to_string(index=False))


if __name__ == "__main__":
    main()
