from __future__ import annotations

import gc
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
OUTPUT_DIR = DATA_DIR
RANDOM_STATE = 42


KOR_HOLIDAYS = {
    "2023-01-01",
    "2023-01-21",
    "2023-01-22",
    "2023-01-23",
    "2023-01-24",
    "2023-03-01",
    "2023-05-05",
    "2023-05-27",
    "2023-05-29",
    "2023-06-06",
    "2023-08-15",
    "2023-09-28",
    "2023-09-29",
    "2023-09-30",
    "2023-10-03",
    "2023-10-09",
    "2023-12-25",
    "2024-01-01",
    "2024-02-09",
    "2024-02-10",
    "2024-02-11",
    "2024-02-12",
    "2024-03-01",
    "2024-04-10",
    "2024-05-05",
    "2024-05-06",
    "2024-05-15",
    "2024-06-06",
    "2024-08-15",
    "2024-09-16",
    "2024-09-17",
    "2024-09-18",
    "2024-10-03",
    "2024-10-09",
    "2024-12-25",
    "2025-01-01",
    "2025-01-28",
    "2025-01-29",
    "2025-01-30",
    "2025-03-01",
    "2025-03-03",
    "2025-05-05",
    "2025-05-06",
    "2025-06-03",
    "2025-06-06",
    "2025-08-15",
    "2025-10-03",
    "2025-10-05",
    "2025-10-06",
    "2025-10-07",
    "2025-10-08",
    "2025-10-09",
    "2025-12-25",
}


@dataclass
class ModelSpec:
    name: str
    kind: str
    builder: Callable[[], object] | None = None
    train_sample: int | None = None
    notes: str = ""


def load_flow() -> pd.DataFrame:
    path = DATA_DIR / "station_hour_bike_flow_2023_2025.csv"
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


def load_weather() -> pd.DataFrame:
    parts = []
    for path in sorted(DATA_DIR.glob("gangnam_weather_1year_*.csv")):
        weather = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["datetime"])
        parts.append(weather)

    weather = pd.concat(parts, ignore_index=True).sort_values("datetime")
    time_range = pd.date_range(weather["datetime"].min(), weather["datetime"].max(), freq="h")
    weather = weather.drop_duplicates("datetime").set_index("datetime").reindex(time_range)
    weather.index.name = "time"
    weather = weather.interpolate(limit_direction="both")
    weather = weather.reset_index()

    for col in ["temperature", "humidity", "precipitation", "wind_speed"]:
        weather[col] = pd.to_numeric(weather[col], errors="coerce", downcast="float")
    return weather


