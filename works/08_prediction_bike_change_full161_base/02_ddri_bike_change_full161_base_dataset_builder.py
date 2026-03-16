from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/cheng80/Desktop/ddri_work")
WORK_DIR = ROOT / "works" / "08_prediction_bike_change_full161_base"
OUTPUT_ROOT = ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "bike_change_full161_base_outputs"
OUTPUT_DATA_DIR = OUTPUT_ROOT / "data"
OUTPUT_REPORT_DIR = OUTPUT_ROOT / "reports"

SOURCE_DIR = ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "full_data"
TRAIN_SOURCE = SOURCE_DIR / "ddri_prediction_long_train_2023_2024.csv"
TEST_SOURCE = SOURCE_DIR / "ddri_prediction_long_test_2025.csv"

TRAIN_OUT = OUTPUT_DATA_DIR / "ddri_prediction_bike_change_full161_base_train_2023_2024.csv"
TEST_OUT = OUTPUT_DATA_DIR / "ddri_prediction_bike_change_full161_base_test_2025.csv"
FEATURE_SUMMARY_OUT = OUTPUT_DATA_DIR / "ddri_prediction_bike_change_full161_base_feature_summary.csv"
META_OUT = OUTPUT_REPORT_DIR / "ddri_prediction_bike_change_full161_base_feature_meta.json"

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
]


def log(message: str) -> None:
    print(message, flush=True)


def validate_columns(df: pd.DataFrame, path: Path) -> None:
    required = {"station_id", "date", "hour", "rental_count"} | set(BASE_FEATURES)
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{path.name}에 필수 컬럼이 없습니다: {missing}")


def validate_duplicates(df: pd.DataFrame, path: Path) -> None:
    dup_count = int(df.duplicated(subset=["station_id", "date", "hour"]).sum())
    if dup_count > 0:
        raise ValueError(f"{path.name}에 station_id+date+hour 중복 {dup_count}건이 있습니다.")


def add_targets(df: pd.DataFrame, seasonal_map: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    result = df.copy()
    result["date"] = pd.to_datetime(result["date"])
    result = result.sort_values(["station_id", "date", "hour"]).reset_index(drop=True)
    grouped = result.groupby("station_id", sort=False)["rental_count"]

    result["bike_change_raw"] = grouped.diff().astype("float32")

    if seasonal_map is None:
        seasonal_map = (
            result.dropna(subset=["bike_change_raw"])
            .groupby(["station_id", "weekday", "hour"], as_index=False)["bike_change_raw"]
            .mean()
            .rename(columns={"bike_change_raw": "seasonal_mean_train_2023"})
        )

    result = result.merge(seasonal_map, on=["station_id", "weekday", "hour"], how="left")
    result["bike_change_deseasonalized"] = (
        result["bike_change_raw"] - result["seasonal_mean_train_2023"]
    ).astype("float32")
    result = result.dropna(subset=["bike_change_raw"]).reset_index(drop=True)
    return result, seasonal_map


def build_feature_summary(train_df: pd.DataFrame, test_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in BASE_FEATURES:
        rows.append(
            {
                "feature": col,
                "in_train": True,
                "in_test": True,
                "dtype_train": str(train_df[col].dtype),
                "dtype_test": str(test_df[col].dtype),
            }
        )
    rows.extend(
        [
            {
                "feature": "bike_change_raw",
                "in_train": True,
                "in_test": True,
                "dtype_train": str(train_df["bike_change_raw"].dtype),
                "dtype_test": str(test_df["bike_change_raw"].dtype),
            },
            {
                "feature": "seasonal_mean_train_2023",
                "in_train": True,
                "in_test": True,
                "dtype_train": str(train_df["seasonal_mean_train_2023"].dtype),
                "dtype_test": str(test_df["seasonal_mean_train_2023"].dtype),
            },
            {
                "feature": "bike_change_deseasonalized",
                "in_train": True,
                "in_test": True,
                "dtype_train": str(train_df["bike_change_deseasonalized"].dtype),
                "dtype_test": str(test_df["bike_change_deseasonalized"].dtype),
            },
        ]
    )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    log("[1/4] 정본 데이터 로드")
    train_source_df = pd.read_csv(TRAIN_SOURCE)
    test_source_df = pd.read_csv(TEST_SOURCE)
    validate_columns(train_source_df, TRAIN_SOURCE)
    validate_columns(test_source_df, TEST_SOURCE)
    validate_duplicates(train_source_df, TRAIN_SOURCE)
    validate_duplicates(test_source_df, TEST_SOURCE)
    log(f"  train rows={len(train_source_df):,}, test rows={len(test_source_df):,}")
    log(
        "  "
        + f"train unique stations={train_source_df['station_id'].nunique()}, "
        + f"test unique stations={test_source_df['station_id'].nunique()}"
    )

    log("[2/4] Train 2023 기준 seasonal mean 생성")
    train_source_df["date"] = pd.to_datetime(train_source_df["date"])
    train_2023_source = train_source_df[train_source_df["date"] < pd.Timestamp("2024-01-01")].copy()
    train_2023_with_target, seasonal_map = add_targets(train_2023_source)
    log(f"  train_2023 rows(after target)={len(train_2023_with_target):,}")
    log(f"  seasonal groups={len(seasonal_map):,}")

    log("[3/4] full train/test 정제 데이터 생성")
    train_df, _ = add_targets(train_source_df, seasonal_map)
    test_df, _ = add_targets(test_source_df, seasonal_map)

    keep_cols = ["date", "rental_count"] + BASE_FEATURES + [
        "bike_change_raw",
        "seasonal_mean_train_2023",
        "bike_change_deseasonalized",
    ]
    train_df = train_df[keep_cols].copy()
    test_df = test_df[keep_cols].copy()

    train_df.to_csv(TRAIN_OUT, index=False, encoding="utf-8-sig")
    test_df.to_csv(TEST_OUT, index=False, encoding="utf-8-sig")
    feature_summary = build_feature_summary(train_df, test_df)
    feature_summary.to_csv(FEATURE_SUMMARY_OUT, index=False, encoding="utf-8-sig")
    log(f"  saved: {TRAIN_OUT}")
    log(f"  saved: {TEST_OUT}")
    log(f"  saved: {FEATURE_SUMMARY_OUT}")

    meta = {
        "train_source": str(TRAIN_SOURCE),
        "test_source": str(TEST_SOURCE),
        "train_output": str(TRAIN_OUT),
        "test_output": str(TEST_OUT),
        "feature_summary_output": str(FEATURE_SUMMARY_OUT),
        "base_features": BASE_FEATURES,
        "target_columns": [
            "bike_change_raw",
            "seasonal_mean_train_2023",
            "bike_change_deseasonalized",
        ],
        "train_rows_after_target": int(len(train_df)),
        "test_rows_after_target": int(len(test_df)),
        "train_unique_stations": int(train_df["station_id"].nunique()),
        "test_unique_stations": int(test_df["station_id"].nunique()),
        "seasonal_groups_from_train_2023": int(len(seasonal_map)),
        "policy": {
            "train": "2023",
            "validation": "2024",
            "test": "2025",
            "refit": "validation 우세 모델 선택 후 2023+2024 재학습 -> 2025 평가",
        },
    }
    META_OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"[4/4] 완료: {META_OUT}")


if __name__ == "__main__":
    main()
