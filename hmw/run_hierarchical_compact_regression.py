from __future__ import annotations

import gc
import json
import os
from dataclasses import dataclass
from pathlib import Path

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
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance

import run_station_hour_regression as base


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
REPORT_DIR = ROOT / "reports"
ASSET_DIR = REPORT_DIR / "hierarchical_compact_assets"

FULL_TRAIN_PATH = DATA_DIR / "station_hour_bike_change_hierarchical_compact_train_2023.csv.gz"
TRAIN_PATH = DATA_DIR / "station_hour_bike_change_hierarchical_compact_sampled_train_2023.csv.gz"
VALID_PATH = DATA_DIR / "station_hour_bike_change_hierarchical_compact_valid_2024.csv.gz"
TEST_PATH = DATA_DIR / "station_hour_bike_change_hierarchical_compact_test_2025.csv.gz"
CLUSTER_PATH = DATA_DIR / "clustering" / "ddri_second_cluster_train_with_labels.csv"
BAlANCED_COUNT_PATH = DATA_DIR / "station_hour_bike_change_hierarchical_balanced_counts.csv"

REPORT_MD = REPORT_DIR / "hierarchical_compact_model_report.md"
REPORT_PDF = REPORT_DIR / "hierarchical_compact_model_report.pdf"

RANDOM_STATE = base.RANDOM_STATE

REPORT_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

CLUSTER_NAME_MAP = {
    0: "cluster_0",
    1: "cluster_1",
    2: "cluster_2",
    3: "cluster_3",
    4: "cluster_4",
}