def load_station_meta() -> pd.DataFrame:
    parts = []
    for path in sorted(DATA_DIR.glob("20*.csv")):
        if path.stat().st_size > 100_000:
            continue
        meta = pd.read_csv(path, encoding="utf-8-sig")
        if len(meta.columns) < 5:
            continue
        if "대여소번호" not in meta.columns[0]:
            continue

        year = int(path.name[:4])
        meta = meta.rename(
            columns={
                "대여소번호": "station_id",
                "대여소명": "station_name",
                "위도": "lat",
                "경도": "lon",
                "LCD": "lcd_count",
                "QR": "qr_count",
            }
        )
        meta["station_id"] = pd.to_numeric(meta["station_id"], errors="coerce").astype("Int64")
        meta = meta.dropna(subset=["station_id"]).copy()
        meta["station_id"] = meta["station_id"].astype("int32")
        meta["source_year"] = year
        parts.append(meta)

    station_meta = pd.concat(parts, ignore_index=True).sort_values(["station_id", "source_year"])
    station_meta = station_meta.drop_duplicates("station_id", keep="last")
    station_meta["dock_total"] = (
        pd.to_numeric(station_meta["lcd_count"], errors="coerce").fillna(0)
        + pd.to_numeric(station_meta["qr_count"], errors="coerce").fillna(0)
    )
    station_meta["is_qr_mixed"] = (pd.to_numeric(station_meta["qr_count"], errors="coerce").fillna(0) > 0).astype(
        "int8"
    )
    keep_cols = [
        "station_id",
        "lat",
        "lon",
        "lcd_count",
        "qr_count",
        "dock_total",
        "is_qr_mixed",
    ]
    return station_meta[keep_cols].copy()


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    holiday_dates = pd.to_datetime(sorted(KOR_HOLIDAYS))
    holiday_set = set(holiday_dates.date)
    holiday_eve_set = set((holiday_dates - pd.Timedelta(days=1)).date)

    df["date"] = df["time"].dt.date
    df["dayofyear"] = df["time"].dt.dayofyear.astype("int16")
    df["weekofyear"] = df["time"].dt.isocalendar().week.astype("int16")
    df["is_weekend"] = (df["weekday"] >= 5).astype("int8")
    df["is_holiday"] = df["date"].isin(holiday_set).astype("int8")
    df["is_holiday_eve"] = df["date"].isin(holiday_eve_set).astype("int8")
    df["is_weekend_or_holiday"] = ((df["is_weekend"] == 1) | (df["is_holiday"] == 1)).astype("int8")
    df["is_commute_hour"] = df["hour"].isin([7, 8, 9, 17, 18, 19]).astype("int8")
    df["is_night_hour"] = df["hour"].isin([0, 1, 2, 3, 4, 5]).astype("int8")
    df["is_lunch_hour"] = df["hour"].isin([11, 12, 13]).astype("int8")
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24).astype("float32")
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24).astype("float32")
    df["weekday_sin"] = np.sin(2 * np.pi * df["weekday"] / 7).astype("float32")
    df["weekday_cos"] = np.cos(2 * np.pi * df["weekday"] / 7).astype("float32")
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12).astype("float32")
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12).astype("float32")
    return df


def add_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    df["is_rainy"] = (df["precipitation"] > 0).astype("int8")
    df["heavy_rain"] = (df["precipitation"] >= 3).astype("int8")
    df["temp_x_commute"] = (df["temperature"] * df["is_commute_hour"]).astype("float32")
    df["rain_x_commute"] = (df["precipitation"] * df["is_commute_hour"]).astype("float32")
    df["rain_x_night"] = (df["precipitation"] * df["is_night_hour"]).astype("float32")
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    group = df.groupby("station_id", sort=False)

    for col in ["bike_change", "bike_count_index", "rental_count", "return_count"]:
        for lag in [1, 2, 24, 168]:
            df[f"{col}_lag_{lag}"] = group[col].shift(lag).astype("float32")

    shifted_change = group["bike_change"].shift(1)
    shifted_index = group["bike_count_index"].shift(1)

    for window in [3, 24, 168]:
        df[f"bike_change_rollmean_{window}"] = (
            shifted_change.groupby(df["station_id"]).rolling(window).mean().reset_index(level=0, drop=True).astype("float32")
        )
        df[f"bike_change_rollstd_{window}"] = (
            shifted_change.groupby(df["station_id"]).rolling(window).std().reset_index(level=0, drop=True).fillna(0).astype("float32")
        )
        df[f"bike_index_rollmean_{window}"] = (
            shifted_index.groupby(df["station_id"]).rolling(window).mean().reset_index(level=0, drop=True).astype("float32")
        )

    return df


def build_dataset() -> pd.DataFrame:
    flow = load_flow()
    weather = load_weather()
    station_meta = load_station_meta()

    df = flow.merge(weather, left_on="time", right_on="time", how="left")
    df = df.merge(station_meta, on="station_id", how="left")
    df = add_calendar_features(df)
    df = add_weather_features(df)
    df = add_lag_features(df)

    numeric_fill_zero = ["lat", "lon", "lcd_count", "qr_count", "dock_total", "is_qr_mixed"]
    for col in numeric_fill_zero:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.drop(columns=["date"])
    df = df.dropna().reset_index(drop=True)
    return df


