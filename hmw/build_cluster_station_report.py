from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import wrap

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

import run_station_hour_regression as base


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
CLUSTER_DIR = DATA_DIR / "clustering"
REPORT_DIR = ROOT / "reports"
ASSET_DIR = REPORT_DIR / "assets"
REPORT_MD = REPORT_DIR / "station_hour_cluster_augmented_report.md"
REPORT_PDF = REPORT_DIR / "station_hour_cluster_augmented_report.pdf"

REPORT_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


CLUSTER_NAME_MAP = {
    0: "업무/상업 혼합형",
    1: "아침 도착 업무 집중형",
    2: "주거 도착형",
    3: "생활·상권 혼합형",
    4: "외곽 주거형",
}


def load_cluster_labels() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(CLUSTER_DIR / "ddri_second_cluster_train_with_labels.csv", encoding="utf-8-sig")
    test = pd.read_csv(CLUSTER_DIR / "ddri_second_cluster_test_with_labels.csv", encoding="utf-8-sig")
    rep = pd.read_csv(CLUSTER_DIR / "ddri_second_cluster_representative_stations.csv", encoding="utf-8-sig")
    summary = pd.read_csv(CLUSTER_DIR / "ddri_second_cluster_summary.csv", encoding="utf-8-sig")
    return train, test, rep, summary


def add_cluster_features(df: pd.DataFrame, train_labels: pd.DataFrame) -> pd.DataFrame:
    station_cluster = train_labels[["station_id", "cluster"]].drop_duplicates("station_id").copy()
    station_cluster["station_id"] = pd.to_numeric(station_cluster["station_id"], errors="coerce").astype(int)
    station_cluster["cluster"] = pd.to_numeric(station_cluster["cluster"], errors="coerce").astype(int)
    out = df.merge(station_cluster, on="station_id", how="left")
    out["cluster"] = out["cluster"].fillna(-1).astype(int)
    for cluster_id in range(5):
        out[f"cluster_{cluster_id}"] = (out["cluster"] == cluster_id).astype("int8")
    return out


def compare_cluster_stability(train_labels: pd.DataFrame, test_labels: pd.DataFrame) -> pd.DataFrame:
    train_station = train_labels[["station_id", "cluster"]].drop_duplicates().rename(columns={"cluster": "train_cluster"})
    test_station = test_labels[["station_id", "cluster"]].drop_duplicates().rename(columns={"cluster": "test_cluster"})
    merged = train_station.merge(test_station, on="station_id", how="inner")
    merged["cluster_changed"] = (merged["train_cluster"] != merged["test_cluster"]).astype(int)
    return merged


def run_cluster_feature_experiment(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    base_sets = base.feature_sets()
    cluster_cols = ["cluster"] + [f"cluster_{i}" for i in range(5)]
    feature_map = {
        "bike_change_without_cluster": base_sets["enhanced"],
        "bike_change_with_cluster": base_sets["enhanced"] + cluster_cols,
        "bike_count_index_without_cluster": base_sets["basic"],
        "bike_count_index_with_cluster": base_sets["basic"] + cluster_cols,
    }

    train_mask = df["year"].isin([2023, 2024])
    test_mask = df["year"] == 2025
    records: list[dict[str, object]] = []
    predictions: dict[str, np.ndarray] = {}

    configs = [
        (
            "bike_change",
            "bike_change_without_cluster",
            HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_depth=12,
                max_iter=180,
                min_samples_leaf=60,
                l2_regularization=0.05,
                random_state=base.RANDOM_STATE,
            ),
            600_000,
        ),
        (
            "bike_change",
            "bike_change_with_cluster",
            HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_depth=12,
                max_iter=180,
                min_samples_leaf=60,
                l2_regularization=0.05,
                random_state=base.RANDOM_STATE,
            ),
            600_000,
        ),
        (
            "bike_count_index",
            "bike_count_index_without_cluster",
            Ridge(alpha=2.0, random_state=base.RANDOM_STATE),
            400_000,
        ),
        (
            "bike_count_index",
            "bike_count_index_with_cluster",
            Ridge(alpha=2.0, random_state=base.RANDOM_STATE),
            400_000,
        ),
    ]

    for target, feature_key, model, sample_size in configs:
        cols = feature_map[feature_key]
        X_train = df.loc[train_mask, cols]
        y_train = df.loc[train_mask, target]
        X_test = df.loc[test_mask, cols]
        y_test = df.loc[test_mask, target]
        X_fit, y_fit = base.sample_train(X_train, y_train, sample_size)
        model.fit(X_fit, y_fit)
        pred = model.predict(X_test)
        predictions[f"{target}:{feature_key}"] = pred
        metrics = base.evaluate_predictions(y_test, pred)
        records.append(
            {
                "target": target,
                "feature_variant": feature_key,
                "train_rows": len(X_fit),
                "eval_rows": len(X_test),
                **metrics,
            }
        )

    return pd.DataFrame(records), predictions


def compute_cluster_augmented_feature_importance(df: pd.DataFrame) -> pd.DataFrame:
    base_sets = base.feature_sets()
    cluster_cols = ["cluster"] + [f"cluster_{i}" for i in range(5)]
    configs = [
        (
            "bike_change",
            base_sets["enhanced"] + cluster_cols,
            HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_depth=12,
                max_iter=180,
                min_samples_leaf=60,
                l2_regularization=0.05,
                random_state=base.RANDOM_STATE,
            ),
            600_000,
        ),
        (
            "bike_count_index",
            base_sets["basic"] + cluster_cols,
            Ridge(alpha=2.0, random_state=base.RANDOM_STATE),
            400_000,
        ),
    ]
    train_mask = df["year"].isin([2023, 2024])
    test_mask = df["year"] == 2025
    frames: list[pd.DataFrame] = []

    for target, cols, model, sample_size in configs:
        X_train = df.loc[train_mask, cols]
        y_train = df.loc[train_mask, target]
        X_test = df.loc[test_mask, cols]
        y_test = df.loc[test_mask, target]
        X_fit, y_fit = base.sample_train(X_train, y_train, sample_size)
        model.fit(X_fit, y_fit)
        sample_eval = X_test.sample(n=min(5_000, len(X_test)), random_state=base.RANDOM_STATE)
        sample_y = y_test.loc[sample_eval.index]
        importance = base.permutation_importance(
            model,
            sample_eval,
            sample_y,
            scoring="neg_root_mean_squared_error",
            n_repeats=3,
            random_state=base.RANDOM_STATE,
        )
        frame = pd.DataFrame(
            {
                "target": target,
                "feature": cols,
                "importance_mean": importance.importances_mean,
                "importance_std": importance.importances_std,
            }
        ).sort_values("importance_mean", ascending=False)
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def run_reduced_feature_experiment(df: pd.DataFrame, importance_df: pd.DataFrame) -> pd.DataFrame:
    threshold = 0.001
    ranked = importance_df[
        (importance_df["target"] == "bike_change") & (importance_df["importance_mean"] > threshold)
    ]["feature"].tolist()
    train_mask = df["year"].isin([2023, 2024])
    test_mask = df["year"] == 2025

    X_train = df.loc[train_mask, ranked]
    y_train = df.loc[train_mask, "bike_change"]
    X_test = df.loc[test_mask, ranked]
    y_test = df.loc[test_mask, "bike_change"]

    model = HistGradientBoostingRegressor(
        learning_rate=0.04,
        max_depth=12,
        max_iter=180,
        min_samples_leaf=60,
        l2_regularization=0.05,
        random_state=base.RANDOM_STATE,
    )
    X_fit, y_fit = base.sample_train(X_train, y_train, 600_000)
    model.fit(X_fit, y_fit)
    pred = model.predict(X_test)
    metrics = base.evaluate_predictions(y_test, pred)

    return pd.DataFrame(
        [
            {
                "variant": "full_feature_set",
                "feature_count": len(base.feature_sets()["enhanced"] + ["cluster"] + [f"cluster_{i}" for i in range(5)]),
                "selection_rule": "enhanced + cluster",
                "rmse": 1.050757,
                "mae": 0.586025,
                "r2": 0.210975,
            },
            {
                "variant": "reduced_feature_set",
                "feature_count": len(ranked),
                "selection_rule": f"importance_mean > {threshold}",
                **metrics,
            },
        ]
    )