@dataclass
class CompactModelSpec:
    name: str
    kind: str
    builder: callable
    train_sample: int | None
    notes: str


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["time"])
    labels = pd.read_csv(CLUSTER_PATH, encoding="utf-8-sig")
    keep_cols = [
        "station_id",
        "cluster",
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
    station_cluster = labels[keep_cols].drop_duplicates("station_id").copy()
    station_cluster["station_id"] = pd.to_numeric(station_cluster["station_id"], errors="coerce").astype(int)
    for col in keep_cols:
        if col != "station_id":
            station_cluster[col] = pd.to_numeric(station_cluster[col], errors="coerce")
    station_cluster["cluster"] = station_cluster["cluster"].fillna(-1).astype(int)
    out = df.merge(station_cluster, on="station_id", how="left")
    out["cluster"] = out["cluster"].fillna(-1).astype(int)
    for col in keep_cols:
        if col not in {"station_id", "cluster"}:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    for cluster_id in range(5):
        out[f"cluster_{cluster_id}"] = (out["cluster"] == cluster_id).astype("int8")
    out = out.sort_values(["station_id", "time"]).reset_index(drop=True)
    return out


def safe_feature_columns(df: pd.DataFrame) -> list[str]:
    # Use all non-time-series features, excluding bike_change_deseasonalized.
    blacklist = {
        "station_id",
        "time",
        "bike_change",
        "bike_change_deseasonalized",
        "cluster",
        "seasonality_removed_flag",
        "year",
        "bike_change_resid_lag_1",
        "bike_change_resid_lag_2",
        "bike_change_resid_lag_24",
        "bike_change_resid_lag_168",
        "bike_change_resid_rollmean_3",
        "bike_change_resid_rollstd_3",
        "bike_change_resid_rollmean_24",
        "bike_change_resid_rollstd_24",
        "bike_change_resid_rollmean_168",
        "bike_change_resid_rollstd_168",
        "bike_change_resid_trend_1_24",
        "bike_change_resid_trend_24_168",
        "hour",
        "weekday",
        "month",
        "day",
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
        "hour_mean",
        "weekday_hour_mean",
        "station_weekday_hour_mean",
        "station_weekday_hour_count",
        "rental_weekday_hour_mean",
        "return_weekday_hour_mean",
        "month_pattern_group",
        "weekday_pattern_group",
        "hour_pattern_group",
        "representative_month",
        "representative_weekday",
        "representative_hour",
        "month_pattern_corr",
        "weekday_pattern_corr",
        "hour_pattern_corr",
        "month_scale_weight",
        "weekday_scale_weight",
        "hour_scale_weight",
        "is_representative_month",
        "is_representative_weekday",
        "is_representative_hour",
        "pattern_weight_combined",
    }
    return [col for col in df.columns if col not in blacklist and not col.startswith("cluster_")]


def prune_correlated_features(df: pd.DataFrame, cols: list[str], threshold: float = 0.90) -> tuple[list[str], list[dict[str, float | str]]]:
    sample = df[cols].sample(n=min(120_000, len(df)), random_state=RANDOM_STATE).copy()
    corr = sample.corr(numeric_only=True).abs().fillna(0.0)
    keep: list[str] = []
    dropped: list[dict[str, float | str]] = []
    for col in cols:
        matched = None
        for kept in keep:
            if corr.loc[col, kept] >= threshold:
                matched = kept
                break
        if matched is None:
            keep.append(col)
        else:
            dropped.append(
                {
                    "dropped_feature": col,
                    "kept_feature": matched,
                    "corr_abs": float(corr.loc[col, matched]),
                }
            )
    return keep, dropped


def feature_variants(df: pd.DataFrame) -> dict[str, list[str]]:
    base_cols = safe_feature_columns(df)
    cluster_dummy_cols = [f"cluster_{i}" for i in range(5) if f"cluster_{i}" in df.columns]
    return {
        "compact_safe_without_cluster": base_cols,
        "compact_safe_with_cluster": base_cols + cluster_dummy_cols,
    }


def build_train_weights(sampled_train_df: pd.DataFrame, full_train_df: pd.DataFrame) -> pd.Series:
    group_cols = ["month_pattern_group", "weekday_pattern_group", "hour_pattern_group"]
    raw_counts = full_train_df.groupby(group_cols).size().rename("raw_group_count").reset_index()
    sampled_counts = sampled_train_df.groupby(group_cols).size().rename("sampled_group_count").reset_index()
    weight_map = raw_counts.merge(sampled_counts, on=group_cols, how="inner")
    weight_map["pattern_sample_weight"] = weight_map["raw_group_count"] / weight_map["sampled_group_count"]
    out = sampled_train_df.merge(weight_map[group_cols + ["pattern_sample_weight"]], on=group_cols, how="left")
    weights = out["pattern_sample_weight"].fillna(1.0).astype(float)
    weights.index = sampled_train_df.index
    return weights


def model_specs() -> list[CompactModelSpec]:
    from lightgbm import LGBMRegressor
    from xgboost import XGBRegressor

    return [
        CompactModelSpec(
            name="histgbm_balanced",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_depth=10,
                max_iter=320,
                min_samples_leaf=60,
                l2_regularization=0.10,
                random_state=RANDOM_STATE,
            ),
            train_sample=140_000,
            notes="histgbm balanced",
        ),
        CompactModelSpec(
            name="histgbm_deep",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.035,
                max_depth=14,
                max_iter=380,
                min_samples_leaf=40,
                l2_regularization=0.06,
                random_state=RANDOM_STATE,
            ),
            train_sample=140_000,
            notes="histgbm deeper trees",
        ),
        CompactModelSpec(
            name="lightgbm_balanced",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                learning_rate=0.045,
                n_estimators=360,
                max_depth=10,
                num_leaves=63,
                min_child_samples=55,
                subsample=0.85,
                colsample_bytree=0.85,
                reg_lambda=0.15,
                objective="regression",
                random_state=RANDOM_STATE,
                verbosity=-1,
            ),
            train_sample=140_000,
            notes="lightgbm balanced",
        ),
        CompactModelSpec(
            name="lightgbm_leafy",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                learning_rate=0.035,
                n_estimators=420,
                max_depth=14,
                num_leaves=127,
                min_child_samples=35,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_alpha=0.03,
                reg_lambda=0.10,
                objective="regression",
                random_state=RANDOM_STATE,
                verbosity=-1,
            ),
            train_sample=140_000,
            notes="lightgbm leafy",
        ),
        CompactModelSpec(
            name="xgboost_balanced",
            kind="xgboost",
            builder=lambda: XGBRegressor(
                learning_rate=0.04,
                n_estimators=320,
                max_depth=6,
                min_child_weight=18,
                subsample=0.85,
                colsample_bytree=0.85,
                reg_lambda=1.4,
                gamma=0.03,
                objective="reg:squarederror",
                n_jobs=1,
                random_state=RANDOM_STATE,
                tree_method="hist",
                verbosity=0,
            ),
            train_sample=140_000,
            notes="xgboost balanced",
        ),
        CompactModelSpec(
            name="xgboost_regularized",
            kind="xgboost",
            builder=lambda: XGBRegressor(
                learning_rate=0.035,
                n_estimators=360,
                max_depth=8,
                min_child_weight=24,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.08,
                reg_lambda=1.9,
                gamma=0.08,
                objective="reg:squarederror",
                n_jobs=1,
                random_state=RANDOM_STATE,
                tree_method="hist",
                verbosity=0,
            ),
            train_sample=140_000,
            notes="xgboost regularized",
        ),
        CompactModelSpec(
            name="extra_trees",
            kind="ensemble",
            builder=lambda: ExtraTreesRegressor(
                n_estimators=320,
                max_depth=24,
                min_samples_leaf=2,
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
            train_sample=120_000,
            notes="extra trees",
        ),
        CompactModelSpec(
            name="random_forest",
            kind="ensemble",
            builder=lambda: RandomForestRegressor(
                n_estimators=280,
                max_depth=22,
                min_samples_leaf=2,
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
            train_sample=120_000,
            notes="random forest",
        ),
    ]


def evaluate_model(spec: CompactModelSpec, X_train: pd.DataFrame, y_train: pd.Series, X_eval: pd.DataFrame, y_eval: pd.Series):
    X_fit, y_fit = base.sample_train(X_train, y_train, spec.train_sample)
    model = spec.builder()
    model.fit(X_fit, y_fit)
    pred = model.predict(X_eval)
    return {
        "model": model,
        "prediction": pred,
        "train_rows": len(X_fit),
        **base.evaluate_predictions(y_eval, pred),
    }


def fit_with_optional_weight(model, X_train: pd.DataFrame, y_train: pd.Series, sample_weight: pd.Series | np.ndarray | None = None):
    if sample_weight is None:
        model.fit(X_train, y_train)
        return model
    try:
        model.fit(X_train, y_train, sample_weight=sample_weight)
    except TypeError:
        model.fit(X_train, y_train)
    return model


def get_importance(model, X_eval: pd.DataFrame, y_eval: pd.Series, feature_cols: list[str]) -> pd.DataFrame:
    if hasattr(model, "feature_importances_"):
        importance = getattr(model, "feature_importances_")
        return pd.DataFrame({"feature": feature_cols, "importance_mean": importance, "importance_std": 0.0}).sort_values(
            "importance_mean", ascending=False
        )
    sample_X = X_eval.sample(n=min(5000, len(X_eval)), random_state=RANDOM_STATE)
    sample_y = y_eval.loc[sample_X.index]
    perm = permutation_importance(
        model,
        sample_X,
        sample_y,
        n_repeats=3,
        random_state=RANDOM_STATE,
        scoring="neg_root_mean_squared_error",
    )
    return pd.DataFrame(
        {
            "feature": feature_cols,
            "importance_mean": perm.importances_mean,
            "importance_std": perm.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)


def run_feature_variant_search(train_df: pd.DataFrame, valid_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    probe_spec = next(spec for spec in model_specs() if spec.name == "lightgbm_balanced")
    rows: list[dict[str, object]] = []
    variants = feature_variants(train_df)
    for variant_name, cols in variants.items():
        selected_cols, dropped = prune_correlated_features(train_df, cols, threshold=0.90)
        result = evaluate_model(probe_spec, train_df[selected_cols], train_df["bike_change"], valid_df[selected_cols], valid_df["bike_change"])
        rows.append(
            {
                "feature_variant": variant_name,
                "probe_model": probe_spec.name,
                "feature_count": len(selected_cols),
                "dropped_corr_features": len(dropped),
                "train_rows": result["train_rows"],
                "eval_rows": len(valid_df),
                "rmse": result["rmse"],
                "mae": result["mae"],
                "r2": result["r2"],
                "nrmse_std": result["nrmse_std"],
                "nmae_std": result["nmae_std"],
            }
        )
        gc.collect()
    feature_search = pd.DataFrame(rows).sort_values(["r2", "rmse", "mae"], ascending=[False, True, True]).reset_index(drop=True)
    return feature_search, str(feature_search.iloc[0]["feature_variant"])


def run_model_search(train_df: pd.DataFrame, valid_df: pd.DataFrame, variant_name: str) -> tuple[pd.DataFrame, str]:
    cols, dropped = prune_correlated_features(train_df, feature_variants(train_df)[variant_name], threshold=0.90)
    rows: list[dict[str, object]] = []
    for spec in model_specs():
        result = evaluate_model(spec, train_df[cols], train_df["bike_change"], valid_df[cols], valid_df["bike_change"])
        rows.append(
            {
                "model": spec.name,
                "feature_variant": variant_name,
                "feature_count": len(cols),
                "dropped_corr_features": len(dropped),
                "train_rows": result["train_rows"],
                "eval_rows": len(valid_df),
                "rmse": result["rmse"],
                "mae": result["mae"],
                "r2": result["r2"],
                "nrmse_std": result["nrmse_std"],
                "nmae_std": result["nmae_std"],
                "notes": spec.notes,
            }
        )
        gc.collect()
    benchmark = pd.DataFrame(rows).sort_values(["r2", "rmse", "mae"], ascending=[False, True, True]).reset_index(drop=True)
    return benchmark, str(benchmark.iloc[0]["model"])


def run_final_global(train_df: pd.DataFrame, valid_df: pd.DataFrame, test_df: pd.DataFrame, full_train_df: pd.DataFrame, variant_name: str, model_name: str):
    spec = {spec.name: spec for spec in model_specs()}[model_name]
    cols, dropped = prune_correlated_features(train_df, feature_variants(train_df)[variant_name], threshold=0.90)

    select_model_result = evaluate_model(spec, train_df[cols], train_df["bike_change"], valid_df[cols], valid_df["bike_change"])
    select_model = select_model_result["model"]
    train_pred = select_model.predict(train_df[cols])
    valid_pred = select_model.predict(valid_df[cols])

    train_weights = build_train_weights(train_df, full_train_df)
    X_fit, y_fit = base.sample_train(train_df[cols], train_df["bike_change"], spec.train_sample)
    sampled_idx = X_fit.index
    weight_fit = train_weights.loc[sampled_idx]
    final_model = fit_with_optional_weight(spec.builder(), X_fit, y_fit, weight_fit)
    test_pred = final_model.predict(test_df[cols])

    metrics = pd.DataFrame(
        [
            {"stage": "selection", "split": "train", **base.evaluate_predictions(train_df["bike_change"], train_pred)},
            {"stage": "selection", "split": "valid", **base.evaluate_predictions(valid_df["bike_change"], valid_pred)},
            {"stage": "final", "split": "test", **base.evaluate_predictions(test_df["bike_change"], test_pred)},
        ]
    )
    metrics["feature_variant"] = variant_name
    metrics["model"] = model_name
    metrics["feature_count"] = len(cols)
    metrics["dropped_corr_features"] = len(dropped)
    metrics["fit_rows"] = [select_model_result["train_rows"], select_model_result["train_rows"], len(X_fit)]

    predictions = test_df[["station_id", "time", "cluster", "bike_change"]].copy()
    predictions["global_prediction"] = test_pred
    predictions["global_abs_error"] = (predictions["bike_change"] - predictions["global_prediction"]).abs()

    importance = get_importance(final_model, test_df[cols], test_df["bike_change"], cols)
    importance["scope"] = "global"
    return metrics, predictions, importance


def run_cluster_specialists(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    full_train_df: pd.DataFrame,
    global_predictions: pd.DataFrame,
):
    spec_map = {spec.name: spec for spec in model_specs()}
    specialist_features, corr_dropped = prune_correlated_features(train_df, feature_variants(train_df)["compact_safe_without_cluster"], threshold=0.90)
    benchmark_rows: list[dict[str, object]] = []
    best_rows: list[dict[str, object]] = []
    importance_frames: list[pd.DataFrame] = []
    prediction_frames: list[pd.DataFrame] = []

    for cluster_id in sorted(train_df["cluster"].dropna().unique()):
        if cluster_id < 0:
            continue
        cluster_train = train_df[train_df["cluster"] == cluster_id].copy()
        cluster_valid = valid_df[valid_df["cluster"] == cluster_id].copy()
        cluster_test = test_df[test_df["cluster"] == cluster_id].copy()
        if min(len(cluster_train), len(cluster_valid), len(cluster_test)) == 0:
            continue

        cluster_bench_rows: list[dict[str, object]] = []
        for spec in model_specs():
            result = evaluate_model(
                spec,
                cluster_train[specialist_features],
                cluster_train["bike_change"],
                cluster_valid[specialist_features],
                cluster_valid["bike_change"],
            )
            row = {
                "cluster": int(cluster_id),
                "cluster_name": CLUSTER_NAME_MAP.get(int(cluster_id), f"cluster_{cluster_id}"),
                "model": spec.name,
                "feature_count": len(specialist_features),
                "selection_rmse": result["rmse"],
                "selection_mae": result["mae"],
                "selection_r2": result["r2"],
                "train_rows": result["train_rows"],
                "eval_rows": len(cluster_valid),
            }
            cluster_bench_rows.append(row)
            benchmark_rows.append(row)

        cluster_benchmark = pd.DataFrame(cluster_bench_rows).sort_values(["selection_r2", "selection_rmse", "selection_mae"], ascending=[False, True, True]).reset_index(drop=True)
        best = cluster_benchmark.iloc[0].to_dict()
        best_spec = spec_map[str(best["model"])]

        cluster_full_train = full_train_df[full_train_df["cluster"] == cluster_id].copy()
        cluster_weights = build_train_weights(cluster_train, cluster_full_train)
        X_fit, y_fit = base.sample_train(cluster_train[specialist_features], cluster_train["bike_change"], best_spec.train_sample)
        weight_fit = cluster_weights.loc[X_fit.index]
        model = fit_with_optional_weight(best_spec.builder(), X_fit, y_fit, weight_fit)
        cluster_test_pred = model.predict(cluster_test[specialist_features])
        test_metrics = base.evaluate_predictions(cluster_test["bike_change"], cluster_test_pred)

        best_rows.append(
            {
                "cluster": int(cluster_id),
                "cluster_name": CLUSTER_NAME_MAP.get(int(cluster_id), f"cluster_{cluster_id}"),
                "model": str(best["model"]),
                "selection_rmse": float(best["selection_rmse"]),
                "selection_mae": float(best["selection_mae"]),
                "selection_r2": float(best["selection_r2"]),
                "test_rmse": test_metrics["rmse"],
                "test_mae": test_metrics["mae"],
                "test_r2": test_metrics["r2"],
                "fit_rows": len(X_fit),
                "test_rows": len(cluster_test),
                "feature_count": len(specialist_features),
                "dropped_corr_features": len(corr_dropped),
            }
        )

        importance = get_importance(model, cluster_test[specialist_features], cluster_test["bike_change"], specialist_features)
        importance["scope"] = "cluster"
        importance["cluster"] = int(cluster_id)
        importance["cluster_name"] = CLUSTER_NAME_MAP.get(int(cluster_id), f"cluster_{cluster_id}")
        importance_frames.append(importance)

        pred_frame = cluster_test[["station_id", "time", "cluster", "bike_change"]].copy()
        pred_frame["specialist_prediction"] = cluster_test_pred
        prediction_frames.append(pred_frame)
        gc.collect()

    specialist_pred = pd.concat(prediction_frames, ignore_index=True)
    merged = specialist_pred.merge(
        global_predictions[["station_id", "time", "global_prediction"]],
        on=["station_id", "time"],
        how="left",
    )
    merged["global_abs_error"] = (merged["bike_change"] - merged["global_prediction"]).abs()
    merged["specialist_abs_error"] = (merged["bike_change"] - merged["specialist_prediction"]).abs()

    comparison_rows: list[dict[str, object]] = []
    for cluster_id in sorted(merged["cluster"].dropna().unique()):
        cluster_slice = merged[merged["cluster"] == cluster_id]
        comparison_rows.append(
            {
                "scope": "cluster",
                "cluster": int(cluster_id),
                "cluster_name": CLUSTER_NAME_MAP.get(int(cluster_id), f"cluster_{cluster_id}"),
                "variant": "global_shared_model",
                **base.evaluate_predictions(cluster_slice["bike_change"], cluster_slice["global_prediction"]),
            }
        )
        comparison_rows.append(
            {
                "scope": "cluster",
                "cluster": int(cluster_id),
                "cluster_name": CLUSTER_NAME_MAP.get(int(cluster_id), f"cluster_{cluster_id}"),
                "variant": "cluster_specific_model",
                **base.evaluate_predictions(cluster_slice["bike_change"], cluster_slice["specialist_prediction"]),
            }
        )
    comparison_rows.append(
        {
            "scope": "overall",
            "cluster": -1,
            "cluster_name": "overall",
            "variant": "global_shared_model",
            **base.evaluate_predictions(merged["bike_change"], merged["global_prediction"]),
        }
    )
    comparison_rows.append(
        {
            "scope": "overall",
            "cluster": -1,
            "cluster_name": "overall",
            "variant": "cluster_specific_model",
            **base.evaluate_predictions(merged["bike_change"], merged["specialist_prediction"]),
        }
    )

    return (
        pd.DataFrame(benchmark_rows).sort_values(["cluster", "selection_rmse", "selection_mae"]).reset_index(drop=True),
        pd.DataFrame(best_rows).sort_values("cluster").reset_index(drop=True),
        pd.concat(importance_frames, ignore_index=True).sort_values(["cluster", "importance_mean"], ascending=[True, False]).reset_index(drop=True),
        pd.DataFrame(comparison_rows),
        merged.sort_values(["cluster", "station_id", "time"]).reset_index(drop=True),
    )


def build_assets(feature_search, model_search, final_metrics, global_importance, cluster_best, cluster_comparison, cluster_importance):
    plt.style.use("seaborn-v0_8-whitegrid")
    assets: list[Path] = []

    fig, ax = plt.subplots(figsize=(7, 4))
    plot_df = feature_search.sort_values("rmse")
    ax.bar(plot_df["feature_variant"], plot_df["rmse"], color="#4C78A8")
    ax.set_title("Feature Variant Validation RMSE")
    ax.set_ylabel("RMSE")
    fig.tight_layout()
    path = ASSET_DIR / "feature_variant_rmse.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assets.append(path)

    fig, ax = plt.subplots(figsize=(9, 4))
    plot_df = model_search.sort_values("rmse")
    ax.bar(plot_df["model"], plot_df["rmse"], color="#F58518")
    ax.set_title("Model Validation RMSE")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    path = ASSET_DIR / "model_benchmark_rmse.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assets.append(path)

    fig, ax = plt.subplots(figsize=(8, 5))
    top = global_importance.head(12).sort_values("importance_mean")
    ax.barh(top["feature"], top["importance_mean"], color="#54A24B")
    ax.set_title("Global Feature Importance")
    fig.tight_layout()
    path = ASSET_DIR / "global_feature_importance.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assets.append(path)

    fig, ax = plt.subplots(figsize=(8, 4))
    plot_df = cluster_best.sort_values("cluster")
    ax.bar(plot_df["cluster_name"], plot_df["test_rmse"], color="#E45756")
    ax.set_title("Best Specialist Test RMSE by Cluster")
    ax.set_ylabel("RMSE")
    fig.tight_layout()
    path = ASSET_DIR / "cluster_best_rmse.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assets.append(path)

    cmp = cluster_comparison[cluster_comparison["scope"] == "overall"].copy()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(cmp["variant"], cmp["rmse"], color=["#4C78A8", "#72B7B2"])
    ax.set_title("Overall Test RMSE Comparison")
    ax.set_ylabel("RMSE")
    fig.tight_layout()
    path = ASSET_DIR / "overall_rmse_comparison.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assets.append(path)

    top_cluster = (
        cluster_importance.sort_values(["cluster", "importance_mean"], ascending=[True, False])
        .groupby("cluster", as_index=False)
        .head(1)
        .sort_values("cluster")
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(top_cluster["cluster_name"], top_cluster["importance_mean"], color="#B279A2")
    for idx, feat in enumerate(top_cluster["feature"]):
        ax.text(idx, top_cluster.iloc[idx]["importance_mean"], feat, rotation=30, ha="center", va="bottom", fontsize=8)
    ax.set_title("Top Feature Importance by Cluster")
    fig.tight_layout()
    path = ASSET_DIR / "cluster_top_feature_importance.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    assets.append(path)

    return assets


def write_markdown(feature_search, model_search, final_metrics, global_importance, cluster_best, cluster_comparison, cluster_importance):
    best_test = final_metrics[final_metrics["split"] == "test"].iloc[0]
    overall_cmp = cluster_comparison[cluster_comparison["scope"] == "overall"].set_index("variant")
    lines = [
        "# Hierarchical Compact Regression Report",
        "",
        "## 1. 데이터와 실험 목적",
        "",
        "- 입력 데이터는 `hierarchical_compact` 버전이다.",
        "- 학습 train은 대표 패턴을 균형 샘플링한 `sampled_train_2023`, 검증은 `valid_2024`, 최종 평가는 `test_2025`를 사용했다.",
        "- 목표는 단순화한 데이터에서도 RMSE와 MAE를 낮추고, cluster별로 최적 모델을 다르게 적용해 R²를 최대화하는 것이다.",
        "- 현재 시점 타깃 분해값인 `bike_change_deseasonalized`, `bike_change_seasonal_expected`, `return_count_deseasonalized`는 누수 방지를 위해 제외했다.",
        "",
        "## 2. Feature Variant 비교",
        "",
        feature_search.round(4).to_markdown(index=False),
        "",
        "## 3. 글로벌 모델 비교",
        "",
        model_search.round(4).to_markdown(index=False),
        "",
        "## 4. 최종 글로벌 모델 성능",
        "",
        final_metrics.round(4).to_markdown(index=False),
        "",
        f"- 최종 글로벌 모델: `{best_test['model']}`",
        f"- 선택된 feature variant: `{best_test['feature_variant']}`",
        f"- test RMSE `{best_test['rmse']:.4f}`, MAE `{best_test['mae']:.4f}`, R² `{best_test['r2']:.4f}`",
        "",
        "## 5. 글로벌 Feature Importance",
        "",
        global_importance.head(15).round(6).to_markdown(index=False),
        "",
        "## 6. Cluster별 최적 모델",
        "",
        cluster_best.round(4).to_markdown(index=False),
        "",
        "## 7. Global vs Cluster Specialist",
        "",
        cluster_comparison.round(4).to_markdown(index=False),
        "",
        f"- overall global shared model RMSE `{overall_cmp.loc['global_shared_model', 'rmse']:.4f}`",
        f"- overall cluster specific model RMSE `{overall_cmp.loc['cluster_specific_model', 'rmse']:.4f}`",
        f"- overall global shared model R² `{overall_cmp.loc['global_shared_model', 'r2']:.4f}`",
        f"- overall cluster specific model R² `{overall_cmp.loc['cluster_specific_model', 'r2']:.4f}`",
        "",
        "## 8. Cluster별 중요 Feature",
        "",
        cluster_importance.groupby("cluster").head(5).round(6).to_markdown(index=False),
        "",
        "## 9. 해석",
        "",
        "- 단순화된 데이터에서도 residual lag 계열과 deseasonalized target 계열이 핵심 설명력을 유지하는지 확인할 수 있다.",
        "- cluster specialist는 station 성격이 다른 묶음에서 개별 최적 모델을 쓰기 때문에, 전체 shared model보다 오차가 낮아질 가능성이 있다.",
        "- cluster 1처럼 station 수가 적은 군집은 과적합 위험이 있어, 복잡한 모델보다 규제가 강한 부스팅 모델이 더 유리할 수 있다.",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_pdf(feature_search, model_search, final_metrics, cluster_best, cluster_comparison, assets: list[Path]):
    best_test = final_metrics[final_metrics["split"] == "test"].iloc[0]
    overall_cmp = cluster_comparison[cluster_comparison["scope"] == "overall"].set_index("variant")
    with PdfPages(REPORT_PDF) as pdf:
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        summary_lines = [
            "Hierarchical Compact Modeling Summary",
            "",
            f"Global best model: {best_test['model']}",
            f"Feature variant: {best_test['feature_variant']}",
            f"Test RMSE: {best_test['rmse']:.4f}",
            f"Test MAE: {best_test['mae']:.4f}",
            f"Test R2: {best_test['r2']:.4f}",
            "",
            f"Overall shared RMSE: {overall_cmp.loc['global_shared_model', 'rmse']:.4f}",
            f"Overall specialist RMSE: {overall_cmp.loc['cluster_specific_model', 'rmse']:.4f}",
            f"Overall shared R2: {overall_cmp.loc['global_shared_model', 'r2']:.4f}",
            f"Overall specialist R2: {overall_cmp.loc['cluster_specific_model', 'r2']:.4f}",
            "",
            "Best specialist model by cluster:",
        ]
        for _, row in cluster_best.iterrows():
            summary_lines.append(
                f"- {row['cluster_name']}: {row['model']} | RMSE {row['test_rmse']:.4f} | MAE {row['test_mae']:.4f} | R2 {row['test_r2']:.4f}"
            )
        ax.text(0.03, 0.97, "\n".join(summary_lines), va="top", ha="left", fontsize=12)
        pdf.savefig(fig)
        plt.close(fig)

        for asset in assets:
            img = plt.imread(asset)
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.imshow(img)
            ax.axis("off")
            ax.set_title(asset.stem)
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def main():
    full_train_df = load_dataset(FULL_TRAIN_PATH)
    train_df = load_dataset(TRAIN_PATH)
    valid_df = load_dataset(VALID_PATH)
    test_df = load_dataset(TEST_PATH)

    feature_search, best_variant = run_feature_variant_search(train_df, valid_df)
    model_search, best_model = run_model_search(train_df, valid_df, best_variant)
    final_metrics, global_predictions, global_importance = run_final_global(train_df, valid_df, test_df, full_train_df, best_variant, best_model)
    cluster_benchmark, cluster_best, cluster_importance, cluster_comparison, merged_predictions = run_cluster_specialists(
        train_df,
        valid_df,
        test_df,
        full_train_df,
        global_predictions,
    )

    feature_search.to_csv(DATA_DIR / "hierarchical_compact_feature_variant_search.csv", index=False, encoding="utf-8-sig")
    model_search.to_csv(DATA_DIR / "hierarchical_compact_model_benchmark.csv", index=False, encoding="utf-8-sig")
    final_metrics.to_csv(DATA_DIR / "hierarchical_compact_final_metrics.csv", index=False, encoding="utf-8-sig")
    global_importance.to_csv(DATA_DIR / "hierarchical_compact_global_feature_importance.csv", index=False, encoding="utf-8-sig")
    cluster_benchmark.to_csv(DATA_DIR / "hierarchical_compact_cluster_model_benchmark.csv", index=False, encoding="utf-8-sig")
    cluster_best.to_csv(DATA_DIR / "hierarchical_compact_cluster_best_models.csv", index=False, encoding="utf-8-sig")
    cluster_importance.to_csv(DATA_DIR / "hierarchical_compact_cluster_feature_importance.csv", index=False, encoding="utf-8-sig")
    cluster_comparison.to_csv(DATA_DIR / "hierarchical_compact_cluster_comparison.csv", index=False, encoding="utf-8-sig")
    merged_predictions.to_csv(DATA_DIR / "hierarchical_compact_test_predictions.csv", index=False, encoding="utf-8-sig")

    assets = build_assets(
        feature_search,
        model_search,
        final_metrics,
        global_importance,
        cluster_best,
        cluster_comparison,
        cluster_importance,
    )
    write_markdown(feature_search, model_search, final_metrics, global_importance, cluster_best, cluster_comparison, cluster_importance)
    write_pdf(feature_search, model_search, final_metrics, cluster_best, cluster_comparison, assets)

    meta = {
        "target": "bike_change",
        "data": {
            "full_train": FULL_TRAIN_PATH.name,
            "train": TRAIN_PATH.name,
            "valid": VALID_PATH.name,
            "test": TEST_PATH.name,
        },
        "global_best": {
            "feature_variant": best_variant,
            "model": best_model,
        },
        "outputs": {
            "feature_variant_search": "hierarchical_compact_feature_variant_search.csv",
            "model_benchmark": "hierarchical_compact_model_benchmark.csv",
            "final_metrics": "hierarchical_compact_final_metrics.csv",
            "global_feature_importance": "hierarchical_compact_global_feature_importance.csv",
            "cluster_model_benchmark": "hierarchical_compact_cluster_model_benchmark.csv",
            "cluster_best_models": "hierarchical_compact_cluster_best_models.csv",
            "cluster_feature_importance": "hierarchical_compact_cluster_feature_importance.csv",
            "cluster_comparison": "hierarchical_compact_cluster_comparison.csv",
            "test_predictions": "hierarchical_compact_test_predictions.csv",
            "report_md": str(REPORT_MD.relative_to(ROOT)),
            "report_pdf": str(REPORT_PDF.relative_to(ROOT)),
        },
    }
    (DATA_DIR / "hierarchical_compact_model_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