def sample_train(X: pd.DataFrame, y: pd.Series, sample_size: int | None, seed: int = RANDOM_STATE):
    if sample_size is None or len(X) <= sample_size:
        return X, y
    sample_idx = X.sample(n=sample_size, random_state=seed).index
    return X.loc[sample_idx], y.loc[sample_idx]


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    rmse = float(root_mean_squared_error(y_true, y_pred))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    std = float(np.std(y_true))
    return {
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "nrmse_std": rmse / std if std else np.nan,
        "nmae_std": mae / std if std else np.nan,
    }


def model_specs() -> list[ModelSpec]:
    return [
        ModelSpec(
            name="dummy_mean",
            kind="sklearn",
            builder=lambda: DummyRegressor(strategy="mean"),
            notes="전체 평균 예측",
        ),
        ModelSpec(
            name="ridge",
            kind="sklearn",
            builder=lambda: Ridge(alpha=2.0, random_state=RANDOM_STATE),
            train_sample=400_000,
            notes="선형 회귀 계열",
        ),
        ModelSpec(
            name="random_forest",
            kind="sklearn",
            builder=lambda: RandomForestRegressor(
                n_estimators=120,
                max_depth=16,
                min_samples_leaf=5,
                n_jobs=1,
                random_state=RANDOM_STATE,
            ),
            train_sample=80_000,
            notes="비선형 앙상블, 표본 학습",
        ),
        ModelSpec(
            name="extra_trees",
            kind="sklearn",
            builder=lambda: ExtraTreesRegressor(
                n_estimators=150,
                max_depth=24,
                min_samples_leaf=3,
                n_jobs=1,
                random_state=RANDOM_STATE,
            ),
            train_sample=80_000,
            notes="랜덤 분할 앙상블, 표본 학습",
        ),
        ModelSpec(
            name="hist_gbm",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_depth=10,
                max_iter=140,
                min_samples_leaf=80,
                l2_regularization=0.1,
                random_state=RANDOM_STATE,
            ),
            train_sample=450_000,
            notes="히스토그램 기반 부스팅",
        ),
        ModelSpec(
            name="hist_gbm_tuned",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_depth=12,
                max_iter=180,
                min_samples_leaf=60,
                l2_regularization=0.05,
                random_state=RANDOM_STATE,
            ),
            train_sample=600_000,
            notes="부스팅 튜닝 버전",
        ),
    ]


def baseline_predictions(df: pd.DataFrame, target: str) -> dict[str, np.ndarray]:
    if target == "bike_change":
        return {
            "baseline_lag1": df["bike_change_lag_1"].to_numpy(),
            "baseline_lag24": df["bike_change_lag_24"].to_numpy(),
            "baseline_lag168": df["bike_change_lag_168"].to_numpy(),
        }
    return {
        "baseline_lag1": df["bike_count_index_lag_1"].to_numpy(),
        "baseline_lag24": df["bike_count_index_lag_24"].to_numpy(),
        "baseline_lag168": df["bike_count_index_lag_168"].to_numpy(),
    }


def feature_sets() -> dict[str, list[str]]:
    base = [
        "station_id",
        "year",
        "month",
        "day",
        "weekday",
        "hour",
        "dayofyear",
        "weekofyear",
        "is_weekend",
        "is_holiday",
        "is_holiday_eve",
        "is_weekend_or_holiday",
        "is_commute_hour",
        "is_night_hour",
        "is_lunch_hour",
        "hour_sin",
        "hour_cos",
        "weekday_sin",
        "weekday_cos",
        "month_sin",
        "month_cos",
        "bike_change_lag_1",
        "bike_change_lag_2",
        "bike_change_lag_24",
        "bike_change_lag_168",
        "bike_count_index_lag_1",
        "bike_count_index_lag_2",
        "bike_count_index_lag_24",
        "bike_count_index_lag_168",
        "rental_count_lag_1",
        "rental_count_lag_24",
        "return_count_lag_1",
        "return_count_lag_24",
        "bike_change_rollmean_3",
        "bike_change_rollmean_24",
        "bike_change_rollmean_168",
        "bike_change_rollstd_24",
        "bike_change_rollstd_168",
        "bike_index_rollmean_3",
        "bike_index_rollmean_24",
        "bike_index_rollmean_168",
    ]
    enhanced = base + [
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "is_rainy",
        "heavy_rain",
        "temp_x_commute",
        "rain_x_commute",
        "rain_x_night",
        "lat",
        "lon",
        "lcd_count",
        "qr_count",
        "dock_total",
        "is_qr_mixed",
    ]
    return {"basic": base, "enhanced": enhanced}