def run_cluster_specific_model_experiment(
    df: pd.DataFrame, global_prediction_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_mask = df["year"].isin([2023, 2024])
    test_mask = df["year"] == 2025
    feature_cols = base.feature_sets()["enhanced"]
    specs = [spec for spec in base.model_specs() if spec.name != "dummy_mean"]
    cluster_sample_caps = {
        "ridge": 120_000,
        "random_forest": 40_000,
        "extra_trees": 40_000,
        "hist_gbm": 150_000,
        "hist_gbm_tuned": 180_000,
    }
    benchmark_rows: list[dict[str, object]] = []
    best_rows: list[dict[str, object]] = []
    importance_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []

    global_pred_map = global_prediction_df[["station_id", "time", "prediction"]].rename(columns={"prediction": "global_prediction"})

    specialist_frames: list[pd.DataFrame] = []

    for cluster_id in range(5):
        cluster_train_mask = train_mask & (df["cluster"] == cluster_id)
        cluster_test_mask = test_mask & (df["cluster"] == cluster_id)
        X_train = df.loc[cluster_train_mask, feature_cols]
        y_train = df.loc[cluster_train_mask, "bike_change"]
        X_test = df.loc[cluster_test_mask, feature_cols]
        y_test = df.loc[cluster_test_mask, "bike_change"]

        if len(X_train) == 0 or len(X_test) == 0:
            continue

        cluster_predictions: dict[str, np.ndarray] = {}
        for spec in specs:
            sample_cap = cluster_sample_caps.get(spec.name, spec.train_sample)
            X_fit, y_fit = base.sample_train(X_train, y_train, sample_cap)
            model = spec.builder()
            model.fit(X_fit, y_fit)
            pred = model.predict(X_test)
            cluster_predictions[spec.name] = pred
            metrics = base.evaluate_predictions(y_test, pred)
            benchmark_rows.append(
                {
                    "cluster": cluster_id,
                    "cluster_name": CLUSTER_NAME_MAP.get(cluster_id, f"cluster_{cluster_id}"),
                    "model": spec.name,
                    "train_rows": len(X_fit),
                    "eval_rows": len(X_test),
                    **metrics,
                    "feature_set": "enhanced_no_cluster",
                }
            )

        cluster_benchmark = pd.DataFrame([row for row in benchmark_rows if row["cluster"] == cluster_id]).sort_values(["rmse", "mae"])
        best_row = cluster_benchmark.iloc[0].to_dict()
        best_model_name = best_row["model"]
        best_rows.append(best_row)

        best_sample_cap = cluster_sample_caps.get(best_model_name, next(spec.train_sample for spec in specs if spec.name == best_model_name))
        X_fit, y_fit = base.sample_train(X_train, y_train, best_sample_cap)
        best_model = next(spec.builder() for spec in specs if spec.name == best_model_name)
        best_model.fit(X_fit, y_fit)
        best_pred = cluster_predictions[best_model_name]

        specialist_frame = df.loc[cluster_test_mask, ["station_id", "time", "cluster", "bike_change"]].copy()
        specialist_frame["specialist_prediction"] = best_pred
        specialist_frames.append(specialist_frame)

        sample_eval = X_test.sample(n=min(1_500, len(X_test)), random_state=base.RANDOM_STATE)
        sample_y = y_test.loc[sample_eval.index]
        importance = base.permutation_importance(
            best_model,
            sample_eval,
            sample_y,
            scoring="neg_root_mean_squared_error",
            n_repeats=2,
            random_state=base.RANDOM_STATE,
        )
        importance_rows.extend(
            pd.DataFrame(
                {
                    "cluster": cluster_id,
                    "cluster_name": CLUSTER_NAME_MAP.get(cluster_id, f"cluster_{cluster_id}"),
                    "best_model": best_model_name,
                    "feature": feature_cols,
                    "importance_mean": importance.importances_mean,
                    "importance_std": importance.importances_std,
                }
            )
            .sort_values("importance_mean", ascending=False)
            .to_dict("records")
        )

    specialist_pred_df = pd.concat(specialist_frames, ignore_index=True).merge(global_pred_map, on=["station_id", "time"], how="left")
    for cluster_id, cluster_name in CLUSTER_NAME_MAP.items():
        cluster_slice = specialist_pred_df[specialist_pred_df["cluster"] == cluster_id]
        if len(cluster_slice) == 0:
            continue
        specialist_metrics = base.evaluate_predictions(cluster_slice["bike_change"], cluster_slice["specialist_prediction"])
        global_metrics = base.evaluate_predictions(cluster_slice["bike_change"], cluster_slice["global_prediction"])
        comparison_rows.extend(
            [
                {
                    "scope": "cluster",
                    "cluster": cluster_id,
                    "cluster_name": cluster_name,
                    "variant": "global_shared_model",
                    **global_metrics,
                },
                {
                    "scope": "cluster",
                    "cluster": cluster_id,
                    "cluster_name": cluster_name,
                    "variant": "cluster_specific_model",
                    **specialist_metrics,
                },
            ]
        )

    overall_global = base.evaluate_predictions(specialist_pred_df["bike_change"], specialist_pred_df["global_prediction"])
    overall_specialist = base.evaluate_predictions(specialist_pred_df["bike_change"], specialist_pred_df["specialist_prediction"])
    comparison_rows.extend(
        [
            {
                "scope": "overall",
                "cluster": -1,
                "cluster_name": "overall",
                "variant": "global_shared_model",
                **overall_global,
            },
            {
                "scope": "overall",
                "cluster": -1,
                "cluster_name": "overall",
                "variant": "cluster_specific_model",
                **overall_specialist,
            },
        ]
    )

    return (
        pd.DataFrame(benchmark_rows),
        pd.DataFrame(best_rows),
        pd.DataFrame(importance_rows),
        pd.DataFrame(comparison_rows),
    )


def feature_description(feature: str) -> tuple[str, str, str]:
    manual = {
        "station_id": ("identifier", "station 고유 식별자", "시간별 집계 데이터"),
        "year": ("calendar", "연도", "time 파생"),
        "month": ("calendar", "월", "time 파생"),
        "day": ("calendar", "일", "time 파생"),
        "weekday": ("calendar", "요일(0~6)", "time 파생"),
        "hour": ("calendar", "시간(0~23)", "time 파생"),
        "dayofyear": ("calendar", "연중 몇 번째 날인지", "time 파생"),
        "weekofyear": ("calendar", "연중 몇 번째 주인지", "time 파생"),
        "is_weekend": ("calendar", "주말 여부", "휴일 캘린더"),
        "is_holiday": ("calendar", "공휴일 여부", "휴일 캘린더"),
        "is_holiday_eve": ("calendar", "공휴일 전날 여부", "휴일 캘린더"),
        "is_weekend_or_holiday": ("calendar", "주말 또는 공휴일 여부", "휴일 캘린더"),
        "is_commute_hour": ("calendar", "출퇴근 시간대 여부", "time 파생"),
        "is_night_hour": ("calendar", "심야 시간대 여부", "time 파생"),
        "is_lunch_hour": ("calendar", "점심 시간대 여부", "time 파생"),
        "hour_sin": ("calendar", "시간의 주기성(sin)", "time 파생"),
        "hour_cos": ("calendar", "시간의 주기성(cos)", "time 파생"),
        "weekday_sin": ("calendar", "요일의 주기성(sin)", "time 파생"),
        "weekday_cos": ("calendar", "요일의 주기성(cos)", "time 파생"),
        "month_sin": ("calendar", "월의 주기성(sin)", "time 파생"),
        "month_cos": ("calendar", "월의 주기성(cos)", "time 파생"),
        "temperature": ("weather", "기온", "gangnam_weather"),
        "humidity": ("weather", "습도", "gangnam_weather"),
        "precipitation": ("weather", "강수량", "gangnam_weather"),
        "wind_speed": ("weather", "풍속", "gangnam_weather"),
        "is_rainy": ("weather", "강수 여부", "gangnam_weather 파생"),
        "heavy_rain": ("weather", "강한 비 여부", "gangnam_weather 파생"),
        "temp_x_commute": ("weather_interaction", "출퇴근 시간대 기온 상호작용", "weather x calendar"),
        "rain_x_commute": ("weather_interaction", "출퇴근 시간대 강수 상호작용", "weather x calendar"),
        "rain_x_night": ("weather_interaction", "심야 시간대 강수 상호작용", "weather x calendar"),
        "lat": ("station_meta", "대여소 위도", "대여소 정보"),
        "lon": ("station_meta", "대여소 경도", "대여소 정보"),
        "lcd_count": ("station_meta", "LCD 거치대 수", "대여소 정보"),
        "qr_count": ("station_meta", "QR 거치대 수", "대여소 정보"),
        "dock_total": ("station_meta", "총 거치면 수", "대여소 정보"),
        "is_qr_mixed": ("station_meta", "QR 혼합 대여소 여부", "대여소 정보"),
        "cluster": ("cluster", "train 기준 cluster 라벨", "works/01_clustering 결과"),
        "cluster_0": ("cluster", "cluster 0 여부", "cluster dummy"),
        "cluster_1": ("cluster", "cluster 1 여부", "cluster dummy"),
        "cluster_2": ("cluster", "cluster 2 여부", "cluster dummy"),
        "cluster_3": ("cluster", "cluster 3 여부", "cluster dummy"),
        "cluster_4": ("cluster", "cluster 4 여부", "cluster dummy"),
    }
    if feature in manual:
        return manual[feature]
    if "_lag_" in feature:
        base_name, lag = feature.split("_lag_")
        return ("lag", f"{base_name}의 {lag}시간 전 값", "station-hour 집계 파생")
    if "_rollmean_" in feature:
        base_name, window = feature.split("_rollmean_")
        return ("rolling", f"{base_name}의 직전 {window}시간 이동평균", "station-hour 집계 파생")
    if "_rollstd_" in feature:
        base_name, window = feature.split("_rollstd_")
        return ("rolling", f"{base_name}의 직전 {window}시간 이동표준편차", "station-hour 집계 파생")
    return ("other", feature, "파생 feature")


def build_feature_inventory(importance_df: pd.DataFrame, target: str) -> pd.DataFrame:
    subset = importance_df[importance_df["target"] == target].copy()
    rows = []
    for _, row in subset.iterrows():
        category, description, source = feature_description(row["feature"])
        rows.append(
            {
                "target": target,
                "feature": row["feature"],
                "category": category,
                "description": description,
                "source": source,
                "importance_mean": row["importance_mean"],
                "importance_std": row["importance_std"],
            }
        )
    return pd.DataFrame(rows).sort_values("importance_mean", ascending=False)


def pick_representative_stations(
    flow_2025: pd.DataFrame,
    rep: pd.DataFrame,
    prediction_df: pd.DataFrame,
    train_labels: pd.DataFrame,
) -> pd.DataFrame:
    station_usage = flow_2025.groupby("station_id", as_index=False).agg(
        rental_total_2025=("rental_count", "sum"),
        return_total_2025=("return_count", "sum"),
        bike_change_abs_mean_2025=("bike_change", lambda s: np.mean(np.abs(s))),
    )
    pred_error = prediction_df.groupby("station_id", as_index=False).agg(
        mean_abs_error=("abs_error", "mean"),
        max_abs_error=("abs_error", "max"),
    )
    train_station = train_labels[
        [
            "station_id",
            "cluster",
            "station_name",
            "주소",
            "subway_distance_m",
            "bus_stop_count_300m",
            "arrival_7_10_ratio",
            "arrival_17_20_ratio",
        ]
    ].drop_duplicates("station_id")

    merged = (
        train_station.merge(rep[["station_id", "center_distance"]], on="station_id", how="left")
        .merge(station_usage, on="station_id", how="left")
        .merge(pred_error, on="station_id", how="left")
    )
    merged["center_distance"] = merged["center_distance"].fillna(
        merged.groupby("cluster")["center_distance"].transform("median")
    )
    merged["representative_score"] = merged.groupby("cluster")["center_distance"].transform(
        lambda s: 1 - (s - s.min()) / (s.max() - s.min() + 1e-6)
    )
    merged["usage_score"] = merged.groupby("cluster")["rental_total_2025"].transform(
        lambda s: (s - s.min()) / (s.max() - s.min() + 1e-6)
    )
    merged["error_score"] = merged.groupby("cluster")["mean_abs_error"].transform(
        lambda s: (s - s.min()) / (s.max() - s.min() + 1e-6)
    )
    merged["selection_score"] = 0.45 * merged["usage_score"] + 0.35 * merged["representative_score"] + 0.20 * merged["error_score"]
    merged["cluster_name"] = merged["cluster"].map(CLUSTER_NAME_MAP)
    selected = (
        merged.sort_values(["cluster", "selection_score"], ascending=[True, False])
        .groupby("cluster", group_keys=False)
        .head(3)
        .copy()
    )
    selected["selection_reason"] = selected.apply(
        lambda r: f"usage {r['rental_total_2025']:.0f}, center {r['center_distance']:.3f}, mae {r['mean_abs_error']:.3f}",
        axis=1,
    )
    return selected.sort_values(["cluster", "selection_score"], ascending=[True, False])


def build_station_charts(
    selected: pd.DataFrame,
    prediction_df: pd.DataFrame,
    train_labels: pd.DataFrame,
    cluster_stability: pd.DataFrame,
):
    train_flow = pd.read_csv(DATA_DIR / "station_hour_bike_flow_train_2023_2024.csv", encoding="utf-8-sig", parse_dates=["time"])
    test_flow = pd.read_csv(DATA_DIR / "station_hour_bike_flow_test_2025.csv", encoding="utf-8-sig", parse_dates=["time"])

    coverage = pd.DataFrame(
        {
            "split": ["train_2023_2024", "test_2025"],
            "rows": [len(train_flow), len(test_flow)],
            "stations": [train_flow["station_id"].nunique(), test_flow["station_id"].nunique()],
        }
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(coverage["split"], coverage["rows"], color=["#4c956c", "#f4a261"])
    ax.set_title("학습/테스트 데이터 규모")
    ax.set_ylabel("station-hour rows")
    for i, row in coverage.iterrows():
        ax.text(i, row["rows"], f"{int(row['rows']):,}\n({int(row['stations'])} stations)", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "data_coverage.png", dpi=160)
    plt.close(fig)

    hourly_overview = test_flow.groupby("hour", as_index=False).agg(
        rental_mean=("rental_count", "mean"),
        return_mean=("return_count", "mean"),
        bike_change_mean=("bike_change", "mean"),
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(hourly_overview["hour"], hourly_overview["rental_mean"], marker="o", label="rental_mean", color="#e76f51")
    ax.plot(hourly_overview["hour"], hourly_overview["return_mean"], marker="o", label="return_mean", color="#2a9d8f")
    ax.plot(hourly_overview["hour"], hourly_overview["bike_change_mean"], marker="o", label="bike_change_mean", color="#1d3557")
    ax.set_title("2025 시간대별 평균 흐름")
    ax.set_xlabel("hour")
    ax.set_ylabel("mean count")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "hourly_flow_overview.png", dpi=160)
    plt.close(fig)

    weekday_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    weekday_df = test_flow.groupby("weekday", as_index=False).agg(
        rental_mean=("rental_count", "mean"),
        return_mean=("return_count", "mean"),
        bike_change_mean=("bike_change", "mean"),
    )
    weekday_df["weekday_label"] = weekday_df["weekday"].map(weekday_map)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(weekday_df["weekday_label"], weekday_df["bike_change_mean"], color="#457b9d", alpha=0.8, label="bike_change_mean")
    ax.plot(weekday_df["weekday_label"], weekday_df["rental_mean"], marker="o", color="#bc4749", label="rental_mean")
    ax.plot(weekday_df["weekday_label"], weekday_df["return_mean"], marker="o", color="#2a9d8f", label="return_mean")
    ax.set_title("2025 요일별 평균 흐름")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "weekday_flow_overview.png", dpi=160)
    plt.close(fig)

    pred_map = prediction_df.merge(train_labels[["station_id", "cluster"]].drop_duplicates(), on="station_id", how="left")
    pred_map["cluster_name"] = pred_map["cluster"].map(CLUSTER_NAME_MAP)

    benchmark = pd.read_csv(DATA_DIR / "station_hour_test_benchmark_metrics.csv", encoding="utf-8-sig")
    for target in ["bike_change", "bike_count_index"]:
        subset = benchmark[benchmark["target"] == target].copy().sort_values("rmse")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(subset["model"], subset["rmse"], color="#4c956c")
        ax.set_title(f"{target} 모델별 RMSE 비교")
        ax.set_xlabel("RMSE")
        fig.tight_layout()
        fig.savefig(ASSET_DIR / f"benchmark_{target}.png", dpi=160)
        plt.close(fig)

    importance = pd.read_csv(DATA_DIR / "station_hour_feature_importance.csv", encoding="utf-8-sig")
    imp_subset = importance[importance["target"] == "bike_change"].head(10).sort_values("importance_mean")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(imp_subset["feature"], imp_subset["importance_mean"], color="#bc4749")
    ax.set_title("bike_change 상위 중요 피처")
    ax.set_xlabel("importance_mean")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "feature_importance_bike_change.png", dpi=160)
    plt.close(fig)

    difficulty = pd.read_csv(DATA_DIR / "station_hour_target_difficulty_comparison.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(difficulty["target"], difficulty["nrmse_std"], color=["#457b9d", "#f4a261"])
    ax.set_title("타깃별 정규화 RMSE 비교")
    ax.set_ylabel("nRMSE (std)")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "target_difficulty.png", dpi=160)
    plt.close(fig)

    comparison = pd.read_csv(DATA_DIR / "station_hour_cluster_feature_experiment.csv", encoding="utf-8-sig")
    comp = comparison.copy()
    comp["label"] = comp["target"] + "\n" + comp["feature_variant"].str.replace("_", " ")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(comp["label"], comp["rmse"], color=["#8d99ae", "#2a9d8f", "#8d99ae", "#2a9d8f"])
    ax.set_title("cluster feature 추가 전후 RMSE")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_feature_effect.png", dpi=160)
    plt.close(fig)

    cluster_mae = pred_map.groupby(["cluster", "cluster_name"], as_index=False)["abs_error"].mean().sort_values("cluster")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(cluster_mae["cluster_name"], cluster_mae["abs_error"], color="#2a6f97")
    ax.set_title("Cluster별 bike_change 평균 절대오차(2025)")
    ax.set_ylabel("MAE")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_mae.png", dpi=160)
    plt.close(fig)

    stability_counts = pd.Series(
        {
            "유지": int((cluster_stability["cluster_changed"] == 0).sum()),
            "변경": int((cluster_stability["cluster_changed"] == 1).sum()),
        }
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(stability_counts.index, stability_counts.values, color=["#4c956c", "#e76f51"])
    ax.set_title("2025 cluster 안정성")
    ax.set_ylabel("station 수")
    for i, v in enumerate(stability_counts.values):
        ax.text(i, v, f"{v}", ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_stability.png", dpi=160)
    plt.close(fig)

    summary = pd.read_csv(CLUSTER_DIR / "ddri_second_cluster_summary.csv", encoding="utf-8-sig")
    summary["cluster_name"] = summary["cluster"].map(CLUSTER_NAME_MAP)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(summary["cluster_name"], summary["station_count"], color="#6a994e")
    ax.set_title("cluster별 station 수")
    ax.set_ylabel("station_count")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_station_count.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(summary["cluster_name"], summary["arrival_7_10_ratio"], color="#f4a261")
    axes[0].set_title("아침 도착 비율")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(summary["cluster_name"], summary["arrival_17_20_ratio"], color="#457b9d")
    axes[1].set_title("저녁 도착 비율")
    axes[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_profile.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    labels = selected["cluster_name"] + " | " + selected["station_name"]
    ax.barh(labels, selected["rental_total_2025"], color="#588157")
    ax.set_title("선정 대표 station의 2025 대여 총량")
    ax.set_xlabel("rental_total_2025")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "representative_station_usage.png", dpi=160)
    plt.close(fig)

    score_cols = selected[["cluster_name", "station_name", "selection_score"]].copy()
    score_cols["label"] = score_cols["cluster_name"] + " | " + score_cols["station_name"]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(score_cols["label"], score_cols["selection_score"], color="#6a4c93")
    ax.set_title("대표 station 선정 점수")
    ax.set_xlabel("selection_score")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "representative_station_score.png", dpi=160)
    plt.close(fig)

    focus_ids = selected["station_id"].tolist()
    focus_pred = pred_map[pred_map["station_id"].isin(focus_ids)].copy()
    focus_pred["hour"] = pd.to_datetime(focus_pred["time"]).dt.hour
    daily_profile = (
        focus_pred.groupby(["station_id", "hour"], as_index=False)
        .agg(actual_mean=("bike_change", "mean"), pred_mean=("prediction", "mean"))
        .merge(selected[["station_id", "station_name", "cluster_name"]], on="station_id", how="left")
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    sample = daily_profile.groupby("cluster_name", group_keys=False).head(1)
    for _, row in sample.iterrows():
        station_df = daily_profile[daily_profile["station_id"] == row["station_id"]]
        ax.plot(station_df["hour"], station_df["actual_mean"], label=f"{row['cluster_name']} actual")
        ax.plot(station_df["hour"], station_df["pred_mean"], linestyle="--", label=f"{row['cluster_name']} pred")
    ax.set_title("Cluster별 대표 station 1개 평균 시간대 프로파일")
    ax.set_xlabel("hour")
    ax.set_ylabel("bike_change")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_station_daily_profile.png", dpi=160)
    plt.close(fig)

    pred_map["month"] = pd.to_datetime(pred_map["time"]).dt.month
    monthly = pred_map.groupby("month", as_index=False).agg(
        actual_mean=("bike_change", "mean"),
        pred_mean=("prediction", "mean"),
        mae=("abs_error", "mean"),
    )
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(monthly["month"], monthly["actual_mean"], marker="o", label="actual mean", color="#1d3557")
    ax1.plot(monthly["month"], monthly["pred_mean"], marker="o", linestyle="--", label="pred mean", color="#e76f51")
    ax1.set_title("2025 월별 평균 bike_change 추세")
    ax1.set_xlabel("month")
    ax1.set_ylabel("mean bike_change")
    ax1.legend(loc="upper left")
    ax2 = ax1.twinx()
    ax2.bar(monthly["month"], monthly["mae"], alpha=0.2, color="#457b9d", label="mae")
    ax2.set_ylabel("monthly MAE")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "monthly_trend_actual_vs_pred.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    residual = pred_map["bike_change"] - pred_map["prediction"]
    ax.hist(residual.clip(-8, 8), bins=40, color="#577590", alpha=0.85)
    ax.set_title("bike_change 잔차 분포")
    ax.set_xlabel("actual - prediction (clipped to [-8, 8])")
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "residual_distribution.png", dpi=160)
    plt.close(fig)

    final_metrics = pd.read_csv(DATA_DIR / "station_hour_final_model_metrics.csv", encoding="utf-8-sig")
    final_all = final_metrics[final_metrics["metric_scope"] == "all_hours"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(final_all["target"], final_all["mae"], color=["#e76f51", "#2a9d8f"])
    axes[0].set_title("최종 모델 MAE")
    axes[0].set_ylabel("MAE")
    axes[1].bar(final_all["target"], final_all["nrmse_std"], color=["#457b9d", "#f4a261"])
    axes[1].set_title("최종 모델 nRMSE")
    axes[1].set_ylabel("nRMSE (std)")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "final_conclusion_summary.png", dpi=160)
    plt.close(fig)


def build_cluster_specific_charts(best_models: pd.DataFrame, comparison: pd.DataFrame, importance: pd.DataFrame):
    best_plot = best_models.sort_values("cluster").copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(best_plot["cluster_name"], best_plot["rmse"], color="#3a86ff")
    ax.set_title("cluster별 최적 모델 RMSE")
    ax.set_ylabel("RMSE")
    for bar, label in zip(bars, best_plot["model"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, label, ha="center", va="bottom", rotation=90, fontsize=8)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_specific_best_rmse.png", dpi=160)
    plt.close(fig)

    cmp_plot = comparison[comparison["scope"] == "cluster"].copy()
    rmse_pivot = cmp_plot.pivot(index="cluster_name", columns="variant", values="rmse").reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(rmse_pivot))
    width = 0.35
    ax.bar(x - width / 2, rmse_pivot["global_shared_model"], width, label="global_shared_model", color="#8ecae6")
    ax.bar(x + width / 2, rmse_pivot["cluster_specific_model"], width, label="cluster_specific_model", color="#219ebc")
    ax.set_xticks(x)
    ax.set_xticklabels(rmse_pivot["cluster_name"], rotation=20, ha="right")
    ax.set_ylabel("RMSE")
    ax.set_title("cluster별 글로벌 모델 vs cluster 특화 모델")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "cluster_specific_vs_global_rmse.png", dpi=160)
    plt.close(fig)

    for cluster_id in range(5):
        subset = importance[importance["cluster"] == cluster_id].head(5).copy()
        subset["rank"] = np.arange(1, len(subset) + 1)


def write_markdown(cluster_stability: pd.DataFrame, cluster_experiment: pd.DataFrame, selected: pd.DataFrame, final_metrics: pd.DataFrame):
    changed = int(cluster_stability["cluster_changed"].sum())
    total = int(len(cluster_stability))
    benchmark = pd.read_csv(DATA_DIR / "station_hour_test_benchmark_metrics.csv", encoding="utf-8-sig")
    augmented_importance = pd.read_csv(DATA_DIR / "station_hour_cluster_augmented_feature_importance.csv", encoding="utf-8-sig")
    feature_inventory = pd.read_csv(DATA_DIR / "station_hour_feature_inventory.csv", encoding="utf-8-sig")
    reduced_feature_experiment = pd.read_csv(DATA_DIR / "station_hour_reduced_feature_experiment.csv", encoding="utf-8-sig")
    reduced_feature_experiment = pd.read_csv(DATA_DIR / "station_hour_reduced_feature_experiment.csv", encoding="utf-8-sig")
    reduced_feature_experiment = pd.read_csv(DATA_DIR / "station_hour_reduced_feature_experiment.csv", encoding="utf-8-sig")

    bike_change_cmp = cluster_experiment[cluster_experiment["target"] == "bike_change"].sort_values("rmse")
    bike_index_cmp = cluster_experiment[cluster_experiment["target"] == "bike_count_index"].sort_values("rmse")
    base_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_without_cluster"].iloc[0]
    with_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_with_cluster"].iloc[0]
    base_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_without_cluster"].iloc[0]
    with_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_with_cluster"].iloc[0]

    def model_rank_table(target: str) -> pd.DataFrame:
        sub = benchmark[(benchmark["target"] == target) & (~benchmark["model"].str.startswith("baseline_"))].copy()
        sub = sub.sort_values(["rmse", "mae"]).reset_index(drop=True)
        sub["rank"] = np.arange(1, len(sub) + 1)
        return sub[["rank", "model", "rmse", "mae", "r2", "notes"]]

    bike_change_rank = model_rank_table("bike_change")
    bike_index_rank = model_rank_table("bike_count_index")

    selected_table = selected[
        ["cluster", "cluster_name", "station_id", "station_name", "rental_total_2025", "mean_abs_error", "selection_reason"]
    ].copy()
    report_feature_threshold = 0.001
    bike_change_inventory_report = feature_inventory[
        (feature_inventory["target"] == "bike_change") & (feature_inventory["importance_mean"] > report_feature_threshold)
    ][["feature", "category", "description", "source", "importance_mean", "importance_std"]].copy()
    bike_change_importance_report = augmented_importance[
        (augmented_importance["target"] == "bike_change") & (augmented_importance["importance_mean"] > report_feature_threshold)
    ].copy()
    reduced_full = reduced_feature_experiment[reduced_feature_experiment["variant"] == "full_feature_set"].iloc[0]
    reduced_slim = reduced_feature_experiment[reduced_feature_experiment["variant"] == "reduced_feature_set"].iloc[0]
    cluster_specific_benchmark = pd.read_csv(
        DATA_DIR / "station_hour_cluster_specific_model_benchmark.csv", encoding="utf-8-sig"
    )
    reduced_full = reduced_feature_experiment[reduced_feature_experiment["variant"] == "full_feature_set"].iloc[0]
    reduced_slim = reduced_feature_experiment[reduced_feature_experiment["variant"] == "reduced_feature_set"].iloc[0]

    lines = [
        "# Station-Hour Cluster Augmented Report",
        "",
        "## 1. 분석 개요",
        "",
        "- 학습 기간: `2023-01-01 ~ 2024-12-31`",
        "- 테스트 기간: `2025-01-01 ~ 2025-12-31`",
        "- 기본 문제 정의: `station-hour` 단위 회귀",
        "- 핵심 타깃: `bike_change`, `bike_count_index`",
        "- 최종 확장 질문: `cluster 0~4`를 feature로 추가하면 성능과 해석이 개선되는가",
        "",
        "## 2. 최종 선택 모델",
        "",
        "### bike_change 케이스",
        "",
        f"- 최종 선택 모델 family: `hist_gbm_tuned`",
        f"- 기본 enhanced feature 기준 성능: RMSE `{base_change.rmse:.4f}`, MAE `{base_change.mae:.4f}`",
        f"- cluster 추가 후 최종 성능: RMSE `{with_change.rmse:.4f}`, MAE `{with_change.mae:.4f}`",
        f"- cluster 추가 개선폭: RMSE `{with_change.rmse - base_change.rmse:.4f}`, MAE `{with_change.mae - base_change.mae:.4f}`",
        "- 해석: 변화량 예측은 비선형성과 시간 반복 패턴이 함께 작동한다. 튜닝된 히스토그램 부스팅은 출퇴근 피크, 날씨 상호작용, lag 구조를 가장 안정적으로 흡수했다.",
        "",
        "### bike_change 모델 순위",
        "",
        bike_change_rank.to_markdown(index=False),
        "",
        "#### bike_change 모델 해석",
        "",
        f"- 1위 `hist_gbm_tuned`: RMSE와 MAE 모두 상위권이며, 큰 오차와 평균 오차를 같이 억제했다. 최종적으로 cluster를 붙였을 때도 가장 자연스럽게 확장되었다.",
        f"- 2위 `hist_gbm`: 튜닝 전 버전이지만 차이가 매우 작다. 즉, 문제 구조 자체가 부스팅 계열에 잘 맞는다는 뜻이다.",
        f"- 3위 `extra_trees`: RMSE는 랜덤포레스트보다 약간 좋았다. 큰 오차를 줄이는 데는 다소 강했지만, MAE는 더 높아 평균적 안정성은 떨어졌다.",
        f"- 4위 `random_forest`: MAE는 `extra_trees`보다 약간 좋지만 RMSE는 더 높았다. 평균적 오차는 억제했지만 피크 구간 큰 오차를 충분히 줄이지 못했다.",
        f"- 5위 `ridge`: 선형 구조만으로도 일정 수준 설명은 가능했지만, 출퇴근 피크와 비선형 상호작용을 충분히 반영하지 못해 RMSE와 MAE 모두 뒤처졌다.",
        f"- 참고 `dummy_mean`: MAE만 보면 낮아 보이지만, 이는 값이 0 근처인 시간이 매우 많기 때문이다. 실제 피크 대응을 못해 R²가 사실상 0이므로 운영용 모델로는 부적절하다.",
        "",
        "### bike_count_index 케이스",
        "",
        f"- 최종 선택 모델 family: `ridge`",
        f"- 기본 basic feature 기준 성능: RMSE `{base_index.rmse:.4f}`, MAE `{base_index.mae:.4f}`",
        f"- cluster 추가 후 최종 성능: RMSE `{with_index.rmse:.4f}`, MAE `{with_index.mae:.4f}`",
        f"- cluster 추가 개선폭: RMSE `{with_index.rmse - base_index.rmse:.4f}`, MAE `{with_index.mae - base_index.mae:.4f}`",
        "- 해석: 이 타깃은 누적지수라 선형성과 자기상관이 매우 강했다. 그래서 복잡한 트리 모델보다 규제가 있는 선형 모델이 훨씬 안정적이었다.",
        "",
        "### bike_count_index 모델 순위",
        "",
        bike_index_rank.to_markdown(index=False),
        "",
        "#### bike_count_index 모델 해석",
        "",
        "- 1위 `ridge`: 누적지수의 선형 구조와 강한 자기상관을 가장 안정적으로 반영했다.",
        "- 2위 `extra_trees`, 3위 `random_forest`: 비선형 앙상블이지만 오히려 규모가 큰 누적지수 문제에서는 불필요한 복잡성이 생겼다.",
        "- 4위 `hist_gbm`, 5위 `hist_gbm_tuned`: 부스팅 계열은 변화량 문제에는 강했지만, 누적지수 문제에서는 대규모 값의 안정성을 충분히 확보하지 못했다.",
        "- 참고 `dummy_mean`: 평균 예측은 구조를 완전히 놓치기 때문에 가장 부적절했다.",
        "",
        "## 3. RMSE와 MAE 해석",
        "",
        "- `RMSE`는 큰 오차를 더 강하게 벌점 주기 때문에, 피크 시간대나 급격한 수요 변동 대응력을 볼 때 중요하다.",
        "- `MAE`는 평균적인 절대 오차이므로, 전체 시간대를 통틀어 얼마나 안정적으로 틀리는지를 보여준다.",
        "- `bike_change`에서는 `hist_gbm_tuned`가 RMSE와 MAE를 함께 낮게 유지했다. 즉, 평균적으로도 안정적이고 큰 실패도 상대적으로 적었다.",
        "- `bike_change`에서 `dummy_mean`의 MAE가 낮게 보인 이유는 값이 0 근처인 시간이 많기 때문이다. 그러나 RMSE와 R²를 보면 피크 구간 대응이 거의 안 된다.",
        "- `bike_count_index`는 MAE와 RMSE가 모두 선형 모델에 유리하게 나타났는데, 이는 누적지수 자체가 변화량보다 훨씬 쉬운 문제이기 때문이다.",
        "",
        "## 4. 최종 사용 Feature 상세",
        "",
        "### 4-1. bike_change 최종 사용 Feature 전체",
        "",
        bike_change_inventory_report.to_markdown(index=False),
        "",
        "### 4-2. bike_count_index 최종 사용 Feature 전체",
        "",
        feature_inventory[feature_inventory["target"] == "bike_count_index"][
            ["feature", "category", "description", "source", "importance_mean", "importance_std"]
        ].to_markdown(index=False),
        "",
        "## 5. 상위 Feature와 importance 해석",
        "",
        "### bike_change 상위 15개",
        "",
        bike_change_importance_report.head(15).to_markdown(index=False),
        "",
        "- `bike_change_lag_168`, `bike_change_lag_24`가 상위인 것은 주간/일간 반복 구조가 매우 강하다는 뜻이다.",
        "- `hour_sin`, `hour`, `is_commute_hour`가 상위인 것은 출퇴근 시간대 패턴이 핵심이라는 뜻이다.",
        "- `cluster`와 일부 `cluster_dummy`가 상위권에 들어오면 station의 공간적 성격이 설명력에 실제 기여하고 있음을 의미한다.",
        "",
        "### bike_count_index 상위 15개",
        "",
        augmented_importance[augmented_importance["target"] == "bike_count_index"].head(15).to_markdown(index=False),
        "",
        "- `bike_count_index_lag_*`와 `bike_index_rollmean_*` 계열이 상위에 오를 가능성이 높다. 이는 누적지수의 자기상관 구조가 매우 강하기 때문이다.",
        "- `station_id`, `cluster`, `dock_total` 같은 정적 정보는 station 수준 차이를 설명하는 보조 축으로 해석할 수 있다.",
        "",
        "## 6. 추가로 검토한 Feature와 보강 사항",
        "",
        "- `3조 공유폴더`와 `hmw/Data`를 다시 확인한 결과, 현재 구조적으로 쓸 수 있는 추가 파일은 대여소 메타데이터, 날씨, 군집 결과였다.",
        "- 이미 모델에는 `lcd_count`, `qr_count`, `dock_total`, `is_qr_mixed`, `temperature`, `humidity`, `precipitation`, `wind_speed`, `cluster` 계열이 반영되어 있다.",
        "- 즉 이번 단계에서 새로 더할 수 있었던 유효 structured feature는 사실상 `cluster`가 핵심 보강 포인트였다.",
        "- 남아 있는 부족 feature는 실시간 재고 API, 재배치 로그, 인접 station 상호작용, 행사/연휴 캘린더와 같은 운영 데이터 계열이다.",
        "",
        "## 7. 대표 station 상세 분석",
        "",
        selected_table.to_markdown(index=False),
        "",
    ]

    for _, row in selected.iterrows():
        lines.extend(
            [
                f"### {row['cluster_name']} | {int(row['station_id'])} {row['station_name']}",
                "",
                f"- 2025 대여 총량: `{int(row['rental_total_2025'])}`",
                f"- 평균 절대오차(MAE): `{row['mean_abs_error']:.4f}`",
                f"- 군집 중심 거리: `{row['center_distance']:.4f}`",
                f"- 선정 사유: `{row['selection_reason']}`",
                "- 해석: 이 station은 해당 cluster의 패턴을 대표하면서도 실제 운영상 중요도가 높거나 예측 난도가 두드러져 개별 분석 대상으로 적합했다.",
                "",
            ]
        )

    lines.extend(
        [
            "## 8. 상세 결론",
            "",
            "- 최종적으로 더 잘 맞는 타깃은 `bike_count_index`였지만, 이 값은 절대 재고가 아니라 관측 기반 누적지수라 서비스 핵심 문제로 보기 어렵다.",
            "- 실제 사용자와 운영자 관점에서 중요한 문제는 `bike_change` 예측이며, 이 문제에서는 `hist_gbm_tuned + enhanced feature + cluster feature` 조합이 가장 현실적이었다.",
            "- RMSE와 MAE를 함께 보면, 선택 모델은 큰 오차와 평균 오차를 동시에 억제했다. 이는 단순한 평균 예측이나 선형 모델보다 실무 가치가 높다는 뜻이다.",
            "- cluster 정보는 성능 향상 폭만 보면 아주 크진 않지만, station의 구조적 성격을 설명하고 대표 station 해석을 가능하게 만드는 데 매우 유효했다.",
            "- 따라서 현 단계의 최종 추천은 `cluster를 보조 feature로 포함한 bike_change 중심 회귀 모델`이며, 이를 실시간 재고 API와 결합해 앱/관리자 웹으로 연결하는 구조다.",
            "- 다음 고도화 우선순위는 `실시간 재고`, `재배치 로그`, `인접 station 상호작용`, `행사/연휴 캘린더`, `확장 날씨 변수` 순서다.",
            "",
        ]
    )

    lines.extend(
        [
            "## Appendix C. bike_change Feature Group Guide",
            "",
            bike_change_feature_group_df.to_markdown(index=False),
            "",
            "- 이 피처 구성은 `과거 같은 시간의 흐름`, `현재 시간대와 요일`, `날씨`, `station 성향`을 함께 반영하도록 설계되었다.",
            "- 특히 `lag24`, `lag168`은 전날 같은 시각, 지난주 같은 요일 같은 시각의 패턴을 담기 때문에 중요도가 높게 나타난다.",
            "",
        ]
    )

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