def run_validation_rounds(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    feature_map = feature_sets()
    train_mask = df["year"] == 2023
    valid_mask = df["year"] == 2024
    records: list[dict[str, object]] = []
    chosen_feature_set: dict[str, str] = {}

    for target in ["bike_change", "bike_count_index"]:
        y_valid = df.loc[valid_mask, target]
        baseline_preds = baseline_predictions(df.loc[valid_mask], target)
        for baseline_name, pred in baseline_preds.items():
            metrics = evaluate_predictions(y_valid, pred)
            records.append(
                {
                    "round": "validation_feature_search",
                    "target": target,
                    "feature_set": "baseline",
                    "model": baseline_name,
                    **metrics,
                    "train_rows": int(train_mask.sum()),
                    "eval_rows": int(valid_mask.sum()),
                    "notes": "과거 값 그대로 예측",
                }
            )

        for feature_set_name, cols in feature_map.items():
            X_train = df.loc[train_mask, cols]
            y_train = df.loc[train_mask, target]
            X_valid = df.loc[valid_mask, cols]

            model = HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_depth=10,
                max_iter=120,
                min_samples_leaf=80,
                random_state=RANDOM_STATE,
            )
            sample_X, sample_y = sample_train(X_train, y_train, 300_000)
            model.fit(sample_X, sample_y)
            pred = model.predict(X_valid)
            metrics = evaluate_predictions(y_valid, pred)
            records.append(
                {
                    "round": "validation_feature_search",
                    "target": target,
                    "feature_set": feature_set_name,
                    "model": "hist_gbm_probe",
                    **metrics,
                    "train_rows": len(sample_X),
                    "eval_rows": int(valid_mask.sum()),
                    "notes": "feature set 비교용",
                }
            )

        subset = [r for r in records if r["round"] == "validation_feature_search" and r["target"] == target and r["model"] == "hist_gbm_probe"]
        chosen_feature_set[target] = min(subset, key=lambda r: r["rmse"])["feature_set"]

    return pd.DataFrame(records), chosen_feature_set


def run_model_benchmark(df: pd.DataFrame, chosen_feature_set: dict[str, str]) -> tuple[pd.DataFrame, dict[str, str]]:
    train_mask = df["year"].isin([2023, 2024])
    test_mask = df["year"] == 2025
    feature_map = feature_sets()
    records: list[dict[str, object]] = []
    best_ml_model: dict[str, str] = {}

    for target in ["bike_change", "bike_count_index"]:
        selected_feature_name = chosen_feature_set[target]
        cols = feature_map[selected_feature_name]
        X_train = df.loc[train_mask, cols]
        y_train = df.loc[train_mask, target]
        X_test = df.loc[test_mask, cols]
        y_test = df.loc[test_mask, target]

        baseline_preds = baseline_predictions(df.loc[test_mask], target)
        for baseline_name, pred in baseline_preds.items():
            metrics = evaluate_predictions(y_test, pred)
            records.append(
                {
                    "round": "test_benchmark",
                    "target": target,
                    "feature_set": "baseline",
                    "model": baseline_name,
                    **metrics,
                    "train_rows": int(train_mask.sum()),
                    "eval_rows": int(test_mask.sum()),
                    "notes": "과거 값 그대로 예측",
                }
            )

        for spec in model_specs():
            X_fit, y_fit = sample_train(X_train, y_train, spec.train_sample)
            model = spec.builder()
            model.fit(X_fit, y_fit)
            pred = model.predict(X_test)
            metrics = evaluate_predictions(y_test, pred)
            records.append(
                {
                    "round": "test_benchmark",
                    "target": target,
                    "feature_set": selected_feature_name,
                    "model": spec.name,
                    **metrics,
                    "train_rows": len(X_fit),
                    "eval_rows": int(test_mask.sum()),
                    "notes": spec.notes,
                }
            )
            gc.collect()

        ml_only = [r for r in records if r["round"] == "test_benchmark" and r["target"] == target and r["model"] not in {"baseline_lag1", "baseline_lag24", "baseline_lag168"}]
        best_ml_model[target] = min(ml_only, key=lambda r: r["rmse"])["model"]

    return pd.DataFrame(records), best_ml_model