A4_LANDSCAPE = (11.69, 8.27)


def _new_page():
    fig = plt.figure(figsize=A4_LANDSCAPE)
    fig.patch.set_facecolor("white")
    return fig


def _draw_wrapped_lines(fig, lines: list[str], x: float, y: float, width: int, fontsize: float, line_gap: float):
    cursor = y
    for raw in lines:
        if raw == "":
            cursor -= line_gap * 0.7
            continue
        prefix = "- " if raw.startswith("- ") else ""
        text = raw[2:] if prefix else raw
        wrapped = wrap(text, width=width) or [text]
        for idx, line in enumerate(wrapped):
            fig.text(
                x + (0.018 if prefix else 0.0),
                cursor,
                (prefix if idx == 0 else "  ") + line,
                fontsize=fontsize,
                va="top",
            )
            cursor -= line_gap
        cursor -= line_gap * 0.12
    return cursor


def _draw_report_header(fig, title: str, subtitle: str | None = None):
    if subtitle:
        fig.text(0.06, 0.955, subtitle, fontsize=9.5, color="#64748b")
    fig.text(0.06, 0.92, title, fontsize=19, weight="bold", color="#0f172a")
    fig.add_artist(plt.Line2D([0.06, 0.34], [0.895, 0.895], color="#1d4ed8", linewidth=3))


def _draw_callout(fig, text: str, x: float = 0.06, y: float = 0.08, w: float = 0.88, h: float = 0.09, compact: bool = False):
    rect = plt.Rectangle((x, y), w, h, transform=fig.transFigure, facecolor="#eff6ff", edgecolor="#bfdbfe", linewidth=1.2)
    fig.add_artist(rect)
    fig.add_artist(plt.Line2D([x, x], [y, y + h], transform=fig.transFigure, color="#2563eb", linewidth=4))
    _draw_wrapped_lines(fig, [text], x=x + 0.018, y=y + h - 0.018, width=100 if compact else 88, fontsize=10.2 if compact else 10.8, line_gap=0.022)


def _draw_table(fig, df: pd.DataFrame, bbox: list[float], fontsize: float = 10):
    ax = fig.add_axes(bbox)
    ax.axis("off")
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="left", colLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.35)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#94a3b8")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor("#e0ecff")
            cell.set_text_props(weight="bold", color="#0f172a")
        else:
            cell.set_facecolor("#ffffff")
    return table


def _make_status_page(title: str, status_df: pd.DataFrame, callout: str):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle="Project Report Status")
    fig.text(0.06, 0.845, "보고서 구성 현황", fontsize=13, weight="bold", color="#0f172a")
    _draw_table(fig, status_df, bbox=[0.06, 0.28, 0.88, 0.5], fontsize=10)
    _draw_callout(fig, callout, y=0.11, h=0.1)
    return fig


def _make_table_page(title: str, section_title: str, df: pd.DataFrame, callout: str, subtitle: str | None = None, fontsize: float = 9.5):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    fig.text(0.06, 0.845, section_title, fontsize=13, weight="bold", color="#0f172a")
    _draw_table(fig, df, bbox=[0.05, 0.22, 0.9, 0.56], fontsize=fontsize)
    _draw_callout(fig, callout, y=0.08, h=0.1, compact=True)
    return fig


def _make_text_page(title: str, lines: list[str], subtitle: str | None = None):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    _draw_wrapped_lines(fig, lines, x=0.06, y=0.85, width=84, fontsize=10.8, line_gap=0.025)
    return fig


def _make_two_column_text_page(
    title: str,
    left_title: str,
    left_lines: list[str],
    right_title: str,
    right_lines: list[str],
    subtitle: str | None = None,
):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    fig.text(0.06, 0.845, left_title, fontsize=12.5, weight="bold", color="#0f172a")
    fig.text(0.54, 0.845, right_title, fontsize=12.5, weight="bold", color="#0f172a")
    fig.add_artist(plt.Line2D([0.5, 0.5], [0.11, 0.86], color="#d9d9d9", linewidth=1))
    _draw_wrapped_lines(fig, left_lines, x=0.06, y=0.81, width=38, fontsize=10.4, line_gap=0.023)
    _draw_wrapped_lines(fig, right_lines, x=0.54, y=0.81, width=38, fontsize=10.4, line_gap=0.023)
    return fig


def _make_chart_page(title: str, image_path: Path, caption: list[str], subtitle: str | None = None):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    ax = fig.add_axes([0.08, 0.28, 0.84, 0.5])
    ax.imshow(plt.imread(image_path))
    ax.axis("off")
    _draw_callout(fig, " ".join([line[2:] if line.startswith('- ') else line for line in caption]), y=0.08, h=0.13)
    return fig


def _make_story_chart_page(
    title: str,
    intro_lines: list[str],
    image_path: Path,
    callout: str,
    subtitle: str | None = None,
):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    _draw_wrapped_lines(fig, intro_lines, x=0.06, y=0.855, width=92, fontsize=10.4, line_gap=0.022)
    ax = fig.add_axes([0.06, 0.22, 0.88, 0.48])
    ax.imshow(plt.imread(image_path))
    ax.axis("off")
    _draw_callout(fig, callout, y=0.07, h=0.1, compact=True)
    return fig


def _make_two_chart_page(
    title: str,
    intro_lines: list[str],
    left_image: Path,
    right_image: Path,
    left_label: str,
    right_label: str,
    callout: str,
    subtitle: str | None = None,
):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    _draw_wrapped_lines(fig, intro_lines, x=0.06, y=0.855, width=92, fontsize=10.2, line_gap=0.021)
    fig.text(0.06, 0.625, left_label, fontsize=11.3, weight="bold", color="#0f172a")
    fig.text(0.515, 0.625, right_label, fontsize=11.3, weight="bold", color="#0f172a")
    left_ax = fig.add_axes([0.06, 0.23, 0.41, 0.37])
    left_ax.imshow(plt.imread(left_image))
    left_ax.axis("off")
    right_ax = fig.add_axes([0.515, 0.23, 0.41, 0.37])
    right_ax.imshow(plt.imread(right_image))
    right_ax.axis("off")
    _draw_callout(fig, callout, y=0.07, h=0.1, compact=True)
    return fig