def train_final_models(df: pd.DataFrame, chosen_feature_set: dict[str, str], best_ml_model: dict[str, str]):
    train_mask = df["year"].isin([2023, 2024])
    test_mask = df["year"] == 2025
    specs = {spec.name: spec for spec in model_specs()}
    feature_map = feature_sets()
    prediction_frames = []
    importance_frames = []
    metrics_records = []

    for target in ["bike_change", "bike_count_index"]:
        model_name = best_ml_model[target]
        cols = feature_map[chosen_feature_set[target]]
        spec = specs[model_name]

        X_train = df.loc[train_mask, cols]
        y_train = df.loc[train_mask, target]
        X_test = df.loc[test_mask, cols]
        y_test = df.loc[test_mask, target]

        X_fit, y_fit = sample_train(X_train, y_train, spec.train_sample)
        model = spec.builder()
        model.fit(X_fit, y_fit)
        pred = model.predict(X_test)

        overall = evaluate_predictions(y_test, pred)
        active_mask = y_test.ne(0) if target == "bike_change" else pd.Series(True, index=y_test.index)
        active = evaluate_predictions(y_test.loc[active_mask], pred[active_mask.to_numpy()])

        metrics_records.append(
            {
                "target": target,
                "best_model": model_name,
                "feature_set": chosen_feature_set[target],
                "metric_scope": "all_hours",
                **overall,
            }
        )
        metrics_records.append(
            {
                "target": target,
                "best_model": model_name,
                "feature_set": chosen_feature_set[target],
                "metric_scope": "active_hours" if target == "bike_change" else "all_hours_duplicate",
                **active,
            }
        )

        test_slice = df.loc[test_mask, ["station_id", "time", target]].copy()
        test_slice["prediction"] = pred
        test_slice["abs_error"] = (test_slice[target] - test_slice["prediction"]).abs()
        test_slice["target_name"] = target
        prediction_frames.append(test_slice)

        sample_eval = X_test.sample(n=min(5_000, len(X_test)), random_state=RANDOM_STATE)
        sample_y = y_test.loc[sample_eval.index]
        importance = permutation_importance(
            model,
            sample_eval,
            sample_y,
            scoring="neg_root_mean_squared_error",
            n_repeats=3,
            random_state=RANDOM_STATE,
        )
        importance_frames.append(
            pd.DataFrame(
                {
                    "target": target,
                    "feature": cols,
                    "importance_mean": importance.importances_mean,
                    "importance_std": importance.importances_std,
                }
            ).sort_values("importance_mean", ascending=False)
        )

    return (
        pd.DataFrame(metrics_records),
        pd.concat(prediction_frames, ignore_index=True),
        pd.concat(importance_frames, ignore_index=True),
    )