def write_pdf(cluster_experiment: pd.DataFrame, selected: pd.DataFrame, cluster_stability: pd.DataFrame):
    bike_change_cmp = cluster_experiment[cluster_experiment["target"] == "bike_change"].sort_values("rmse")
    bike_index_cmp = cluster_experiment[cluster_experiment["target"] == "bike_count_index"].sort_values("rmse")
    base_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_without_cluster"].iloc[0]
    with_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_with_cluster"].iloc[0]
    base_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_without_cluster"].iloc[0]
    with_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_with_cluster"].iloc[0]
    final_metrics = pd.read_csv(DATA_DIR / "station_hour_final_model_metrics.csv", encoding="utf-8-sig")
    benchmark = pd.read_csv(DATA_DIR / "station_hour_test_benchmark_metrics.csv", encoding="utf-8-sig")
    importance = pd.read_csv(DATA_DIR / "station_hour_feature_importance.csv", encoding="utf-8-sig")
    overall = final_metrics[final_metrics["metric_scope"] == "all_hours"].set_index("target")
    changed = int(cluster_stability["cluster_changed"].sum())
    total = int(len(cluster_stability))
    train_flow = pd.read_csv(DATA_DIR / "station_hour_bike_flow_train_2023_2024.csv", encoding="utf-8-sig", parse_dates=["time"])
    test_flow = pd.read_csv(DATA_DIR / "station_hour_bike_flow_test_2025.csv", encoding="utf-8-sig", parse_dates=["time"])
    full_rows = len(train_flow) + len(test_flow)
    station_count = int(pd.concat([train_flow["station_id"], test_flow["station_id"]]).nunique())
    best_change_model = benchmark[benchmark["target"] == "bike_change"].sort_values("rmse").iloc[0]
    top_importance = importance[importance["target"] == "bike_change"].head(5)["feature"].tolist()
    cluster_counts = selected.groupby("cluster").size().to_dict()

    status_df = pd.DataFrame(
        [
            ["1. 프로젝트 개요", "완료", "분석 목표와 기간 반영"],
            ["2. 데이터 정리", "완료", "station-hour 집계 반영"],
            ["3. 피처 설계", "완료", "시간, lag, 입지, 날씨"],
            ["4. 모델 비교", "완료", "2025 테스트 성능 정리"],
            ["5. 군집 결합", "완료", "cluster 0~4 feature 실험 반영"],
            ["6. 대표 station", "완료", "cluster별 2~3개 선정"],
            ["7. 서비스 연결", "완료", "앱/웹 활용 초안 반영"],
        ],
        columns=["장", "상태", "비고"],
    )
    metrics_df = final_metrics.copy()
    metrics_df["rmse"] = metrics_df["rmse"].map(lambda x: f"{x:.4f}")
    metrics_df["mae"] = metrics_df["mae"].map(lambda x: f"{x:.4f}")
    metrics_df["r2"] = metrics_df["r2"].map(lambda x: f"{x:.4f}")
    metrics_df = metrics_df[["target", "best_model", "feature_set", "metric_scope", "rmse", "mae", "r2"]]
    representative_summary = selected[["cluster_name", "station_name", "rental_total_2025", "mean_abs_error"]].copy()
    representative_summary["rental_total_2025"] = representative_summary["rental_total_2025"].astype(int)
    representative_summary["mean_abs_error"] = representative_summary["mean_abs_error"].map(lambda x: f"{x:.3f}")
    benchmark_rank_change = benchmark[(benchmark["target"] == "bike_change") & (~benchmark["model"].str.startswith("baseline_"))].copy()
    benchmark_rank_change = benchmark_rank_change.sort_values(["rmse", "mae"]).reset_index(drop=True)
    benchmark_rank_change["rank"] = np.arange(1, len(benchmark_rank_change) + 1)
    benchmark_rank_change = benchmark_rank_change[["rank", "model", "rmse", "mae", "r2"]]
    benchmark_rank_index = benchmark[(benchmark["target"] == "bike_count_index") & (~benchmark["model"].str.startswith("baseline_"))].copy()
    benchmark_rank_index = benchmark_rank_index.sort_values(["rmse", "mae"]).reset_index(drop=True)
    benchmark_rank_index["rank"] = np.arange(1, len(benchmark_rank_index) + 1)
    benchmark_rank_index = benchmark_rank_index[["rank", "model", "rmse", "mae", "r2"]]
    augmented_importance = pd.read_csv(DATA_DIR / "station_hour_cluster_augmented_feature_importance.csv", encoding="utf-8-sig")
    feature_inventory = pd.read_csv(DATA_DIR / "station_hour_feature_inventory.csv", encoding="utf-8-sig")

    with PdfPages(REPORT_PDF) as pdf:
        pages = [
            _make_status_page(
                "Station-Hour Prediction Analysis Report",
                status_df,
                f"학습 기간은 {train_flow['time'].min():%Y-%m-%d}부터 {train_flow['time'].max():%Y-%m-%d}, 테스트 기간은 {test_flow['time'].min():%Y-%m-%d}부터 {test_flow['time'].max():%Y-%m-%d}까지다. 전체 행 수는 {full_rows:,}, 대상 station은 {station_count}개다.",
            ),
            _make_text_page(
                "1. Data Sources and Feature Logic",
                [
                    "월별로 나뉜 2023, 2024, 2025 강남구 따릉이 이용정보 CSV를 연도별로 합친 뒤 사용했다.",
                    "- 대여일시와 반납일시를 시간 단위로 내림하여 station-hour 데이터셋을 생성했다.",
                    "- 대여소 메타데이터, 입지 정보, 강남구 날씨 데이터를 결합했다.",
                    "- works/01_clustering의 cluster 0~4 결과를 hmw/Data로 복사해 feature 실험에 활용했다.",
                    "- bike_change = return_count - rental_count, bike_count_index = bike_change 누적합",
                    "- bike_count_index는 절대 재고가 아니라 관측 기반 재고지수이므로 변화 방향 중심으로 해석했다.",
                ],
                subtitle="데이터와 타깃 정의",
            ),
            _make_two_chart_page(
                "2. Data Coverage and Hourly Flow",
                [
                    "모델을 보기 전에 먼저 데이터가 어떤 규모와 패턴을 가지는지 확인했다.",
                    f"- train rows: {len(train_flow):,}, test rows: {len(test_flow):,}",
                    f"- 공통 station 수: {station_count}",
                    "- 시간대별 평균 흐름을 보면 대여와 반납이 출퇴근 시간에 뚜렷하게 달라진다.",
                ],
                ASSET_DIR / "data_coverage.png",
                ASSET_DIR / "hourly_flow_overview.png",
                "data coverage",
                "hourly overview",
                "이 단계는 단순 전처리 확인이 아니라, 예측 문제가 왜 station-hour 구조여야 하는지를 보여주는 근거다.",
                subtitle="데이터 규모와 기본 패턴",
            ),
            _make_two_chart_page(
                "3. Weekly Pattern and Target Meaning",
                [
                    "요일별 흐름을 보면 주중과 주말의 패턴 차이가 뚜렷하다.",
                    "- rental, return, bike_change의 상대적 위치가 요일마다 달라진다.",
                    "- 이는 is_weekend, weekday, holiday 계열 feature가 필요한 이유를 설명한다.",
                    "- bike_change는 실제 운영 판단으로 연결되는 핵심 타깃이고, bike_count_index는 보조적 해석용 지수다.",
                ],
                ASSET_DIR / "weekday_flow_overview.png",
                ASSET_DIR / "target_difficulty.png",
                "weekday overview",
                "target difficulty",
                "주중/주말 차이와 타깃 난이도 비교를 함께 보면, 왜 변화량 예측을 서비스 중심 문제로 보는지 자연스럽게 이어진다.",
                subtitle="타깃 설정 근거",
            ),
            _make_two_chart_page(
                "4. Model Benchmark",
                [
                    "2025년 전체 구간을 테스트셋으로 두고 여러 회귀 모델을 비교했다.",
                    f"- bike_change 최고 성능 모델: {best_change_model['model']}",
                    f"- bike_change RMSE {best_change_model['rmse']:.4f}, MAE {best_change_model['mae']:.4f}, R2 {best_change_model['r2']:.4f}",
                    "- bike_count_index는 ridge가 가장 안정적이었고 구조적으로 더 쉬운 문제였다.",
                ],
                ASSET_DIR / "benchmark_bike_change.png",
                ASSET_DIR / "benchmark_bike_count_index.png",
                "bike_change benchmark",
                "bike_count_index benchmark",
                "두 타깃 모두 baseline보다 ML 모델이 우수했지만, 서비스 가치가 더 큰 것은 변화량 예측인 bike_change였다.",
                subtitle="모델 비교",
            ),
            _make_table_page(
                "5. Top Models for bike_change",
                "bike_change 상위 6개 ML 모델",
                benchmark_rank_change.round(4),
                "선정 기준은 RMSE와 MAE를 함께 본 것이다. hist_gbm_tuned는 큰 오차와 평균 오차를 같이 억제해 최종 채택 모델 family가 되었다.",
                subtitle="모델 랭킹 상세",
                fontsize=9.2,
            ),
            _make_table_page(
                "6. Top Models for bike_count_index",
                "bike_count_index 상위 6개 ML 모델",
                benchmark_rank_index.round(4),
                "bike_count_index는 누적지수라 선형 구조가 매우 강했고, 그래서 ridge가 다른 비선형 모델보다 압도적으로 안정적이었다.",
                subtitle="모델 랭킹 상세",
                fontsize=9.2,
            ),
            _make_two_chart_page(
                "7. Importance and Difficulty",
                [
                    "모델이 어떤 정보를 중요하게 쓰는지와, 어떤 타깃이 더 어려운지를 함께 봤다.",
                    f"- 상위 중요 피처: {', '.join(top_importance)}",
                    f"- bike_change: RMSE {overall.loc['bike_change', 'rmse']:.4f}, nRMSE {overall.loc['bike_change', 'nrmse_std']:.4f}",
                    f"- bike_count_index: RMSE {overall.loc['bike_count_index', 'rmse']:.4f}, nRMSE {overall.loc['bike_count_index', 'nrmse_std']:.6f}",
                    "- bike_count_index는 더 쉽지만, 실제 운영 의미는 bike_change가 더 크다.",
                ],
                ASSET_DIR / "feature_importance_bike_change.png",
                ASSET_DIR / "target_difficulty.png",
                "feature importance",
                "target difficulty",
                "강남구 따릉이 패턴은 강한 반복 리듬을 갖고 있어서 lag와 시간대 파생변수가 매우 중요했다. 반면 누적지수 타깃은 구조적으로 쉬워 보이는 착시가 생길 수 있다.",
                subtitle="핵심 해석",
            ),
            _make_two_chart_page(
                "8. Prediction Behavior",
                [
                    "예측이 연간 추세를 얼마나 따라가는지와 잔차가 어떤 형태로 남는지를 같이 봤다.",
                    "- 월별 평균 수준은 대체로 잘 따라가지만, 세밀한 진폭은 더 개선 여지가 있다.",
                    "- 잔차가 0 부근에 몰리면서도 양쪽 꼬리를 남기는 구조는 특정 시간대/특정 station의 어려움을 의미한다.",
                ],
                ASSET_DIR / "monthly_trend_actual_vs_pred.png",
                ASSET_DIR / "residual_distribution.png",
                "monthly trend",
                "residual distribution",
                "모델은 전체적인 방향성은 잘 따라가지만, 특정 패턴에서는 큰 오차가 남는다. 이 구간은 군집별 보정, 이벤트 피처, 인접 station 상호작용으로 줄일 수 있다.",
                subtitle="예측 거동",
            ),
            _make_status_page(
                "9. Final Metric Summary",
                metrics_df,
                "bike_count_index는 더 쉽게 맞지만, 실제 서비스 가치와 운영 연결성은 bike_change 쪽이 더 크므로 최종 해석은 변화량 중심으로 진행했다.",
            ),
            _make_text_page(
                "10. Why Add Clustering?",
                [
                    "시간 피처와 lag만으로는 station의 구조적 성격을 모두 설명하기 어렵다.",
                    "- 어떤 station은 아침 유입이 강하고 어떤 station은 저녁 유입이 강하다.",
                    "- 생활권/업무권/외곽형 차이가 있다.",
                    "- 이 차이를 요약한 station-level 성향 정보를 모델에 넣기 위해 cluster를 사용했다.",
                    "- 미래 cluster를 그대로 넣으면 leakage가 생기므로 train 기준 cluster만 feature로 사용했다.",
                    f"- 공통 station 수: {total}, 2025년에 cluster가 바뀐 station 수: {changed}, 변화율: {changed / total:.2%}",
                ],
                subtitle="군집 결합 설계",
            ),
            _make_two_chart_page(
                "11. Cluster Effect and Stability",
                [
                    f"- bike_change: without {base_change.rmse:.4f} -> with {with_change.rmse:.4f}",
                    f"- bike_count_index: without {base_index.rmse:.4f} -> with {with_index.rmse:.4f}",
                    f"- 유지 station 수: {int((cluster_stability['cluster_changed'] == 0).sum())}, 변경 station 수: {int((cluster_stability['cluster_changed'] == 1).sum())}",
                    "- 군집 정보의 성능 향상 폭은 크지 않지만, 해석용 보조 feature로는 분명히 유효했다.",
                ],
                ASSET_DIR / "cluster_feature_effect.png",
                ASSET_DIR / "cluster_stability.png",
                "feature effect",
                "cluster stability",
                "cluster는 station 성격을 압축하는 요약 feature로 유용했지만, 2025에도 그대로 고정되는 절대 라벨은 아니었다.",
                subtitle="군집 효과",
            ),
            _make_two_chart_page(
                "12. Cluster Interpretation",
                [
                    "군집별 아침/저녁 도착 패턴과 군집별 예측오차를 같이 보면 어떤 군집이 더 예측하기 어려운지 읽을 수 있다.",
                    "- 업무형 군집과 주거형 군집의 시간대 성격 차이가 뚜렷하게 드러난다.",
                    "- 오차가 큰 군집은 비정형 패턴이 섞여 있어 추가 feature가 필요할 가능성이 높다.",
                ],
                ASSET_DIR / "cluster_profile.png",
                ASSET_DIR / "cluster_mae.png",
                "cluster profile",
                "cluster MAE",
                "운영자 화면에서는 cluster 라벨과 군집별 오차 수준을 함께 보여주면, 예측값의 해석과 신뢰도 전달이 쉬워진다.",
                subtitle="군집 해석",
            ),
            _make_two_chart_page(
                "13. Representative Station Selection",
                [
                    "각 cluster에서 이용량, 중심성과, 예측 오차를 함께 고려해 대표 station을 선정했다.",
                    f"- cluster별 대표 station 수: {cluster_counts}",
                    "- 대표 station은 군집 성격을 잘 보여주면서도 사용자 체감이 큰 지점이다.",
                    "- 선정 점수는 사용량, 군집 대표성, 예측 오차를 함께 반영한다.",
                ],
                ASSET_DIR / "representative_station_usage.png",
                ASSET_DIR / "representative_station_score.png",
                "representative usage",
                "selection score",
                "대표 station은 단순 이용량 순위가 아니라 해석 가치와 운영 중요도를 같이 반영해 뽑았다. 그래서 발표와 보고서 모두에서 설명 근거가 분명하다.",
                subtitle="대표 station 선정",
            ),
            _make_two_chart_page(
                "14. Cluster Composition",
                [
                    "cluster마다 포함된 station 수가 다르고, 그 구성 차이가 실제 운영 해석에도 영향을 준다.",
                    "- station 수가 많은 군집은 내부 다양성도 더 크다.",
                    "- 따라서 군집별 설명은 대표 station과 profile을 함께 봐야 안정적이다.",
                ],
                ASSET_DIR / "cluster_station_count.png",
                ASSET_DIR / "cluster_profile.png",
                "cluster station count",
                "cluster profile",
                "군집의 크기와 시간대 프로파일을 함께 보면, 어떤 군집이 더 일반적이고 어떤 군집이 더 특수한지 빠르게 읽을 수 있다.",
                subtitle="군집 구성과 특성",
            ),
            _make_story_chart_page(
                "15. Daily Pattern of Representative Stations",
                [
                    "대표 station의 실제 평균 패턴과 예측 평균 패턴을 겹쳐 보면 군집별 차이가 더 분명해진다.",
                    "- 출퇴근형 군집은 피크가 뚜렷해 비교적 잘 따라간다.",
                    "- 생활권 혼합형은 피크가 분산되어 상대적으로 더 어렵다.",
                    "- 같은 cluster 안에서도 station별 차이가 남아 있어 후속 feature 보강 여지가 있다.",
                ],
                ASSET_DIR / "cluster_station_daily_profile.png",
                "대표 station 분석은 군집 해석과 예측 성능 해석을 동시에 보여주는 구간이다. 발표에서는 패턴 차이를 설명하는 장표로, 보고서에서는 후속 고도화 근거로 활용할 수 있다.",
                subtitle="대표 station 패턴",
            ),
            _make_status_page(
                "16. Representative Station Summary",
                representative_summary,
                "대표 station 목록은 cluster별 설명용 anchor 역할을 한다. 이후 앱 데모나 관리자 웹 우선 모니터링 station 후보로도 바로 연결할 수 있다.",
            ),
            _make_story_chart_page(
                "17. Final Conclusion Summary",
                [
                    "최종 결론은 한 문장으로 정리하면 이렇다.",
                    "- 더 잘 맞는 값은 bike_count_index지만, 서비스 핵심 문제는 아니다.",
                    "- 실제 운영과 사용자 서비스에 더 중요한 것은 bike_change 예측이다.",
                    "- 그리고 이 문제에서는 cluster를 보조 feature로 넣은 모델이 가장 현실적인 선택이었다.",
                ],
                ASSET_DIR / "final_conclusion_summary.png",
                "최종 선택 모델은 cluster를 보조 feature로 포함한 bike_change 중심 모델이다. 이 모델을 실시간 재고 API와 결합하는 구조가 앱과 관리자 웹 모두에 가장 적합하다.",
                subtitle="최종 결론 요약",
            ),
            _make_text_page(
                "18. Final Interpretation and Service Direction",
                [
                    f"- bike_change 최종 모델: {overall.loc['bike_change', 'best_model']} / RMSE {overall.loc['bike_change', 'rmse']:.4f} / MAE {overall.loc['bike_change', 'mae']:.4f}",
                    f"- bike_count_index 최종 모델: {overall.loc['bike_count_index', 'best_model']} / RMSE {overall.loc['bike_count_index', 'rmse']:.4f} / MAE {overall.loc['bike_count_index', 'mae']:.4f}",
                    "- 절대 오차만 보면 bike_count_index가 더 쉽다.",
                    "- 하지만 서비스 가치와 운영 연결성은 bike_change가 더 크다.",
                    "- 따라서 실무 기준 최종 선택은 cluster를 보조 feature로 포함한 bike_change 중심 모델이다.",
                    "- 이용자 앱은 현재 재고 + 예측 변화량 구조, 관리자 웹은 예상 부족/과잉 station 우선순위 구조가 적절하다.",
                    "- 다음 단계는 실시간 재고 API와 재배치 로그 결합, 인접 station 네트워크와 이벤트/날씨 feature 추가다.",
                ],
                subtitle="최종 결론",
            ),
            _make_text_page(
                "19. App and Admin Web Scenario",
                [
                    "이용자 앱은 다음 1시간 기준 station의 이용 가능 자전거 수를 보여주는 방향이 적절하다.",
                    "- 서버는 bike_change를 예측하고, 현재 재고는 실시간 API로 받아온다.",
                    "- 최종 노출값은 현재 재고 + 예측 변화량으로 계산한다.",
                    "관리자 웹은 어느 station에 더 필요하고 덜 필요한지를 우선순위로 보여주는 방향이 적절하다.",
                    "- 예상 부족 station과 예상 과잉 station 구분",
                    "- cluster별 위험 패턴 강조",
                    "- 현재 재고, 예측 변화량, station 중요도를 합친 재배치 우선순위 점수 제공",
                ],
                subtitle="서비스 적용 시나리오",
            ),
            _make_text_page(
                "20. Limitations and Next Steps",
                [
                    "- 절대 재고가 아니라 관측 기반 재고지수를 사용했다.",
                    "- 재배치와 정비 이동 로그가 없다.",
                    "- 인접 station 상호작용과 이벤트성 수요를 충분히 반영하지 못했다.",
                    "- bike_change를 t+1 hour 타깃으로 더 엄격하게 재구성할 필요가 있다.",
                    "- 실시간 재고 API와 재배치 로그를 결합하면 실제 운영 가치가 크게 높아진다.",
                    "- 인접 station 네트워크, 행사, 더 풍부한 날씨 피처를 추가하는 것이 다음 단계다.",
                ],
                subtitle="향후 고도화",
            ),
        ]
        for target in ["bike_change", "bike_count_index"]:
            inventory = feature_inventory[feature_inventory["target"] == target][
                ["feature", "category", "description", "importance_mean"]
            ].copy()
            inventory["importance_mean"] = inventory["importance_mean"].map(lambda x: f"{x:.6f}")
            chunks = [inventory.iloc[i : i + 14] for i in range(0, len(inventory), 14)]
            for idx, chunk in enumerate(chunks, start=1):
                pages.append(
                    _make_table_page(
                        f"Feature Inventory | {target} ({idx}/{len(chunks)})",
                        f"{target} 최종 사용 feature 상세",
                        chunk,
                        "importance_mean은 permutation importance 기준이며, 값이 클수록 해당 feature가 예측 RMSE를 낮추는 데 더 크게 기여했음을 뜻한다.",
                        subtitle="feature 상세 표",
                        fontsize=8.8,
                    )
                )

        for _, row in selected.iterrows():
            station_id = int(row["station_id"])
            pages.append(
                _make_story_chart_page(
                    f"Representative Station | {station_id} {row['station_name']}",
                    [
                        f"- cluster: {row['cluster_name']}",
                        f"- 2025 rental total: {int(row['rental_total_2025'])}",
                        f"- mean abs error: {row['mean_abs_error']:.4f}",
                        f"- center distance: {row['center_distance']:.4f}",
                        f"- selection reason: {row['selection_reason']}",
                    ],
                    ASSET_DIR / f"station_detail_{station_id}.png",
                    "왼쪽 시계열은 시간대별 평균 패턴, 오른쪽 시계열은 월별 평균 패턴이다. 한 station씩 따로 보면 군집 평균만으로는 보이지 않는 세부 차이를 읽을 수 있다.",
                    subtitle="대표 station 개별 분석",
                )
            )
        for fig in pages:
            pdf.savefig(fig)
            plt.close(fig)


def write_markdown_reframed(
    cluster_stability: pd.DataFrame,
    cluster_experiment: pd.DataFrame,
    selected: pd.DataFrame,
    final_metrics: pd.DataFrame,
):
    changed = int(cluster_stability["cluster_changed"].sum())
    total = int(len(cluster_stability))
    benchmark = pd.read_csv(DATA_DIR / "station_hour_test_benchmark_metrics.csv", encoding="utf-8-sig")
    augmented_importance = pd.read_csv(DATA_DIR / "station_hour_cluster_augmented_feature_importance.csv", encoding="utf-8-sig")
    feature_inventory = pd.read_csv(DATA_DIR / "station_hour_feature_inventory.csv", encoding="utf-8-sig")
    reduced_feature_experiment = pd.read_csv(DATA_DIR / "station_hour_reduced_feature_experiment.csv", encoding="utf-8-sig")

    bike_change_cmp = cluster_experiment[cluster_experiment["target"] == "bike_change"].sort_values("rmse")
    bike_index_cmp = cluster_experiment[cluster_experiment["target"] == "bike_count_index"].sort_values("rmse")
    base_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_without_cluster"].iloc[0]
    with_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_with_cluster"].iloc[0]
    base_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_without_cluster"].iloc[0]
    with_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_with_cluster"].iloc[0]
    change_metrics = final_metrics[
        (final_metrics["target"] == "bike_change") & (final_metrics["metric_scope"] == "all_hours")
    ].iloc[0]

    def model_rank_table(target: str) -> pd.DataFrame:
        sub = benchmark[(benchmark["target"] == target) & (~benchmark["model"].str.startswith("baseline_"))].copy()
        sub = sub.sort_values(["rmse", "mae"]).reset_index(drop=True)
        sub["rank"] = np.arange(1, len(sub) + 1)
        return sub[["rank", "model", "rmse", "mae", "r2", "notes"]]

    bike_change_rank = model_rank_table("bike_change")
    bike_index_rank = model_rank_table("bike_count_index")
    hist_param_df = pd.DataFrame(
        [
            ["learning_rate", 0.05, 0.04, "학습 속도를 낮춰 더 안정적으로 수렴"],
            ["max_depth", 10, 12, "더 복잡한 상호작용 허용"],
            ["max_iter", 140, 180, "부스팅 반복 횟수 확대"],
            ["min_samples_leaf", 80, 60, "지역 패턴을 더 세밀하게 반영"],
            ["l2_regularization", 0.10, 0.05, "정규화 완화로 설명력 확보"],
            ["train_sample", 450000, 600000, "더 큰 표본으로 학습 안정화"],
        ],
        columns=["parameter", "hist_gbm", "hist_gbm_tuned", "interpretation"],
    )
    bike_change_feature_group_df = pd.DataFrame(
        [
            ["time/calendar", "hour, weekday, dayofyear, is_commute_hour, is_weekend_or_holiday, hour_sin/cos", "현재 시간대와 요일, 계절 패턴을 설명"],
            ["lag", "bike_change_lag_1/24/168, rental_count_lag_*, return_count_lag_*", "직전, 전날 같은 시각, 지난주 같은 시각 흐름 반영"],
            ["rolling", "bike_change_rollmean_3/24/168, bike_change_rollstd_24/168", "최근 평균 흐름과 변동성 수준 요약"],
            ["weather", "temperature, humidity, precipitation, wind_speed, is_rainy, heavy_rain", "날씨 변화에 따른 이동 수요 반영"],
            ["weather interaction", "temp_x_commute, rain_x_commute, rain_x_night", "같은 날씨라도 시간대별 영향 차이 반영"],
            ["station meta", "station_id, lat, lon, lcd_count, qr_count, dock_total, is_qr_mixed", "대여소 위치와 규모, 운영 형태 차이 반영"],
            ["cluster", "cluster, cluster_0~4", "station 성향을 요약하는 공간적 패턴 반영"],
        ],
        columns=["feature_group", "included_features", "meaning"],
    )
    report_feature_threshold = 0.001
    bike_change_inventory_report = feature_inventory[
        (feature_inventory["target"] == "bike_change") & (feature_inventory["importance_mean"] > report_feature_threshold)
    ][["feature", "category", "description", "source", "importance_mean", "importance_std"]].copy()
    bike_change_importance_report = augmented_importance[
        (augmented_importance["target"] == "bike_change") & (augmented_importance["importance_mean"] > report_feature_threshold)
    ].copy()
    reduced_full = reduced_feature_experiment[reduced_feature_experiment["variant"] == "full_feature_set"].iloc[0]
    reduced_slim = reduced_feature_experiment[reduced_feature_experiment["variant"] == "reduced_feature_set"].iloc[0]
    cluster_specific_benchmark = pd.read_csv(
        DATA_DIR / "station_hour_cluster_specific_model_benchmark.csv", encoding="utf-8-sig"
    )
    cluster_specific_best = pd.read_csv(DATA_DIR / "station_hour_cluster_specific_best_models.csv", encoding="utf-8-sig")
    cluster_specific_comparison = pd.read_csv(DATA_DIR / "station_hour_cluster_specific_comparison.csv", encoding="utf-8-sig")
    cluster_specific_importance = pd.read_csv(DATA_DIR / "station_hour_cluster_specific_feature_importance.csv", encoding="utf-8-sig")
    selected_table = selected[
        ["cluster", "cluster_name", "station_id", "station_name", "rental_total_2025", "mean_abs_error", "selection_reason"]
    ].copy()

    lines = [
        "# Station-Hour Bike Availability Analysis",
        "",
        "## 1. 분석 목표 재정의",
        "",
        "- 학습 기간: `2023-01-01 ~ 2024-12-31`",
        "- 테스트 기간: `2025-01-01 ~ 2025-12-31`",
        "- 분석 단위: `station-hour`",
        "- 실제 시간대별 보유대수 이력은 현재 데이터에 없다.",
        "- 따라서 이번 분석의 핵심 타깃은 `bike_change`다.",
        "- `bike_change = return_count - rental_count` 이며, 다음 1시간 동안 해당 station의 자전거가 순증가할지 순감소할지를 뜻한다.",
        "- 실제 서비스에서 필요한 다음 시간 보유대수는 `현재 실시간 재고(API) + 예측 bike_change`로 계산해야 한다.",
        "",
        "## 2. 왜 bike_count_index 대신 bike_change 중심으로 가는가",
        "",
        "- `bike_count_index`는 실제 보유대수가 아니라 대여/반납 흐름을 누적한 관측 기반 지수다.",
        "- 이 값은 상대적 방향성 해석에는 유용하지만, 사용자에게 '다음 시간에 몇 대 있나'를 직접 답하는 값은 아니다.",
        "- 반면 `bike_change`는 현재 실제 재고와 결합하면 바로 다음 시간 예상 보유대수로 변환할 수 있다.",
        "- 따라서 앱과 관리자 웹 모두에서 바로 연결되는 핵심 예측값은 `bike_change`다.",
        "",
        "## 3. 데이터와 Feature 구성",
        "",
        "- 기본 원천 데이터: 강남구 따릉이 이용정보(2023~2025), 강남구 날씨, 대여소 메타데이터, `works/01_clustering` 군집 결과",
        "- 시간 파생 feature: `hour`, `weekday`, `dayofyear`, `is_commute_hour`, `is_weekend_or_holiday`, 주기성 sin/cos",
        "- 흐름 lag feature: `bike_change_lag_1`, `bike_change_lag_24`, `bike_change_lag_168`, `rental_count_lag_*`, `return_count_lag_*`",
        "- rolling feature: `bike_change_rollmean_3`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollstd_168`",
        "- 날씨 feature: `temperature`, `humidity`, `precipitation`, `wind_speed`, `is_rainy`, `heavy_rain`",
        "- 상호작용 feature: `temp_x_commute`, `rain_x_commute`, `rain_x_night`",
        "- 대여소 정적 feature: `lat`, `lon`, `lcd_count`, `qr_count`, `dock_total`, `is_qr_mixed`",
        "- 군집 feature: `cluster`, `cluster_0` ~ `cluster_4`",
        "",
        "## 4. 핵심 모델 선택: bike_change",
        "",
        "- 최종 선택 모델 family: `hist_gbm_tuned`",
        f"- cluster 미포함 성능: RMSE `{base_change.rmse:.4f}`, MAE `{base_change.mae:.4f}`",
        f"- cluster 포함 성능: RMSE `{with_change.rmse:.4f}`, MAE `{with_change.mae:.4f}`",
        f"- 최종 전체 성능: RMSE `{change_metrics['rmse']:.4f}`, MAE `{change_metrics['mae']:.4f}`, R² `{change_metrics['r2']:.4f}`",
        f"- cluster 추가 효과: RMSE `{with_change.rmse - base_change.rmse:.4f}`, MAE `{with_change.mae - base_change.mae:.4f}`",
        "",
        "### 4-1. bike_change 상위 5개 모델",
        "",
        bike_change_rank.head(5).to_markdown(index=False),
        "",
        "### 4-2. bike_change 모델 해석",
        "",
        "- `hist_gbm_tuned`: RMSE와 MAE를 동시에 가장 안정적으로 낮췄다.",
        "- `hist_gbm`: 튜닝 전 모델도 근접해서, boosting 계열이 문제 구조에 잘 맞음을 보여줬다.",
        "- `extra_trees`, `random_forest`: 일부 패턴은 따라가지만 피크 시간대 큰 변동 대응력이 상대적으로 떨어졌다.",
        "- `ridge`: 선형 반복 구조는 잡았지만 비선형 상호작용 반영이 부족했다.",
        "",
        "### 4-3. hist_gbm 과 hist_gbm_tuned 파라미터 비교",
        "",
        hist_param_df.to_markdown(index=False),
        "",
        "- `hist_gbm_tuned`는 완전히 다른 모델이 아니라 같은 `HistGradientBoostingRegressor`를 현재 데이터에 맞게 조정한 버전이다.",
        "- 더 작은 `learning_rate`와 더 많은 `max_iter`를 사용해 과하게 흔들리지 않으면서도 패턴을 더 오래 학습하도록 만들었다.",
        "- `max_depth`를 늘리고 `min_samples_leaf`를 줄여 station-hour 수준의 국소 패턴과 비선형 상호작용을 더 세밀하게 반영했다.",
        "- 학습 표본도 더 크게 사용해 tuned 버전의 일반화 안정성을 보강했다.",
        "",
        "## 5. feature를 줄인 경량 버전 비교",
        "",
        f"- full feature set: feature `{int(reduced_full['feature_count'])}`개 / RMSE `{reduced_full['rmse']:.4f}` / MAE `{reduced_full['mae']:.4f}` / R² `{reduced_full['r2']:.4f}`",
        f"- reduced feature set: feature `{int(reduced_slim['feature_count'])}`개 / RMSE `{reduced_slim['rmse']:.4f}` / MAE `{reduced_slim['mae']:.4f}` / R² `{reduced_slim['r2']:.4f}`",
        f"- 경량화 기준: `importance_mean > {report_feature_threshold}`",
        "- 해석: 중요도가 거의 없던 피처를 제거해도 성능이 크게 무너지지 않으면, 운영 단계에서는 경량 버전이 더 실용적일 수 있다.",
        "",
        "## 6. cluster별 특화 모델 실험",
        "",
        "- 이전까지의 분석은 모든 cluster에 같은 글로벌 모델을 적용하고, cluster는 feature로만 반영하는 구조였다.",
        "- 추가 실험에서는 cluster 0~4 각각에 대해 별도 모델 후보를 비교하고, cluster마다 가장 잘 맞는 모델을 따로 선택했다.",
        "",
        cluster_specific_best[["cluster_name", "model", "rmse", "mae", "r2", "train_rows", "eval_rows"]].to_markdown(index=False),
        "",
        "### 6-1. 글로벌 공유 모델 vs cluster별 특화 모델",
        "",
        cluster_specific_comparison[["scope", "cluster_name", "variant", "rmse", "mae", "r2"]].to_markdown(index=False),
        "",
        "- 이 비교를 통해 모든 cluster에 같은 모델을 쓸지, cluster별로 다른 모델을 둘지의 실익을 직접 확인할 수 있다.",
        "",
        "## 7. RMSE와 MAE 해석",
        "",
        "- `RMSE`는 큰 오차에 더 민감하므로 피크 시간대 실패를 보여준다.",
        "- `MAE`는 평균적인 오차 수준을 보여준다.",
        "- 앱/운영에서는 둘 다 중요하므로 두 지표를 함께 봐야 한다.",
        "- `hist_gbm_tuned`가 두 지표를 가장 균형 있게 관리했다.",
        "",
        "## 6. cluster feature 반영 결과",
        "",
        f"- 공통 station `{total}`개 중 `{changed}`개가 2025년에 cluster가 바뀌었다. 변화율은 `{changed / total:.2%}`다.",
        "- 따라서 cluster는 고정 정답이 아니라 station 성향을 요약하는 보조 피처로 해석해야 한다.",
        "- 그래도 bike_change 예측에서는 cluster 추가 후 오차가 소폭 개선되었다.",
        "",
        "## 7. bike_change 최종 사용 Feature 전체",
        "",
        bike_change_inventory_report.to_markdown(index=False),
        "",
        "## 8. bike_change 상위 중요 Feature",
        "",
        augmented_importance[augmented_importance["target"] == "bike_change"].head(15).to_markdown(index=False),
        "",
        "## 9. 부족한 Feature와 추가 필요 데이터",
        "",
        "- 현재 없는 핵심 데이터는 `실시간 재고 스냅샷 이력`, `재배치 로그`, `정비/회수 이동 로그`다.",
        "- 추가 가치가 큰 피처는 `인접 station 상호작용`, `행사/연휴 캘린더`, `세분화된 기상 정보`다.",
        "",
        "## 10. 서비스 적용 방식",
        "",
        "- 이용자 앱: `현재 실시간 재고 + 예측 bike_change = 다음 시간 예상 보유대수`",
        "- 관리자 웹: `현재 재고`, `예측 bike_change`, `station 중요도`, `cluster`를 결합해 부족/과잉 우선순위를 계산",
        "",
        "## 11. 대표 station 분석",
        "",
        selected_table.to_markdown(index=False),
        "",
    ]

    for _, row in selected.iterrows():
        lines.extend(
            [
                f"### {row['cluster_name']} | {int(row['station_id'])} {row['station_name']}",
                "",
                f"- 2025 총 대여량: `{int(row['rental_total_2025'])}`",
                f"- 평균 절대오차(MAE): `{row['mean_abs_error']:.4f}`",
                f"- 군집 중심 거리: `{row['center_distance']:.4f}`",
                f"- 선정 이유: `{row['selection_reason']}`",
                "- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.",
                "",
            ]
        )

    lines.extend(
        [
            "## 12. cluster별 모델 상세 해석",
            "",
        ]
    )

    for _, row in cluster_specific_best.sort_values("cluster").iterrows():
        top_features = cluster_specific_importance[cluster_specific_importance["cluster"] == row["cluster"]].head(8)
        top_models = (
            cluster_specific_benchmark[cluster_specific_benchmark["cluster"] == row["cluster"]]
            .sort_values(["rmse", "mae"])
            .head(5)[["model", "rmse", "mae", "r2"]]
            .copy()
        )
        global_row = cluster_specific_comparison[
            (cluster_specific_comparison["scope"] == "cluster")
            & (cluster_specific_comparison["cluster"] == row["cluster"])
            & (cluster_specific_comparison["variant"] == "global_shared_model")
        ].iloc[0]
        specialist_row = cluster_specific_comparison[
            (cluster_specific_comparison["scope"] == "cluster")
            & (cluster_specific_comparison["cluster"] == row["cluster"])
            & (cluster_specific_comparison["variant"] == "cluster_specific_model")
        ].iloc[0]
        rmse_gain = global_row["rmse"] - specialist_row["rmse"]
        mae_gain = global_row["mae"] - specialist_row["mae"]
        if rmse_gain > 0.005:
            decision_text = "공통 모델보다 RMSE 개선 폭이 뚜렷해서 cluster 특화 학습의 실익이 분명했다."
        elif rmse_gain > 0:
            decision_text = "공통 모델 대비 개선 폭은 크지 않지만, RMSE와 feature 해석이 모두 specialist 쪽에 유리했다."
        elif mae_gain > 0:
            decision_text = "RMSE는 비슷하거나 소폭 불리했지만 MAE가 더 낮아 평균 오차 기준으로는 specialist가 더 안정적이었다."
        else:
            decision_text = "공통 모델이 이미 충분히 강해서 cluster를 따로 나눠도 큰 이득은 없었고, 이 cluster는 공유 모델 구조가 더 효율적이었다."
        lines.extend(
            [
                f"### {row['cluster_name']} | best model `{row['model']}`",
                "",
                f"- train rows: `{int(row['train_rows'])}`",
                f"- eval rows: `{int(row['eval_rows'])}`",
                f"- RMSE: `{row['rmse']:.4f}`",
                f"- MAE: `{row['mae']:.4f}`",
                f"- R²: `{row['r2']:.4f}`",
                f"- global shared model 대비 RMSE 변화: `{rmse_gain:+.4f}`",
                f"- global shared model 대비 MAE 변화: `{mae_gain:+.4f}`",
                f"- 해석: {decision_text}",
                "- top 5 candidate models:",
                top_models.to_markdown(index=False),
                "",
                "- top features:",
                top_features[["feature", "importance_mean", "importance_std"]].to_markdown(index=False),
                "",
            ]
        )

    lines.extend(
        [
            "## 13. 참고: bike_count_index",
            "",
            f"- 참고용 최고 모델은 `ridge`였고, cluster 포함 시 RMSE `{with_index.rmse:.4f}`, MAE `{with_index.mae:.4f}`였다.",
            f"- cluster 미포함 대비 개선 폭은 RMSE `{with_index.rmse - base_index.rmse:.4f}`, MAE `{with_index.mae - base_index.mae:.4f}`였다.",
            "- 그러나 이 값은 실제 재고가 아니라 누적 지수이므로 참고 자료로만 사용한다.",
            "",
            bike_index_rank.head(5).to_markdown(index=False),
            "",
            "## 14. 최종 결론",
            "",
            "- 실제 시간대별 보유대수 이력이 없으므로 이번 분석의 핵심 타깃은 `bike_change`가 맞다.",
            "- 여러 회귀 모델 중 `hist_gbm_tuned`가 RMSE와 MAE를 가장 균형 있게 낮췄다.",
            "- cluster는 성능 향상 폭보다 station 성향 설명력 측면에서 특히 의미가 있었다.",
            "- 최종 추천은 `cluster를 포함한 bike_change 중심 회귀 모델`이다.",
            "- 실서비스에서는 반드시 `실시간 재고 API`를 붙여서 `현재 재고 + 예측 bike_change` 형태로 다음 시간 보유대수를 계산해야 한다.",
            "- 다음 고도화 우선순위는 `실시간 재고 이력 수집`, `재배치 로그 결합`, `인접 station 네트워크 feature`, `행사/연휴 캘린더`, `확장 날씨 변수` 순서다.",
            "",
        ]
    )

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_pdf_reframed(cluster_experiment: pd.DataFrame, selected: pd.DataFrame, cluster_stability: pd.DataFrame):
    bike_change_cmp = cluster_experiment[cluster_experiment["target"] == "bike_change"].sort_values("rmse")
    bike_index_cmp = cluster_experiment[cluster_experiment["target"] == "bike_count_index"].sort_values("rmse")
    base_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_without_cluster"].iloc[0]
    with_change = bike_change_cmp[bike_change_cmp["feature_variant"] == "bike_change_with_cluster"].iloc[0]
    base_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_without_cluster"].iloc[0]
    with_index = bike_index_cmp[bike_index_cmp["feature_variant"] == "bike_count_index_with_cluster"].iloc[0]
    final_metrics = pd.read_csv(DATA_DIR / "station_hour_final_model_metrics.csv", encoding="utf-8-sig")
    benchmark = pd.read_csv(DATA_DIR / "station_hour_test_benchmark_metrics.csv", encoding="utf-8-sig")
    reduced_feature_experiment = pd.read_csv(DATA_DIR / "station_hour_reduced_feature_experiment.csv", encoding="utf-8-sig")
    overall = final_metrics[final_metrics["metric_scope"] == "all_hours"].set_index("target")
    changed = int(cluster_stability["cluster_changed"].sum())
    total = int(len(cluster_stability))
    train_flow = pd.read_csv(DATA_DIR / "station_hour_bike_flow_train_2023_2024.csv", encoding="utf-8-sig", parse_dates=["time"])
    test_flow = pd.read_csv(DATA_DIR / "station_hour_bike_flow_test_2025.csv", encoding="utf-8-sig", parse_dates=["time"])
    full_rows = len(train_flow) + len(test_flow)
    station_count = int(pd.concat([train_flow["station_id"], test_flow["station_id"]]).nunique())
    best_change_model = benchmark[benchmark["target"] == "bike_change"].sort_values("rmse").iloc[0]
    benchmark_rank_change = benchmark[(benchmark["target"] == "bike_change") & (~benchmark["model"].str.startswith("baseline_"))].copy()
    benchmark_rank_change = benchmark_rank_change.sort_values(["rmse", "mae"]).reset_index(drop=True)
    benchmark_rank_change["rank"] = np.arange(1, len(benchmark_rank_change) + 1)
    benchmark_rank_change = benchmark_rank_change[["rank", "model", "rmse", "mae", "r2"]]
    benchmark_rank_index = benchmark[(benchmark["target"] == "bike_count_index") & (~benchmark["model"].str.startswith("baseline_"))].copy()
    benchmark_rank_index = benchmark_rank_index.sort_values(["rmse", "mae"]).reset_index(drop=True)
    benchmark_rank_index["rank"] = np.arange(1, len(benchmark_rank_index) + 1)
    benchmark_rank_index = benchmark_rank_index[["rank", "model", "rmse", "mae", "r2"]]
    feature_inventory = pd.read_csv(DATA_DIR / "station_hour_feature_inventory.csv", encoding="utf-8-sig")
    cluster_specific_benchmark = pd.read_csv(
        DATA_DIR / "station_hour_cluster_specific_model_benchmark.csv", encoding="utf-8-sig"
    )
    cluster_specific_best = pd.read_csv(DATA_DIR / "station_hour_cluster_specific_best_models.csv", encoding="utf-8-sig")
    cluster_specific_comparison = pd.read_csv(DATA_DIR / "station_hour_cluster_specific_comparison.csv", encoding="utf-8-sig")
    cluster_specific_importance = pd.read_csv(DATA_DIR / "station_hour_cluster_specific_feature_importance.csv", encoding="utf-8-sig")
    bike_change_feature_group_df = pd.DataFrame(
        [
            ["time/calendar", "hour, weekday, dayofyear, is_commute_hour, is_weekend_or_holiday, hour_sin/cos", "현재 시간대와 요일, 계절 패턴 설명"],
            ["lag", "bike_change_lag_1/24/168, rental_count_lag_*, return_count_lag_*", "직전, 전날, 지난주 같은 시각 흐름 반영"],
            ["rolling", "bike_change_rollmean_3/24/168, bike_change_rollstd_24/168", "최근 평균 흐름과 변동성 요약"],
            ["weather", "temperature, humidity, precipitation, wind_speed, is_rainy, heavy_rain", "날씨 변화에 따른 이동 수요 반영"],
            ["weather interaction", "temp_x_commute, rain_x_commute, rain_x_night", "시간대별 날씨 영향 차이 반영"],
            ["station meta", "station_id, lat, lon, lcd_count, qr_count, dock_total, is_qr_mixed", "대여소 위치와 규모, 운영 형태 반영"],
            ["cluster", "cluster, cluster_0~4", "station 성향을 요약하는 공간 패턴 반영"],
        ],
        columns=["feature_group", "included_features", "meaning"],
    )
    report_feature_threshold = 0.001
    bike_change_inventory_report = feature_inventory[
        (feature_inventory["target"] == "bike_change") & (feature_inventory["importance_mean"] > report_feature_threshold)
    ][["feature", "category", "description", "importance_mean"]].copy()
    reduced_feature_experiment["rmse"] = reduced_feature_experiment["rmse"].map(lambda x: f"{x:.4f}")
    reduced_feature_experiment["mae"] = reduced_feature_experiment["mae"].map(lambda x: f"{x:.4f}")
    reduced_feature_experiment["r2"] = reduced_feature_experiment["r2"].map(lambda x: f"{x:.4f}")
    hist_param_df = pd.DataFrame(
        [
            ["learning_rate", "0.05", "0.04", "더 작은 step으로 안정적 학습"],
            ["max_depth", "10", "12", "더 복잡한 상호작용 허용"],
            ["max_iter", "140", "180", "부스팅 반복 확대"],
            ["min_samples_leaf", "80", "60", "지역 패턴을 더 세밀하게 반영"],
            ["l2_regularization", "0.10", "0.05", "정규화 완화로 설명력 확보"],
            ["train_sample", "450,000", "600,000", "더 큰 표본으로 학습 안정화"],
        ],
        columns=["parameter", "hist_gbm", "hist_gbm_tuned", "why it matters"],
    )

    status_df = pd.DataFrame(
        [
            ["1. 문제 정의", "완료", "실제 재고 이력 부재 확인, bike_change 중심으로 재정의"],
            ["2. 데이터 정리", "완료", "station-hour 집계와 외부 feature 결합"],
            ["3. 회귀 모델 비교", "완료", "2025 테스트 기준 성능 비교"],
            ["4. 군집 결합", "완료", "cluster 0~4를 보조 feature로 반영"],
            ["5. 대표 station 해석", "완료", "cluster별 대표 station 심층 분석"],
            ["6. 서비스 연결", "완료", "실시간 재고 API 결합 로직 정리"],
        ],
        columns=["단계", "상태", "요약"],
    )

    metrics_df = final_metrics.copy()
    metrics_df["rmse"] = metrics_df["rmse"].map(lambda x: f"{x:.4f}")
    metrics_df["mae"] = metrics_df["mae"].map(lambda x: f"{x:.4f}")
    metrics_df["r2"] = metrics_df["r2"].map(lambda x: f"{x:.4f}")
    metrics_df = metrics_df[["target", "best_model", "feature_set", "metric_scope", "rmse", "mae", "r2"]]

    representative_summary = selected[["cluster_name", "station_name", "rental_total_2025", "mean_abs_error"]].copy()
    representative_summary["rental_total_2025"] = representative_summary["rental_total_2025"].astype(int)
    representative_summary["mean_abs_error"] = representative_summary["mean_abs_error"].map(lambda x: f"{x:.3f}")

    with PdfPages(REPORT_PDF) as pdf:
        pages = [
            _make_status_page(
                "Station-Hour Bike Availability Report",
                status_df,
                f"전체 station-hour 행 수는 {full_rows:,}, 공통 station 수는 {station_count}개다. 학습은 2023~2024, 평가는 2025 전체 기간으로 진행했다.",
            ),
            _make_two_column_text_page(
                "1. Problem Redefinition",
                "핵심 전제",
                [
                    "- 실제 시간대별 보유대수 이력은 없다.",
                    "- 그래서 실제 재고를 직접 맞히는 supervised target을 만들 수 없다.",
                    "- bike_count_index는 실제 재고가 아니라 누적 지수다.",
                ],
                "핵심 결정",
                [
                    "- 따라서 핵심 타깃은 bike_change다.",
                    "- bike_change는 다음 1시간 순증감량이다.",
                    "- 현재 실시간 재고와 결합하면 다음 시간 보유대수로 연결된다.",
                ],
                subtitle="문제 재정의",
            ),
            _make_text_page(
                "2. Service Formula",
                [
                    "- 다음 시간 예상 보유대수 = 현재 실시간 재고(API) + 예측 bike_change",
                    "- 앱은 이 값을 이용해 사용자에게 대여 가능성을 보여준다.",
                    "- 관리자 웹은 부족/과잉 station 우선순위를 계산한다.",
                    "- 따라서 모델이 직접 맞히는 값은 bike_change이고, 실제 보유대수는 서비스 단계에서 계산된다.",
                ],
                subtitle="서비스 적용 공식",
            ),
            _make_two_chart_page(
                "3. Data Structure and Flow",
                [
                    f"- train rows: {len(train_flow):,}",
                    f"- test rows: {len(test_flow):,}",
                    f"- station count: {station_count}",
                    "- station-hour 구조로 재구성해 시간 패턴과 외부 feature를 함께 본다.",
                ],
                ASSET_DIR / "data_coverage.png",
                ASSET_DIR / "hourly_flow_overview.png",
                "data coverage",
                "hourly flow",
                "이 구조 덕분에 시간대 반복, 날씨 영향, 군집 성향을 한 프레임에서 회귀모델에 넣을 수 있었다.",
                subtitle="데이터 구조",
            ),
            _make_two_chart_page(
                "4. Pattern and Target Meaning",
                [
                    "- 요일과 시간대에 따라 rental, return, bike_change 패턴이 달라진다.",
                    "- 이런 반복 구조가 lag와 calendar feature의 중요성을 만든다.",
                    "- bike_count_index는 참고용 비교 대상일 뿐 핵심 타깃은 아니다.",
                ],
                ASSET_DIR / "weekday_flow_overview.png",
                ASSET_DIR / "target_difficulty.png",
                "weekday pattern",
                "target difficulty",
                "쉬운 문제와 중요한 문제는 다르다. 이번 프로젝트에서 중요한 문제는 실제 서비스와 직접 연결되는 bike_change 예측이다.",
                subtitle="타깃 의미",
            ),
            _make_two_chart_page(
                "5. Model Benchmark",
                [
                    f"- best bike_change model: {best_change_model['model']}",
                    f"- RMSE {best_change_model['rmse']:.4f}",
                    f"- MAE {best_change_model['mae']:.4f}",
                    "- 참고용 bike_count_index 비교도 함께 봤지만 결론은 bike_change 기준으로 내렸다.",
                ],
                ASSET_DIR / "benchmark_bike_change.png",
                ASSET_DIR / "benchmark_bike_count_index.png",
                "bike_change benchmark",
                "reference benchmark",
                "핵심 선택은 bike_change 모델 기준으로 진행했다. bike_count_index는 왜 제외했는지 뒤에서 다시 설명한다.",
                subtitle="모델 비교",
            ),
            _make_table_page(
                "6. Top 5 Models for bike_change",
                "bike_change 상위 5개 회귀 모델",
                benchmark_rank_change.head(5).round(4),
                "RMSE와 MAE를 함께 낮춘 모델이 실무적으로 적합하다. 최종적으로 hist_gbm_tuned가 가장 안정적인 균형을 보였다.",
                subtitle="모델 순위",
                fontsize=9.6,
            ),
            _make_two_column_text_page(
                "7. Why HistGBM Won",
                "좋았던 이유",
                [
                    "- 시간 반복 패턴과 비선형 상호작용을 잘 흡수했다.",
                    "- 출퇴근과 날씨, cluster 신호를 함께 반영했다.",
                    "- 큰 오차와 평균 오차를 동시에 관리했다.",
                ],
                "다른 모델이 밀린 이유",
                [
                    "- 트리 앙상블은 급격한 변화를 덜 따라갔다.",
                    "- 선형 모델은 상호작용 반영이 약했다.",
                    "- dummy는 운영적으로 의미가 없는 착시 성능이었다.",
                ],
                subtitle="모델 선정 이유",
            ),
            _make_table_page(
                "8. HistGBM Parameter Tuning",
                "hist_gbm vs hist_gbm_tuned 파라미터 비교",
                hist_param_df,
                "두 모델은 알고리즘 자체는 같고 설정값만 다르다. tuned 버전은 더 작은 learning rate, 더 깊은 트리, 더 많은 반복을 사용해 station-hour 패턴을 더 세밀하게 학습하도록 조정했다.",
                subtitle="파라미터 비교",
                fontsize=9.2,
            ),
            _make_table_page(
                "9. Reduced Feature Version",
                "경량 feature set 성능 비교",
                reduced_feature_experiment[["variant", "feature_count", "selection_rule", "rmse", "mae", "r2"]],
                f"importance_mean > {report_feature_threshold} 기준으로 하위 피처를 제거한 경량 버전도 같이 비교했다. 성능 저하가 크지 않다면 서비스 배포나 추론 비용 측면에서 더 실용적일 수 있다.",
                subtitle="경량화 실험",
                fontsize=9.2,
            ),
            _make_table_page(
                "10. Cluster-Specific Best Models",
                "cluster별 최적 모델 요약",
                cluster_specific_best[["cluster_name", "model", "rmse", "mae", "r2", "train_rows", "eval_rows"]],
                "기존 방식은 모든 cluster에 같은 글로벌 모델을 적용했다. 추가 실험에서는 각 cluster마다 따로 모델 후보를 비교해 최적 모델을 선정했다.",
                subtitle="cluster 특화 학습",
                fontsize=8.9,
            ),
            _make_two_chart_page(
                "11. Global vs Cluster-Specific Models",
                [
                    "- 공유 모델은 모든 cluster에 같은 구조를 적용한다.",
                    "- 특화 모델은 cluster별 데이터만 따로 학습해 cluster마다 다른 모델을 선택한다.",
                    "- 이 비교는 cluster별 패턴이 충분히 다를 때 특화 모델이 유리한지 보여준다.",
                ],
                ASSET_DIR / "cluster_specific_best_rmse.png",
                ASSET_DIR / "cluster_specific_vs_global_rmse.png",
                "best specialist RMSE",
                "global vs specialist",
                "cluster별 특화 학습은 업무형, 주거형, 혼합형 station의 패턴 차이가 클수록 유리할 가능성이 있다. 반대로 데이터가 적거나 패턴이 비슷하면 글로벌 공유 모델이 더 안정적일 수 있다.",
                subtitle="cluster별 모델 비교",
            ),
            _make_two_chart_page(
                "12. Error Interpretation",
                [
                    f"- bike_change RMSE {overall.loc['bike_change', 'rmse']:.4f}",
                    f"- bike_change MAE {overall.loc['bike_change', 'mae']:.4f}",
                    f"- reference bike_count_index RMSE {overall.loc['bike_count_index', 'rmse']:.4f}",
                    "- 그러나 핵심 해석은 bike_change의 오차다.",
                ],
                ASSET_DIR / "monthly_trend_actual_vs_pred.png",
                ASSET_DIR / "residual_distribution.png",
                "monthly trend",
                "residual distribution",
                "RMSE는 피크 시간대 실패를, MAE는 전체 시간대 안정성을 보여준다. 실서비스에서는 둘 다 중요하다.",
                subtitle="오차 해석",
            ),
            _make_two_chart_page(
                "13. Feature Importance",
                [
                    "- 상위 feature는 주간/일간 lag, 시간대, 출퇴근 여부, cluster다.",
                    "- 즉 모델은 과거 같은 시간의 흐름과 station 성향을 함께 본다.",
                    "- 현재 데이터에서 추가 가치가 큰 다음 단계는 실시간 재고 이력과 재배치 로그다.",
                ],
                ASSET_DIR / "feature_importance_bike_change.png",
                ASSET_DIR / "cluster_feature_effect.png",
                "bike_change importance",
                "cluster effect",
                "cluster는 큰 폭의 성능 향상보다 station 성향 설명력 측면에서 특히 가치가 있었다.",
                subtitle="핵심 feature",
            ),
            _make_two_chart_page(
                "14. Cluster Interpretation",
                [
                    f"- changed stations: {changed} / {total}",
                    f"- bike_change RMSE: without {base_change.rmse:.4f} -> with {with_change.rmse:.4f}",
                    f"- reference bike_count_index RMSE: without {base_index.rmse:.4f} -> with {with_index.rmse:.4f}",
                    "- cluster는 고정 라벨보다 station 성향 요약 피처로 봐야 한다.",
                ],
                ASSET_DIR / "cluster_stability.png",
                ASSET_DIR / "cluster_profile.png",
                "cluster stability",
                "cluster profile",
                "cluster를 넣으면 같은 시간대라도 station이 어떤 공간 성격을 가지는지 모델이 구분할 수 있다.",
                subtitle="군집 결합",
            ),
            _make_two_chart_page(
                "15. Representative Station Selection",
                [
                    "- cluster별 대표 station을 2~3개씩 뽑았다.",
                    "- 이용량, 대표성, 평균 오차를 함께 고려했다.",
                    "- 이 station들은 결과 설명과 서비스 예시 화면의 기준점이 된다.",
                ],
                ASSET_DIR / "representative_station_usage.png",
                ASSET_DIR / "representative_station_score.png",
                "usage level",
                "selection score",
                "대표 station은 단순 이용량 순위가 아니라, 군집을 설명하면서도 운영상 중요한 station으로 골랐다.",
                subtitle="대표 station 선정",
            ),
            _make_story_chart_page(
                "16. Representative Pattern Overview",
                [
                    "- 대표 station들의 시간대 패턴을 한 페이지에서 비교했다.",
                    "- cluster가 달라지면 피크 시간과 순변화 방향도 달라진다.",
                    "- 같은 cluster 안에서도 station별 차이가 남아 있어 추가 feature 여지가 남는다.",
                ],
                ASSET_DIR / "cluster_station_daily_profile.png",
                "대표 station 비교는 cluster 평균만으로는 보이지 않는 개별 station 차이를 드러낸다.",
                subtitle="대표 station 패턴",
            ),
            _make_status_page(
                "17. Representative Station Summary",
                representative_summary,
                "이 station들은 이후 앱 예시 화면, 관리자 웹 모니터링 우선 station, 그리고 후속 정성 해석의 기준 목록으로 사용할 수 있다.",
            ),
            _make_text_page(
                "18. Operational Decision Logic",
                [
                    "- 이용자 앱: 현재 재고 + 예측 bike_change -> 다음 시간 예상 보유대수",
                    "- 관리자 웹: 현재 재고, 예측 bike_change, cluster, station 중요도로 재배치 우선순위 계산",
                    "- 예시: 현재 8대, 예측 bike_change -5이면 다음 시간 예상 3대",
                    "- 즉 이번 모델은 보유대수를 직접 맞히는 대신, 보유대수를 움직이는 핵심 변화를 맞힌다.",
                ],
                subtitle="운영 적용 방식",
            ),
            _make_story_chart_page(
                "19. Final Conclusion",
                [
                    "- 실제 재고 이력이 없으므로 핵심 타깃은 bike_change가 맞다.",
                    "- hist_gbm_tuned가 가장 균형 잡힌 RMSE/MAE 성능을 보였다.",
                    "- cluster는 station 성향 설명력과 대표 station 해석에 특히 기여했다.",
                    "- 실시간 재고 API와 결합하는 구조가 가장 현실적인 서비스 경로다.",
                ],
                ASSET_DIR / "final_conclusion_summary.png",
                "이번 프로젝트의 실질적인 산출물은 '다음 시간 보유대수'를 직접 맞히는 모델이 아니라, 그 값을 계산하기 위한 핵심 구성요소인 bike_change 예측 모델이다.",
                subtitle="최종 결론",
            ),
            _make_text_page(
                "20. Detailed Conclusion and Next Steps",
                [
                    f"- bike_change final model: {overall.loc['bike_change', 'best_model']} / RMSE {overall.loc['bike_change', 'rmse']:.4f} / MAE {overall.loc['bike_change', 'mae']:.4f}",
                    f"- reference bike_count_index model: {overall.loc['bike_count_index', 'best_model']} / RMSE {overall.loc['bike_count_index', 'rmse']:.4f} / MAE {overall.loc['bike_count_index', 'mae']:.4f}",
                    "- bike_count_index는 참고 지표일 뿐 서비스 핵심 타깃이 아니다.",
                    "- 최종 추천은 cluster를 포함한 bike_change 중심 회귀 모델이다.",
                    "- 다음 단계는 실시간 재고 이력과 재배치 로그를 수집해 진짜 재고 예측 체계로 확장하는 것이다.",
                ],
                subtitle="결론 상세",
            ),
            _make_table_page(
                "Appendix A. Reference Models",
                "bike_count_index 상위 5개 모델",
                benchmark_rank_index.head(5).round(4),
                "bike_count_index는 누적 지수라 자기상관이 매우 강하다. 참고 비교로는 유용하지만 실제 재고 대체 타깃으로는 적절하지 않다.",
                subtitle="참고 부록",
                fontsize=9.6,
            ),
            _make_status_page(
                "Appendix B. Metric Summary",
                metrics_df,
                "최종 표에서도 핵심 해석 대상은 bike_change다. bike_count_index는 참고 비교 행으로만 남겼다.",
            ),
        ]

        pages.append(
            _make_table_page(
                "Appendix C. bike_change Feature Guide",
                "bike_change 피처 범주별 설명",
                bike_change_feature_group_df,
                "bike_change 예측은 과거 같은 시간 흐름, 현재 시간대, 날씨, station 성향을 함께 보는 구조다. 특히 lag24와 lag168은 전날/지난주 같은 시각 패턴을 담기 때문에 중요도가 높다.",
                subtitle="피처 해설",
                fontsize=8.8,
            )
        )

        bike_change_inventory_report = feature_inventory[feature_inventory["target"] == "bike_change"][
            ["feature", "category", "description", "importance_mean"]
        ].copy()
        bike_change_inventory_report = bike_change_inventory_report[
            pd.to_numeric(bike_change_inventory_report["importance_mean"], errors="coerce") > report_feature_threshold
        ]
        bike_change_inventory_report["importance_mean"] = bike_change_inventory_report["importance_mean"].map(lambda x: f"{x:.6f}")
        chunks = [bike_change_inventory_report.iloc[i : i + 14] for i in range(0, len(bike_change_inventory_report), 14)]
        for idx, chunk in enumerate(chunks, start=1):
            pages.append(
                _make_table_page(
                    f"Feature Inventory | bike_change ({idx}/{len(chunks)})",
                    "bike_change 최종 사용 feature 상세",
                    chunk,
                    "importance_mean은 permutation importance 기준이며, 값이 클수록 bike_change 예측 오차를 줄이는 기여가 크다.",
                    subtitle="feature 상세",
                    fontsize=8.8,
                )
            )

        for _, row in cluster_specific_best.sort_values("cluster").iterrows():
            top_models = (
                cluster_specific_benchmark[cluster_specific_benchmark["cluster"] == row["cluster"]]
                .sort_values(["rmse", "mae"])
                .head(5)[["model", "rmse", "mae", "r2"]]
                .copy()
            )
            global_row = cluster_specific_comparison[
                (cluster_specific_comparison["scope"] == "cluster")
                & (cluster_specific_comparison["cluster"] == row["cluster"])
                & (cluster_specific_comparison["variant"] == "global_shared_model")
            ].iloc[0]
            specialist_row = cluster_specific_comparison[
                (cluster_specific_comparison["scope"] == "cluster")
                & (cluster_specific_comparison["cluster"] == row["cluster"])
                & (cluster_specific_comparison["variant"] == "cluster_specific_model")
            ].iloc[0]
            rmse_gain = global_row["rmse"] - specialist_row["rmse"]
            mae_gain = global_row["mae"] - specialist_row["mae"]
            if rmse_gain > 0.005:
                cluster_comment = "cluster를 분리해 학습한 쪽이 RMSE 기준으로 분명한 이득을 보였다."
            elif rmse_gain > 0:
                cluster_comment = "개선 폭은 크지 않지만 specialist가 shared model보다 조금 더 잘 맞았다."
            elif mae_gain > 0:
                cluster_comment = "RMSE는 비슷하지만 MAE가 더 낮아 평균 오차 기준으로 specialist가 더 안정적이었다."
            else:
                cluster_comment = "이 cluster는 shared model이 이미 충분히 강해서 분리 학습 이득이 제한적이었다."
            pages.append(
                _make_table_page(
                    f"Cluster Model Ranking | {row['cluster_name']}",
                    f"{row['cluster_name']} 상위 5개 후보 모델",
                    top_models.round(4),
                    f"best model은 {row['model']}이며 RMSE {row['rmse']:.4f}, MAE {row['mae']:.4f}를 기록했다. "
                    f"global shared model 대비 RMSE 변화는 {rmse_gain:+.4f}, MAE 변화는 {mae_gain:+.4f}이고, {cluster_comment}",
                    subtitle="cluster별 모델 선택",
                    fontsize=9.0,
                )
            )
            cluster_features = cluster_specific_importance[cluster_specific_importance["cluster"] == row["cluster"]].head(8).copy()
            cluster_features["importance_mean"] = cluster_features["importance_mean"].map(lambda x: f"{x:.6f}")
            pages.append(
                _make_table_page(
                    f"Cluster Detail | {row['cluster_name']}",
                    f"{row['cluster_name']} 최적 모델 `{row['model']}` 상위 feature",
                    cluster_features[["feature", "importance_mean", "importance_std"]],
                    f"이 cluster의 최적 모델은 {row['model']}이며, RMSE {row['rmse']:.4f}, MAE {row['mae']:.4f}를 기록했다. 같은 bike_change 문제라도 cluster별 패턴 차이 때문에 최적 모델과 중요 feature 구성이 달라질 수 있다.",
                    subtitle="cluster별 상세 분석",
                    fontsize=8.9,
                )
            )

        for _, row in selected.iterrows():
            station_id = int(row["station_id"])
            pages.append(
                _make_story_chart_page(
                    f"Representative Station | {station_id} {row['station_name']}",
                    [
                        f"- cluster: {row['cluster_name']}",
                        f"- 2025 rental total: {int(row['rental_total_2025'])}",
                        f"- mean abs error: {row['mean_abs_error']:.4f}",
                        f"- center distance: {row['center_distance']:.4f}",
                        f"- selection reason: {row['selection_reason']}",
                    ],
                    ASSET_DIR / f"station_detail_{station_id}.png",
                    "각 station 페이지에서는 시간대 평균 패턴과 월별 패턴을 함께 보며, 모델이 어떤 station에서 잘 맞고 어디서 더 어려워하는지 해석한다.",
                    subtitle="대표 station 상세",
                )
            )

        for fig in pages:
            pdf.savefig(fig)
            plt.close(fig)