def write_report(validation_df, benchmark_df, final_metrics, importances):
    report_path = OUTPUT_DIR / "station_hour_model_report.md"

    final_best = (
        final_metrics[final_metrics["metric_scope"] == "all_hours"]
        .sort_values(["target", "rmse"])
        .drop_duplicates("target")
        .set_index("target")
    )
    easier_target = final_best["nrmse_std"].idxmin()

    lines = [
        "# Station-Hour Regression Report",
        "",
        "## 1. 분석 개요",
        "",
        "- 학습 기간: 2023-01-01 ~ 2024-12-31",
        "- 테스트 기간: 2025-01-01 ~ 2025-12-31",
        "- 비교 대상 타깃: `bike_change`(시간별 변화량), `bike_count_index`(관측 기반 재고지수)",
        "- 주의: `bike_count_index`는 절대 재고가 아니라 대여/반납 로그 누적 지수다.",
        "",
        "## 2. 검토 과정",
        "",
        "- 1차: `HistGradientBoostingRegressor`로 `basic` vs `enhanced` feature set 비교",
        "- 2차: 선택된 feature set으로 `Dummy`, `Ridge`, `RandomForest`, `ExtraTrees`, `HistGradientBoosting` 계열 비교",
        "- 3차: 타깃별 최고 ML 모델을 다시 학습하고 2025 전체 성능 및 permutation importance 점검",
        "",
        "## 3. 최종 요약",
        "",
        f"- 변화량 예측 최고 ML 모델: `{final_best.loc['bike_change', 'best_model']}`",
        f"- 재고지수 예측 최고 ML 모델: `{final_best.loc['bike_count_index', 'best_model']}`",
        f"- 정규화 RMSE 기준 더 쉬운 타깃: `{easier_target}`",
        "",
        "## 4. 최종 성능",
        "",
    ]

    for target, row in final_best.iterrows():
        lines.extend(
            [
                f"### {target}",
                "",
                f"- 모델: `{row['best_model']}`",
                f"- feature set: `{row['feature_set']}`",
                f"- RMSE: `{row['rmse']:.4f}`",
                f"- MAE: `{row['mae']:.4f}`",
                f"- R²: `{row['r2']:.4f}`",
                f"- normalized RMSE: `{row['nrmse_std']:.4f}`",
                f"- normalized MAE: `{row['nmae_std']:.4f}`",
                "",
            ]
        )

    lines.extend(
        [
            "## 5. 중요 피처 상위 10개",
            "",
        ]
    )

    for target in ["bike_change", "bike_count_index"]:
        top = importances[importances["target"] == target].head(10)
        lines.append(f"### {target}")
        lines.append("")
        for _, row in top.iterrows():
            lines.append(f"- `{row['feature']}`: {row['importance_mean']:.6f}")
        lines.append("")

    lines.extend(
        [
            "## 6. 추가로 고려할 피처",
            "",
            "- 실시간 또는 시간대별 실제 자전거 재배치 로그",
            "- station별 물리 거치대 수의 월별 변동 이력",
            "- 공휴일/연휴/행사 일정의 정형화된 캘린더 파일",
            "- 강수 형태, 체감온도, 적설량 같은 확장 날씨 변수",
            "- 인접 station의 순유입/순유출과 같은 공간적 상호작용 피처",
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    df = build_dataset()

    validation_df, chosen_feature_set = run_validation_rounds(df)
    benchmark_df, best_ml_model = run_model_benchmark(df, chosen_feature_set)
    final_metrics, predictions, importances = train_final_models(df, chosen_feature_set, best_ml_model)

    validation_df.to_csv(OUTPUT_DIR / "station_hour_validation_metrics.csv", index=False, encoding="utf-8-sig")
    benchmark_df.to_csv(OUTPUT_DIR / "station_hour_test_benchmark_metrics.csv", index=False, encoding="utf-8-sig")
    final_metrics.to_csv(OUTPUT_DIR / "station_hour_final_model_metrics.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(OUTPUT_DIR / "station_hour_best_model_predictions_2025.csv", index=False, encoding="utf-8-sig")
    importances.to_csv(OUTPUT_DIR / "station_hour_feature_importance.csv", index=False, encoding="utf-8-sig")

    comparison = (
        final_metrics[final_metrics["metric_scope"] == "all_hours"]
        .sort_values("nrmse_std")
        .reset_index(drop=True)
    )
    comparison.to_csv(OUTPUT_DIR / "station_hour_target_difficulty_comparison.csv", index=False, encoding="utf-8-sig")

    meta = {
        "chosen_feature_set": chosen_feature_set,
        "best_ml_model": best_ml_model,
    }
    (OUTPUT_DIR / "station_hour_model_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report(validation_df, benchmark_df, final_metrics, importances)

    print("chosen_feature_set", chosen_feature_set)
    print("best_ml_model", best_ml_model)
    print(final_metrics.to_string(index=False))


if __name__ == "__main__":
    main()