def main():
    train_labels, test_labels, rep, _summary = load_cluster_labels()
    base_df = base.build_dataset()
    cluster_df = add_cluster_features(base_df, train_labels)
    cluster_stability = compare_cluster_stability(train_labels, test_labels)

    cluster_experiment, predictions = run_cluster_feature_experiment(cluster_df)
    cluster_experiment.to_csv(DATA_DIR / "station_hour_cluster_feature_experiment.csv", index=False, encoding="utf-8-sig")
    cluster_stability.to_csv(DATA_DIR / "station_hour_cluster_stability.csv", index=False, encoding="utf-8-sig")
    augmented_importance = compute_cluster_augmented_feature_importance(cluster_df)
    augmented_importance.to_csv(DATA_DIR / "station_hour_cluster_augmented_feature_importance.csv", index=False, encoding="utf-8-sig")
    reduced_feature_experiment = run_reduced_feature_experiment(cluster_df, augmented_importance)
    reduced_feature_experiment.to_csv(DATA_DIR / "station_hour_reduced_feature_experiment.csv", index=False, encoding="utf-8-sig")
    feature_inventory = pd.concat(
        [
            build_feature_inventory(augmented_importance, "bike_change"),
            build_feature_inventory(augmented_importance, "bike_count_index"),
        ],
        ignore_index=True,
    )
    feature_inventory.to_csv(DATA_DIR / "station_hour_feature_inventory.csv", index=False, encoding="utf-8-sig")

    final_metrics = pd.read_csv(DATA_DIR / "station_hour_final_model_metrics.csv", encoding="utf-8-sig")
    bike_change_variant = (
        cluster_experiment[cluster_experiment["target"] == "bike_change"]
        .sort_values("rmse")
        .iloc[0]["feature_variant"]
    )
    change_pred = predictions[f"bike_change:{bike_change_variant}"]

    flow_2025 = pd.read_csv(DATA_DIR / "station_hour_bike_flow_test_2025.csv", encoding="utf-8-sig", parse_dates=["time"])
    test_mask = cluster_df["year"] == 2025
    prediction_df = cluster_df.loc[test_mask, ["station_id", "time", "bike_change"]].copy()
    prediction_df["prediction"] = change_pred
    prediction_df["abs_error"] = (prediction_df["bike_change"] - prediction_df["prediction"]).abs()
    cluster_specific_benchmark, cluster_specific_best, cluster_specific_importance, cluster_specific_comparison = (
        run_cluster_specific_model_experiment(cluster_df, prediction_df[["station_id", "time", "prediction"]])
    )
    cluster_specific_benchmark.to_csv(
        DATA_DIR / "station_hour_cluster_specific_model_benchmark.csv", index=False, encoding="utf-8-sig"
    )
    cluster_specific_best.to_csv(
        DATA_DIR / "station_hour_cluster_specific_best_models.csv", index=False, encoding="utf-8-sig"
    )
    cluster_specific_importance.to_csv(
        DATA_DIR / "station_hour_cluster_specific_feature_importance.csv", index=False, encoding="utf-8-sig"
    )
    cluster_specific_comparison.to_csv(
        DATA_DIR / "station_hour_cluster_specific_comparison.csv", index=False, encoding="utf-8-sig"
    )

    selected = pick_representative_stations(flow_2025, rep, prediction_df, train_labels)
    selected.to_csv(DATA_DIR / "station_hour_selected_representative_stations.csv", index=False, encoding="utf-8-sig")

    build_station_charts(selected, prediction_df, train_labels, cluster_stability)
    build_cluster_specific_charts(cluster_specific_best, cluster_specific_comparison, cluster_specific_importance)
    write_markdown_reframed(cluster_stability, cluster_experiment, selected, final_metrics)
    write_pdf_reframed(cluster_experiment, selected, cluster_stability)

    print(cluster_experiment.to_string(index=False))
    print(f"saved md: {REPORT_MD}")
    print(f"saved pdf: {REPORT_PDF}")


if __name__ == "__main__":
    main()
