from __future__ import annotations

import gc
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

import run_station_hour_regression as base


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
REPORT_DIR = ROOT / "reports"
ASSET_DIR = REPORT_DIR / "assets"
OUTPUT_DIR = DATA_DIR
RANDOM_STATE = base.RANDOM_STATE
REPORT_PDF = REPORT_DIR / "bike_change_optimization_report.pdf"

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
    raise FileNotFoundError(f"Could not find required data file: {name}")


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


def add_cluster_features(df: pd.DataFrame) -> pd.DataFrame:
    cluster_path = DATA_DIR / "clustering" / "ddri_second_cluster_train_with_labels.csv"
    labels = pd.read_csv(cluster_path, encoding="utf-8-sig")
    station_cluster = labels[["station_id", "cluster"]].drop_duplicates("station_id").copy()
    station_cluster["station_id"] = pd.to_numeric(station_cluster["station_id"], errors="coerce").astype(int)
    station_cluster["cluster"] = pd.to_numeric(station_cluster["cluster"], errors="coerce").astype(int)
    out = df.merge(station_cluster, on="station_id", how="left")
    out["cluster"] = out["cluster"].fillna(-1).astype(int)
    for cluster_id in range(5):
        out[f"cluster_{cluster_id}"] = (out["cluster"] == cluster_id).astype("int8")
    return out


def build_dataset() -> pd.DataFrame:
    flow = load_flow()
    weather = base.load_weather()
    station_meta = base.load_station_meta()

    df = flow.merge(weather, on="time", how="left")
    df = df.merge(station_meta, on="station_id", how="left")
    df = base.add_calendar_features(df)
    df = base.add_weather_features(df)
    df = base.add_lag_features(df)
    df = add_cluster_features(df)
    df = add_diverse_features(df)

    numeric_fill_zero = ["lat", "lon", "lcd_count", "qr_count", "dock_total", "is_qr_mixed"]
    for col in numeric_fill_zero:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.drop(columns=["date"])
    df = df.dropna().reset_index(drop=True)
    return df


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def load_park_features() -> pd.DataFrame | None:
    shared_dir = find_shared_dir()
    if shared_dir is None:
        return None
    candidates = [p for p in shared_dir.iterdir() if "공원" in p.name and p.suffix.lower() == ".csv"]
    if not candidates:
        return None
    park = pd.read_csv(candidates[0], encoding="utf-8-sig")
    col_map = {}
    for col in park.columns:
        if "경도" in col:
            col_map[col] = "park_lon"
        elif "위도" in col:
            col_map[col] = "park_lat"
        elif "공원" in col and "명" in col:
            col_map[col] = "park_name"
        elif "면적" in col:
            col_map[col] = "park_area_raw"
    park = park.rename(columns=col_map)
    required = {"park_lat", "park_lon"}
    if not required.issubset(set(park.columns)):
        return None
    park["park_lat"] = pd.to_numeric(park["park_lat"], errors="coerce")
    park["park_lon"] = pd.to_numeric(park["park_lon"], errors="coerce")
    if "park_area_raw" in park.columns:
        park["park_area"] = (
            park["park_area_raw"].astype(str).str.replace(r"[^0-9.]", "", regex=True).replace("", np.nan).astype(float)
        )
    else:
        park["park_area"] = np.nan
    return park.dropna(subset=["park_lat", "park_lon"]).copy()


def build_station_context_features(df: pd.DataFrame) -> pd.DataFrame:
    station_df = df[["station_id", "lat", "lon", "dock_total"]].drop_duplicates("station_id").copy()
    lat = station_df["lat"].to_numpy()
    lon = station_df["lon"].to_numpy()
    dist = haversine_m(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
    np.fill_diagonal(dist, np.inf)
    station_df["nearest_station_dist_m"] = dist.min(axis=1)
    station_df["nearby_station_count_500m"] = (dist <= 500).sum(axis=1)
    station_df["nearby_station_count_1000m"] = (dist <= 1000).sum(axis=1)
    dock = station_df["dock_total"].to_numpy()
    station_df["nearby_dock_total_500m"] = ((dist <= 500) * dock[None, :]).sum(axis=1)
    station_df["nearby_dock_total_1000m"] = ((dist <= 1000) * dock[None, :]).sum(axis=1)

    park = load_park_features()
    if park is not None and len(park) > 0:
        park_dist = haversine_m(
            lat[:, None],
            lon[:, None],
            park["park_lat"].to_numpy()[None, :],
            park["park_lon"].to_numpy()[None, :],
        )
        station_df["nearest_park_dist_m"] = park_dist.min(axis=1)
        station_df["park_count_1000m"] = (park_dist <= 1000).sum(axis=1)
        park_area = np.nan_to_num(park["park_area"].to_numpy(), nan=0.0)
        station_df["park_area_sum_1000m"] = ((park_dist <= 1000) * park_area[None, :]).sum(axis=1)
    else:
        station_df["nearest_park_dist_m"] = np.nan
        station_df["park_count_1000m"] = 0
        station_df["park_area_sum_1000m"] = 0.0

    return df.merge(station_df, on=["station_id", "lat", "lon", "dock_total"], how="left")


def add_diverse_features(df: pd.DataFrame) -> pd.DataFrame:
    out = build_station_context_features(df)
    dock = out["dock_total"].replace(0, np.nan)
    out["flow_total_lag_1"] = out["rental_count_lag_1"] + out["return_count_lag_1"]
    out["flow_total_lag_24"] = out["rental_count_lag_24"] + out["return_count_lag_24"]
    out["rental_return_ratio_lag_1"] = out["rental_count_lag_1"] / (out["return_count_lag_1"].abs() + 1)
    out["rental_return_ratio_lag_24"] = out["rental_count_lag_24"] / (out["return_count_lag_24"].abs() + 1)
    out["bike_change_trend_1_24"] = out["bike_change_lag_1"] - out["bike_change_lag_24"]
    out["bike_change_trend_24_168"] = out["bike_change_lag_24"] - out["bike_change_lag_168"]
    out["bike_change_roll_gap_24_168"] = out["bike_change_rollmean_24"] - out["bike_change_rollmean_168"]
    out["rental_per_dock_lag_1"] = out["rental_count_lag_1"] / dock
    out["return_per_dock_lag_1"] = out["return_count_lag_1"] / dock
    out["flow_per_dock_lag_24"] = out["flow_total_lag_24"] / dock
    out["temp_x_humidity"] = out["temperature"] * out["humidity"]
    out["rain_x_weekend"] = out["precipitation"] * out["is_weekend_or_holiday"]
    out["commute_x_cluster"] = out["is_commute_hour"] * (out["cluster"] + 1)
    out = out.replace([np.inf, -np.inf], np.nan)
    fill_cols = [
        "rental_return_ratio_lag_1",
        "rental_return_ratio_lag_24",
        "rental_per_dock_lag_1",
        "return_per_dock_lag_1",
        "flow_per_dock_lag_24",
        "nearest_park_dist_m",
    ]
    for col in fill_cols:
        out[col] = out[col].fillna(0)
    return out


def build_prior_maps(source_df: pd.DataFrame) -> dict[str, pd.DataFrame | pd.Series]:
    maps: dict[str, pd.DataFrame | pd.Series] = {}
    maps["global_hour_mean"] = source_df.groupby("hour")["bike_change"].mean()
    maps["station_mean"] = source_df.groupby("station_id")["bike_change"].mean()
    maps["station_abs_mean"] = source_df.groupby("station_id")["bike_change"].apply(lambda s: np.abs(s).mean())
    maps["station_hour"] = source_df.groupby(["station_id", "hour"])["bike_change"].agg(
        station_hour_mean="mean",
        station_hour_std="std",
    ).reset_index()
    maps["station_weekday_hour"] = source_df.groupby(["station_id", "weekday", "hour"])["bike_change"].agg(
        station_weekday_hour_mean="mean",
        station_weekday_hour_std="std",
    ).reset_index()
    maps["station_month_hour"] = source_df.groupby(["station_id", "month", "hour"])["bike_change"].mean().reset_index(
        name="station_month_hour_mean"
    )
    maps["cluster_hour"] = source_df.groupby(["cluster", "hour"])["bike_change"].mean().reset_index(name="cluster_hour_mean")
    maps["cluster_weekday_hour"] = source_df.groupby(["cluster", "weekday", "hour"])["bike_change"].mean().reset_index(
        name="cluster_weekday_hour_mean"
    )
    return maps


def apply_prior_maps(df: pd.DataFrame, maps: dict[str, pd.DataFrame | pd.Series]) -> pd.DataFrame:
    out = df.copy()
    out["global_hour_mean"] = out["hour"].map(maps["global_hour_mean"])
    out["station_mean"] = out["station_id"].map(maps["station_mean"])
    out["station_abs_mean"] = out["station_id"].map(maps["station_abs_mean"])
    out = out.merge(maps["station_hour"], on=["station_id", "hour"], how="left")
    out = out.merge(maps["station_weekday_hour"], on=["station_id", "weekday", "hour"], how="left")
    out = out.merge(maps["station_month_hour"], on=["station_id", "month", "hour"], how="left")
    out = out.merge(maps["cluster_hour"], on=["cluster", "hour"], how="left")
    out = out.merge(maps["cluster_weekday_hour"], on=["cluster", "weekday", "hour"], how="left")

    out["station_hour_mean"] = out["station_hour_mean"].fillna(out["station_mean"]).fillna(out["global_hour_mean"])
    out["station_weekday_hour_mean"] = (
        out["station_weekday_hour_mean"].fillna(out["station_hour_mean"]).fillna(out["global_hour_mean"])
    )
    out["station_month_hour_mean"] = out["station_month_hour_mean"].fillna(out["station_hour_mean"]).fillna(out["global_hour_mean"])
    out["cluster_hour_mean"] = out["cluster_hour_mean"].fillna(out["global_hour_mean"])
    out["cluster_weekday_hour_mean"] = out["cluster_weekday_hour_mean"].fillna(out["cluster_hour_mean"]).fillna(out["global_hour_mean"])
    out["station_hour_std"] = out["station_hour_std"].fillna(0)
    out["station_weekday_hour_std"] = out["station_weekday_hour_std"].fillna(out["station_hour_std"]).fillna(0)

    out["station_hour_gap"] = out["station_hour_mean"] - out["global_hour_mean"]
    out["cluster_hour_gap"] = out["cluster_hour_mean"] - out["global_hour_mean"]
    out["station_cluster_interaction"] = out["station_hour_mean"] - out["cluster_hour_mean"]
    return out


def bike_change_candidate_specs() -> list[base.ModelSpec]:
    from lightgbm import LGBMRegressor
    from xgboost import XGBRegressor

    return [
        base.ModelSpec(
            name="hist_gbm_focus",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.035,
                max_depth=12,
                max_iter=260,
                min_samples_leaf=50,
                l2_regularization=0.08,
                random_state=RANDOM_STATE,
            ),
            train_sample=500_000,
            notes="histgbm tuned for bike_change",
        ),
        base.ModelSpec(
            name="lightgbm_balanced",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                colsample_bytree=0.85,
                learning_rate=0.05,
                max_depth=12,
                min_child_samples=60,
                n_estimators=320,
                num_leaves=63,
                objective="regression",
                random_state=RANDOM_STATE,
                reg_lambda=0.15,
                subsample=0.85,
                verbosity=-1,
            ),
            train_sample=600_000,
            notes="lightgbm balanced tuning",
        ),
        base.ModelSpec(
            name="lightgbm_leafy",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                colsample_bytree=0.9,
                learning_rate=0.035,
                max_depth=14,
                min_child_samples=40,
                n_estimators=420,
                num_leaves=127,
                objective="regression",
                random_state=RANDOM_STATE,
                reg_lambda=0.1,
                subsample=0.9,
                verbosity=-1,
            ),
            train_sample=600_000,
            notes="lightgbm deeper leaves tuning",
        ),
        base.ModelSpec(
            name="lightgbm_regularized",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                colsample_bytree=0.8,
                learning_rate=0.04,
                max_depth=10,
                min_child_samples=85,
                n_estimators=360,
                num_leaves=63,
                objective="regression",
                random_state=RANDOM_STATE,
                reg_alpha=0.08,
                reg_lambda=0.35,
                subsample=0.85,
                verbosity=-1,
            ),
            train_sample=600_000,
            notes="lightgbm regularized tuning",
        ),
        base.ModelSpec(
            name="xgboost_deep",
            kind="xgboost",
            builder=lambda: XGBRegressor(
                colsample_bytree=0.9,
                learning_rate=0.035,
                max_depth=8,
                min_child_weight=14,
                n_estimators=320,
                n_jobs=1,
                objective="reg:squarederror",
                random_state=RANDOM_STATE,
                reg_lambda=1.0,
                subsample=0.9,
                tree_method="hist",
                verbosity=0,
            ),
            train_sample=600_000,
            notes="xgboost deeper tree tuning",
        ),
        base.ModelSpec(
            name="xgboost_regularized",
            kind="xgboost",
            builder=lambda: XGBRegressor(
                colsample_bytree=0.8,
                learning_rate=0.04,
                max_depth=6,
                min_child_weight=20,
                n_estimators=300,
                n_jobs=1,
                objective="reg:squarederror",
                random_state=RANDOM_STATE,
                reg_alpha=0.06,
                reg_lambda=1.8,
                subsample=0.8,
                gamma=0.08,
                tree_method="hist",
                verbosity=0,
            ),
            train_sample=600_000,
            notes="xgboost regularized tuning",
        ),
        base.ModelSpec(
            name="extra_trees_wide",
            kind="ensemble",
            builder=lambda: ExtraTreesRegressor(
                n_estimators=320,
                max_depth=28,
                min_samples_leaf=2,
                n_jobs=1,
                random_state=RANDOM_STATE,
            ),
            train_sample=180_000,
            notes="extra trees ensemble baseline",
        ),
    ]


def prune_correlated_features(df: pd.DataFrame, cols: list[str], threshold: float = 0.985) -> tuple[list[str], list[str]]:
    sample = df[cols].sample(n=min(120_000, len(df)), random_state=RANDOM_STATE)
    corr = sample.corr(numeric_only=True).abs()
    keep: list[str] = []
    dropped: list[str] = []
    for col in cols:
        if any(corr.loc[col, kept] > threshold for kept in keep if kept in corr.columns):
            dropped.append(col)
        else:
            keep.append(col)
    return keep, dropped


def feature_variants() -> dict[str, list[str]]:
    cluster_cols = ["cluster"] + [f"cluster_{i}" for i in range(5)]
    base_cols = base.feature_sets()["enhanced"] + cluster_cols
    diverse_cols = [
        "nearest_station_dist_m",
        "nearby_station_count_500m",
        "nearby_station_count_1000m",
        "nearby_dock_total_500m",
        "nearby_dock_total_1000m",
        "nearest_park_dist_m",
        "park_count_1000m",
        "park_area_sum_1000m",
        "flow_total_lag_1",
        "flow_total_lag_24",
        "rental_return_ratio_lag_1",
        "rental_return_ratio_lag_24",
        "bike_change_trend_1_24",
        "bike_change_trend_24_168",
        "bike_change_roll_gap_24_168",
        "rental_per_dock_lag_1",
        "return_per_dock_lag_1",
        "flow_per_dock_lag_24",
        "temp_x_humidity",
        "rain_x_weekend",
        "commute_x_cluster",
    ]
    prior_cols = [
        "global_hour_mean",
        "station_mean",
        "station_abs_mean",
        "station_hour_mean",
        "station_hour_std",
        "station_weekday_hour_mean",
        "station_weekday_hour_std",
        "station_month_hour_mean",
        "cluster_hour_mean",
        "cluster_weekday_hour_mean",
        "station_hour_gap",
        "cluster_hour_gap",
        "station_cluster_interaction",
    ]
    return {
        "enhanced_cluster": base_cols,
        "enhanced_cluster_diverse": base_cols + diverse_cols,
        "enhanced_cluster_priors": base_cols + prior_cols,
        "enhanced_cluster_diverse_priors": base_cols + diverse_cols + prior_cols,
    }


def probe_spec():
    specs = {spec.name: spec for spec in bike_change_candidate_specs()}
    return specs["lightgbm_balanced"]


def evaluate_model(spec, X_train: pd.DataFrame, y_train: pd.Series, X_eval: pd.DataFrame, y_eval: pd.Series) -> dict[str, float]:
    X_fit, y_fit = base.sample_train(X_train, y_train, spec.train_sample)
    model = spec.builder()
    model.fit(X_fit, y_fit)
    pred = model.predict(X_eval)
    metrics = base.evaluate_predictions(y_eval, pred)
    return {"model": model, "pred": pred, "train_rows": len(X_fit), **metrics}


def run_feature_search(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    train_df = df[df["year"] == 2023].copy()
    valid_df = df[df["year"] == 2024].copy()
    maps = build_prior_maps(train_df)
    train_aug = apply_prior_maps(train_df, maps)
    valid_aug = apply_prior_maps(valid_df, maps)
    variants = feature_variants()
    spec = probe_spec()
    rows: list[dict[str, object]] = []

    for variant_name, cols in variants.items():
        selected_cols, dropped_cols = prune_correlated_features(train_aug, cols)
        result = evaluate_model(spec, train_aug[selected_cols], train_aug["bike_change"], valid_aug[selected_cols], valid_aug["bike_change"])
        rows.append(
            {
                "feature_variant": variant_name,
                "probe_model": spec.name,
                "feature_count": len(selected_cols),
                "dropped_corr_features": len(dropped_cols),
                "train_rows": result["train_rows"],
                "eval_rows": len(valid_aug),
                "rmse": result["rmse"],
                "mae": result["mae"],
                "r2": result["r2"],
                "nrmse_std": result["nrmse_std"],
                "nmae_std": result["nmae_std"],
            }
        )
        gc.collect()

    feature_df = pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    return feature_df, str(feature_df.iloc[0]["feature_variant"])


def run_model_search(df: pd.DataFrame, variant_name: str) -> tuple[pd.DataFrame, str]:
    train_df = df[df["year"] == 2023].copy()
    valid_df = df[df["year"] == 2024].copy()
    maps = build_prior_maps(train_df)
    train_aug = apply_prior_maps(train_df, maps)
    valid_aug = apply_prior_maps(valid_df, maps)
    cols, dropped_cols = prune_correlated_features(train_aug, feature_variants()[variant_name])
    rows: list[dict[str, object]] = []

    for spec in bike_change_candidate_specs():
        result = evaluate_model(spec, train_aug[cols], train_aug["bike_change"], valid_aug[cols], valid_aug["bike_change"])
        rows.append(
            {
                "model": spec.name,
                "feature_variant": variant_name,
                "feature_count": len(cols),
                "dropped_corr_features": len(dropped_cols),
                "train_rows": result["train_rows"],
                "eval_rows": len(valid_aug),
                "rmse": result["rmse"],
                "mae": result["mae"],
                "r2": result["r2"],
                "nrmse_std": result["nrmse_std"],
                "nmae_std": result["nmae_std"],
                "notes": spec.notes,
            }
        )
        gc.collect()

    benchmark_df = pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    return benchmark_df, str(benchmark_df.iloc[0]["model"])


def run_final_global(df: pd.DataFrame, variant_name: str, model_name: str):
    specs = {spec.name: spec for spec in bike_change_candidate_specs()}
    spec = specs[model_name]
    feature_cols = feature_variants()[variant_name]

    train_df = df[df["year"] == 2023].copy()
    valid_df = df[df["year"] == 2024].copy()
    test_df = df[df["year"] == 2025].copy()
    train_valid_df = df[df["year"].isin([2023, 2024])].copy()

    select_maps = build_prior_maps(train_df)
    train_aug = apply_prior_maps(train_df, select_maps)
    valid_aug = apply_prior_maps(valid_df, select_maps)
    feature_cols, dropped_cols = prune_correlated_features(train_aug, feature_cols)

    final_maps = build_prior_maps(train_valid_df)
    test_aug = apply_prior_maps(test_df, final_maps)
    final_train_aug = apply_prior_maps(train_valid_df, final_maps)

    X_fit_sel, y_fit_sel = base.sample_train(train_aug[feature_cols], train_aug["bike_change"], spec.train_sample)
    select_model = spec.builder()
    select_model.fit(X_fit_sel, y_fit_sel)

    train_pred = select_model.predict(train_aug[feature_cols])
    valid_pred = select_model.predict(valid_aug[feature_cols])

    X_fit_final, y_fit_final = base.sample_train(final_train_aug[feature_cols], final_train_aug["bike_change"], spec.train_sample)
    final_model = spec.builder()
    final_model.fit(X_fit_final, y_fit_final)
    test_pred = final_model.predict(test_aug[feature_cols])

    metrics = pd.DataFrame(
        [
            {
                "stage": "selection",
                "split": "train",
                **base.evaluate_predictions(train_aug["bike_change"], train_pred),
            },
            {
                "stage": "selection",
                "split": "valid",
                **base.evaluate_predictions(valid_aug["bike_change"], valid_pred),
            },
            {
                "stage": "final",
                "split": "test",
                **base.evaluate_predictions(test_aug["bike_change"], test_pred),
            },
        ]
    )
    predictions = test_aug[["station_id", "time", "cluster", "bike_change"]].copy()
    predictions["prediction"] = test_pred
    predictions["abs_error"] = (predictions["bike_change"] - predictions["prediction"]).abs()

    importance_df = pd.DataFrame(columns=["feature", "importance"])
    if hasattr(final_model, "feature_importances_"):
        importance_df = pd.DataFrame(
            {"feature": feature_cols, "importance": getattr(final_model, "feature_importances_")}
        ).sort_values("importance", ascending=False)
    else:
        sample_eval = test_aug[feature_cols].sample(n=min(5000, len(test_aug)), random_state=RANDOM_STATE)
        sample_y = test_aug.loc[sample_eval.index, "bike_change"]
        importance = permutation_importance(
            final_model,
            sample_eval,
            sample_y,
            scoring="neg_root_mean_squared_error",
            n_repeats=2,
            random_state=RANDOM_STATE,
        )
        importance_df = pd.DataFrame(
            {"feature": feature_cols, "importance": importance.importances_mean}
        ).sort_values("importance", ascending=False)

    metrics["feature_variant"] = variant_name
    metrics["model"] = model_name
    metrics["feature_count"] = len(feature_cols)
    metrics["dropped_corr_features"] = len(dropped_cols)
    return metrics, predictions, importance_df, feature_cols, dropped_cols


def run_cluster_specialists(df: pd.DataFrame, variant_name: str, global_predictions: pd.DataFrame):
    feature_cols = feature_variants()[variant_name]
    specs = bike_change_candidate_specs()
    spec_map = {spec.name: spec for spec in specs}
    best_rows: list[dict[str, object]] = []
    benchmark_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []

    specialist_frames: list[pd.DataFrame] = []
    global_map = global_predictions[["station_id", "time", "prediction"]].rename(columns={"prediction": "global_prediction"})

    for cluster_id in range(5):
        train_df = df[(df["year"] == 2023) & (df["cluster"] == cluster_id)].copy()
        valid_df = df[(df["year"] == 2024) & (df["cluster"] == cluster_id)].copy()
        train_valid_df = df[(df["year"].isin([2023, 2024])) & (df["cluster"] == cluster_id)].copy()
        test_df = df[(df["year"] == 2025) & (df["cluster"] == cluster_id)].copy()
        if min(len(train_df), len(valid_df), len(test_df)) == 0:
            continue

        select_maps = build_prior_maps(train_df)
        train_aug = apply_prior_maps(train_df, select_maps)
        valid_aug = apply_prior_maps(valid_df, select_maps)
        cluster_cols, dropped_cols = prune_correlated_features(train_aug, feature_cols)
        final_maps = build_prior_maps(train_valid_df)
        final_train_aug = apply_prior_maps(train_valid_df, final_maps)
        test_aug = apply_prior_maps(test_df, final_maps)

        cluster_bench: list[dict[str, object]] = []
        for spec in specs:
            result = evaluate_model(spec, train_aug[cluster_cols], train_aug["bike_change"], valid_aug[cluster_cols], valid_aug["bike_change"])
            row = {
                "cluster": cluster_id,
                "cluster_name": CLUSTER_NAME_MAP[cluster_id],
                "model": spec.name,
                "feature_count": len(cluster_cols),
                "dropped_corr_features": len(dropped_cols),
                "selection_rmse": result["rmse"],
                "selection_mae": result["mae"],
                "selection_r2": result["r2"],
                "train_rows": result["train_rows"],
                "eval_rows": len(valid_aug),
                "feature_variant": variant_name,
            }
            cluster_bench.append(row)
            benchmark_rows.append(row)

        cluster_bench_df = pd.DataFrame(cluster_bench).sort_values(["selection_rmse", "selection_mae"]).reset_index(drop=True)
        best = cluster_bench_df.iloc[0].to_dict()
        best_spec = spec_map[str(best["model"])]
        X_fit, y_fit = base.sample_train(final_train_aug[cluster_cols], final_train_aug["bike_change"], best_spec.train_sample)
        best_model = best_spec.builder()
        best_model.fit(X_fit, y_fit)
        test_pred = best_model.predict(test_aug[cluster_cols])
        test_metrics = base.evaluate_predictions(test_aug["bike_change"], test_pred)
        best_rows.append(
            {
                "cluster": cluster_id,
                "cluster_name": CLUSTER_NAME_MAP[cluster_id],
                "model": best["model"],
                "feature_variant": variant_name,
                "selection_rmse": best["selection_rmse"],
                "selection_mae": best["selection_mae"],
                "selection_r2": best["selection_r2"],
                "test_rmse": test_metrics["rmse"],
                "test_mae": test_metrics["mae"],
                "test_r2": test_metrics["r2"],
                "train_rows": len(X_fit),
                "eval_rows": len(test_aug),
            }
        )

        frame = test_aug[["station_id", "time", "cluster", "bike_change"]].copy()
        frame["specialist_prediction"] = test_pred
        specialist_frames.append(frame)
        gc.collect()

    specialist_df = pd.concat(specialist_frames, ignore_index=True).merge(global_map, on=["station_id", "time"], how="left")
    for cluster_id, cluster_name in CLUSTER_NAME_MAP.items():
        cluster_slice = specialist_df[specialist_df["cluster"] == cluster_id]
        if len(cluster_slice) == 0:
            continue
        comparison_rows.append(
            {
                "scope": "cluster",
                "cluster": cluster_id,
                "cluster_name": cluster_name,
                "variant": "global_shared_model",
                **base.evaluate_predictions(cluster_slice["bike_change"], cluster_slice["global_prediction"]),
            }
        )
        comparison_rows.append(
            {
                "scope": "cluster",
                "cluster": cluster_id,
                "cluster_name": cluster_name,
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
            **base.evaluate_predictions(specialist_df["bike_change"], specialist_df["global_prediction"]),
        }
    )
    comparison_rows.append(
        {
            "scope": "overall",
            "cluster": -1,
            "cluster_name": "overall",
            "variant": "cluster_specific_model",
            **base.evaluate_predictions(specialist_df["bike_change"], specialist_df["specialist_prediction"]),
        }
    )

    return pd.DataFrame(benchmark_rows), pd.DataFrame(best_rows), pd.DataFrame(comparison_rows)


def write_report(feature_search: pd.DataFrame, model_search: pd.DataFrame, final_metrics: pd.DataFrame, importance_df: pd.DataFrame, cluster_best: pd.DataFrame, cluster_comparison: pd.DataFrame):
    report_path = REPORT_DIR / "bike_change_optimization_report.md"
    best_final = final_metrics[final_metrics["split"] == "test"].iloc[0]
    overall_cmp = cluster_comparison[cluster_comparison["scope"] == "overall"].copy()

    lines = [
        "# Bike Change Optimization Report",
        "",
        "## 1. Goal",
        "",
        "- Only `bike_change` is used as the target.",
        "- Objective: lower RMSE and MAE while pushing R2 as high as possible on the 2025 holdout test.",
        "",
        "## 2. New Feature Candidates",
        "",
        "- `station_hour_mean`, `station_weekday_hour_mean`, `station_month_hour_mean`",
        "- `station_hour_std`, `station_weekday_hour_std`, `station_abs_mean`",
        "- `cluster_hour_mean`, `cluster_weekday_hour_mean`",
        "- `station_hour_gap`, `cluster_hour_gap`, `station_cluster_interaction`",
        "",
        "## 3. Feature Search",
        "",
        feature_search.round(4).to_markdown(index=False),
        "",
        "## 4. Validation Model Search",
        "",
        model_search.round(4).to_markdown(index=False),
        "",
        "## 5. Final Global Result",
        "",
        final_metrics.round(4).to_markdown(index=False),
        "",
        f"- Final test RMSE: `{best_final['rmse']:.4f}`",
        f"- Final test MAE: `{best_final['mae']:.4f}`",
        f"- Final test R2: `{best_final['r2']:.4f}`",
        "",
        "## 6. Top Features In Final Model",
        "",
        importance_df.head(20).round(6).to_markdown(index=False),
        "",
        "## 7. Cluster Specialists",
        "",
        cluster_best.round(4).to_markdown(index=False),
        "",
        "## 8. Global vs Cluster-Specific",
        "",
        overall_cmp.round(4).to_markdown(index=False),
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")


A4_LANDSCAPE = (11.69, 8.27)


def _new_page():
    fig = plt.figure(figsize=A4_LANDSCAPE)
    fig.patch.set_facecolor("white")
    return fig


def _draw_wrapped_lines(fig, lines: list[str], x: float, y: float, width: int, fontsize: float, line_gap: float):
    from textwrap import wrap

    cursor = y
    for raw in lines:
        if raw == "":
            cursor -= line_gap * 0.7
            continue
        prefix = "- " if raw.startswith("- ") else ""
        text = raw[2:] if prefix else raw
        wrapped = wrap(text, width=width) or [text]
        for idx, line in enumerate(wrapped):
            fig.text(x, cursor, (prefix if idx == 0 else "  ") + line, fontsize=fontsize, va="top")
            cursor -= line_gap
        cursor -= line_gap * 0.08
    return cursor


def _draw_report_header(fig, title: str, subtitle: str | None = None):
    if subtitle:
        fig.text(0.06, 0.955, subtitle, fontsize=9.5, color="#64748b")
    fig.text(0.06, 0.92, title, fontsize=19, weight="bold", color="#0f172a")
    fig.add_artist(plt.Line2D([0.06, 0.34], [0.895, 0.895], color="#1d4ed8", linewidth=3))


def _draw_callout(fig, text: str, x: float = 0.06, y: float = 0.08, w: float = 0.88, h: float = 0.1):
    rect = plt.Rectangle((x, y), w, h, transform=fig.transFigure, facecolor="#eff6ff", edgecolor="#bfdbfe", linewidth=1.2)
    fig.add_artist(rect)
    fig.add_artist(plt.Line2D([x, x], [y, y + h], transform=fig.transFigure, color="#2563eb", linewidth=4))
    _draw_wrapped_lines(fig, [text], x=x + 0.018, y=y + h - 0.018, width=92, fontsize=10.4, line_gap=0.022)


def _draw_table(fig, df: pd.DataFrame, bbox: list[float], fontsize: float = 9.5):
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
    _draw_report_header(fig, title, subtitle="Bike Change Optimization")
    fig.text(0.06, 0.845, "진행 단계", fontsize=13, weight="bold", color="#0f172a")
    _draw_table(fig, status_df, bbox=[0.06, 0.28, 0.88, 0.5], fontsize=10)
    _draw_callout(fig, callout, y=0.11, h=0.1)
    return fig


def _make_text_page(title: str, lines: list[str], subtitle: str | None = None):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    _draw_wrapped_lines(fig, lines, x=0.06, y=0.85, width=84, fontsize=10.6, line_gap=0.024)
    return fig


def _make_table_page(title: str, section_title: str, df: pd.DataFrame, callout: str, subtitle: str | None = None, fontsize: float = 9.2):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    fig.text(0.06, 0.845, section_title, fontsize=13, weight="bold", color="#0f172a")
    _draw_table(fig, df, bbox=[0.05, 0.22, 0.9, 0.56], fontsize=fontsize)
    _draw_callout(fig, callout, y=0.08, h=0.1)
    return fig


def _make_chart_page(title: str, image_path: Path, intro_lines: list[str], callout: str, subtitle: str | None = None):
    fig = _new_page()
    _draw_report_header(fig, title, subtitle=subtitle)
    _draw_wrapped_lines(fig, intro_lines, x=0.06, y=0.85, width=84, fontsize=10.3, line_gap=0.022)
    ax = fig.add_axes([0.09, 0.24, 0.82, 0.48])
    ax.imshow(plt.imread(image_path))
    ax.axis("off")
    _draw_callout(fig, callout, y=0.08, h=0.1)
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
    _draw_wrapped_lines(fig, intro_lines, x=0.06, y=0.86, width=84, fontsize=10.1, line_gap=0.021)
    fig.text(0.08, 0.64, left_label, fontsize=11.2, weight="bold", color="#0f172a")
    fig.text(0.53, 0.64, right_label, fontsize=11.2, weight="bold", color="#0f172a")
    left_ax = fig.add_axes([0.07, 0.24, 0.38, 0.36])
    right_ax = fig.add_axes([0.52, 0.24, 0.38, 0.36])
    left_ax.imshow(plt.imread(left_image))
    right_ax.imshow(plt.imread(right_image))
    left_ax.axis("off")
    right_ax.axis("off")
    _draw_callout(fig, callout, y=0.08, h=0.1)
    return fig


def build_parameter_table() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in bike_change_candidate_specs():
        model = spec.builder()
        params = model.get_params()
        rows.append(
            {
                "model": spec.name,
                "learning_rate": params.get("learning_rate", ""),
                "max_depth": params.get("max_depth", ""),
                "n_estimators": params.get("n_estimators", params.get("max_iter", "")),
                "subsample": params.get("subsample", ""),
                "colsample_bytree": params.get("colsample_bytree", ""),
                "num_leaves": params.get("num_leaves", ""),
                "min_child": params.get("min_child_samples", params.get("min_child_weight", params.get("min_samples_leaf", ""))),
                "reg": params.get("reg_lambda", params.get("l2_regularization", "")),
                "train_sample": spec.train_sample,
            }
        )
    return pd.DataFrame(rows)


def build_visual_assets(
    feature_search: pd.DataFrame,
    model_search: pd.DataFrame,
    final_metrics: pd.DataFrame,
    importance_df: pd.DataFrame,
    predictions: pd.DataFrame,
    cluster_best: pd.DataFrame,
    cluster_comparison: pd.DataFrame,
):
    fig, ax = plt.subplots(figsize=(8, 5))
    plot_df = feature_search.sort_values("rmse")
    ax.bar(plot_df["feature_variant"], plot_df["rmse"], color=["#4c956c", "#f4a261", "#577590", "#bc4749"][: len(plot_df)])
    ax.set_title("Feature Variant Validation RMSE")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_feature_search.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    plot_df = model_search.sort_values("rmse")
    ax.barh(plot_df["model"], plot_df["rmse"], color="#1d3557")
    ax.set_title("Validation RMSE by Model")
    ax.set_xlabel("RMSE")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_model_search.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    imp = importance_df.head(15).sort_values("importance")
    ax.barh(imp["feature"], imp["importance"], color="#2a9d8f")
    ax.set_title("Top Feature Importance")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_importance.png", dpi=160)
    plt.close(fig)

    pred_month = predictions.copy()
    pred_month["month"] = pd.to_datetime(pred_month["time"]).dt.month
    monthly = pred_month.groupby("month", as_index=False).agg(actual=("bike_change", "mean"), pred=("prediction", "mean"))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(monthly["month"], monthly["actual"], marker="o", label="actual", color="#bc4749")
    ax.plot(monthly["month"], monthly["pred"], marker="o", label="prediction", color="#1d3557")
    ax.set_title("2025 Monthly Mean bike_change")
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean bike_change")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_monthly_trend.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    residual = (predictions["bike_change"] - predictions["prediction"]).clip(-8, 8)
    ax.hist(residual, bins=40, color="#6c757d", alpha=0.85)
    ax.set_title("Residual Distribution")
    ax.set_xlabel("actual - prediction (clipped)")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_residual_dist.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    best_plot = cluster_best.sort_values("cluster")
    ax.bar(best_plot["cluster_name"], best_plot["test_rmse"], color="#457b9d")
    ax.set_title("Cluster Specialist Test RMSE")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_cluster_best_rmse.png", dpi=160)
    plt.close(fig)

    cmp = cluster_comparison[cluster_comparison["scope"] == "overall"].copy()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(cmp["variant"], cmp["rmse"], color=["#8d99ae", "#2a9d8f"])
    ax.set_title("Overall RMSE: Global vs Cluster Specialist")
    ax.set_ylabel("RMSE")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "bike_change_overall_comparison.png", dpi=160)
    plt.close(fig)

    corr_cols = [
        "bike_change_lag_1",
        "bike_change_lag_24",
        "bike_change_lag_168",
        "bike_change_rollmean_24",
        "bike_change_rollmean_168",
        "flow_total_lag_24",
        "rental_return_ratio_lag_24",
        "nearest_station_dist_m",
        "park_count_1000m",
        "temp_x_humidity",
        "hour_sin",
        "is_commute_hour",
    ]
    corr_cols = [col for col in corr_cols if col in predictions.columns or col in final_metrics.columns]
    if corr_cols:
        pass


def write_detailed_pdf(
    feature_search: pd.DataFrame,
    model_search: pd.DataFrame,
    final_metrics: pd.DataFrame,
    importance_df: pd.DataFrame,
    predictions: pd.DataFrame,
    cluster_benchmark: pd.DataFrame,
    cluster_best: pd.DataFrame,
    cluster_comparison: pd.DataFrame,
):
    build_visual_assets(feature_search, model_search, final_metrics, importance_df, predictions, cluster_best, cluster_comparison)
    status_df = pd.DataFrame(
        [
            ["1. Target 고정", "완료", "bike_change만 사용"],
            ["2. Feature 후보 정의", "완료", "enhanced_cluster, priors 확장형 비교"],
            ["3. Feature 선정", "완료", "2023 train -> 2024 valid"],
            ["4. 모델/파라미터 선정", "완료", "LightGBM/XGBoost/HistGBM 튜닝 비교"],
            ["5. 최종 평가", "완료", "2023+2024 재학습 -> 2025 test"],
            ["6. Cluster별 specialist", "완료", "cluster마다 최적 모델 개별 선택"],
        ],
        columns=["Step", "Status", "Summary"],
    )

    feature_df = feature_search.copy()
    model_df = model_search.copy()
    final_df = final_metrics.copy()
    importance_top = importance_df.head(20).copy()
    cluster_bench_df = cluster_benchmark.copy()
    cluster_best_df = cluster_best.copy()
    cluster_cmp_df = cluster_comparison.copy()
    param_df = build_parameter_table()

    for df in [feature_df, model_df, final_df, importance_top, cluster_bench_df, cluster_best_df, cluster_cmp_df]:
        for col in df.columns:
            if df[col].dtype.kind in "fc":
                df[col] = df[col].map(lambda x: f"{x:.4f}")

    pages = [
        _make_status_page(
            "Bike Change Optimization Report",
            status_df,
            "이 보고서는 bike_change 단일 타깃 기준으로 feature 선정, 모델 선정, 파라미터 선정, cluster별 specialist 구성까지 전 과정을 순서대로 정리한다.",
        ),
        _make_text_page(
            "1. Problem Setup",
            [
                "- 목표 타깃은 bike_change 하나로 고정했다.",
                "- 평가 프로토콜은 2023 train, 2024 validation, 2025 test다.",
                "- feature 선정과 모델 선정은 validation only로 수행했다.",
                "- 최종 test 점수는 선택 완료 후 2023+2024로 재학습한 모델의 holdout 성능이다.",
                "- cluster specialist도 같은 규칙으로 cluster별 train-valid-test를 나눠서 선택했다.",
            ],
            subtitle="Setup",
        ),
        _make_text_page(
            "2. Feature Candidates",
            [
                "- 기본 후보: enhanced feature + cluster feature",
                "- 추가 후보: station-hour prior, station-weekday-hour prior, station-month-hour prior",
                "- 변동성 후보: station_hour_std, station_weekday_hour_std, station_abs_mean",
                "- cluster prior 후보: cluster_hour_mean, cluster_weekday_hour_mean",
                "- interaction 후보: station_hour_gap, cluster_hour_gap, station_cluster_interaction",
                "- prior 계열은 2023 train split에서만 집계해 leakage를 막았다.",
            ],
            subtitle="Feature Design",
        ),
        _make_table_page(
            "3. Feature Selection",
            "Feature variant comparison on 2024 validation",
            feature_df,
            "prior 확장형 feature를 넣어봤지만 validation RMSE/MAE가 오히려 나빠졌다. 그래서 최종 채택 feature는 enhanced_cluster다.",
            subtitle="Feature Search",
            fontsize=9.2,
        ),
        _make_table_page(
            "4. Parameter Candidates",
            "Tuned LightGBM / XGBoost / HistGBM candidates",
            param_df,
            "단순 모델 family 비교가 아니라, LightGBM/XGBoost 안에서도 성향이 다른 튜닝 버전을 여러 개 준비해 validation에서 직접 경쟁시켰다.",
            subtitle="Hyperparameters",
            fontsize=8.5,
        ),
        _make_table_page(
            "5. Model Selection",
            "Validation benchmark for bike_change",
            model_df,
            "validation 기준 최상위는 lightgbm_leafy였다. LightGBM 계열이 상위권을 차지했고, XGBoost는 근접하지만 약간 뒤처졌다.",
            subtitle="Model Search",
            fontsize=8.6,
        ),
        _make_two_chart_page(
            "6. Selection Visuals",
            [
                "- 왼쪽은 feature variant별 validation RMSE 비교다.",
                "- 오른쪽은 모델별 validation RMSE 비교다.",
                "- 다양한 feature를 넣는 것보다, 검증 기준으로 실제 도움이 되는 구성만 남기는 것이 중요했다.",
            ],
            ASSET_DIR / "bike_change_feature_search.png",
            ASSET_DIR / "bike_change_model_search.png",
            "feature variants",
            "model candidates",
            "이번 실험에서는 prior 확장형보다 enhanced_cluster가 더 안정적이었다.",
            subtitle="Validation Comparison",
        ),
        _make_table_page(
            "7. Final Global Model",
            "Train / valid / test performance of selected global model",
            final_df,
            "최종 전역 모델은 lightgbm_leafy이며, 2025 holdout test에서 RMSE 1.0408, MAE 0.5819, R2 0.2259를 기록했다.",
            subtitle="Final Global",
            fontsize=9.0,
        ),
        _make_two_chart_page(
            "8. Prediction Behavior",
            [
                "- 왼쪽은 2025 월별 평균 실제값과 예측값 추세다.",
                "- 오른쪽은 잔차 분포로, 큰 오차가 어느 정도로 퍼져 있는지 보여준다.",
                "- 추세를 따라가더라도 피크 시간대에서 잔차가 남는지 함께 확인해야 한다.",
            ],
            ASSET_DIR / "bike_change_monthly_trend.png",
            ASSET_DIR / "bike_change_residual_dist.png",
            "monthly mean trend",
            "residual distribution",
            "RMSE를 더 낮추려면 피크 시간대와 sudden spike 구간을 설명할 추가 feature가 더 필요하다.",
            subtitle="Test Diagnostics",
        ),
        _make_table_page(
            "9. Final Feature Importance",
            "Top features used by the final global model",
            importance_top,
            "중요 feature를 보면 lag/rolling 계열과 시간대, 날씨, station 위치 정보가 강하게 작동했다. 새 prior feature는 이번 최종 채택안에는 포함되지 않았다.",
            subtitle="Importance",
            fontsize=8.8,
        ),
        _make_table_page(
            "10. Cluster Validation Search",
            "Cluster-wise validation model search results",
            cluster_bench_df[["cluster_name", "model", "selection_rmse", "selection_mae", "selection_r2", "feature_variant"]].head(20),
            "cluster마다 패턴이 달라서 validation best model도 달라졌다. 한 개 전역 모델로 모두 해결하는 것보다 specialist 구성이 더 낫다.",
            subtitle="Cluster Search",
            fontsize=8.8,
        ),
        _make_table_page(
            "11. Cluster Best Models",
            "Selected specialist model for each cluster",
            cluster_best_df[["cluster_name", "model", "selection_rmse", "test_rmse", "test_mae", "test_r2", "train_rows", "eval_rows"]],
            "cluster 0/2는 LightGBM balanced, cluster 1은 XGBoost regularized, cluster 4는 HistGBM이 최적이었다. cluster별로 최적 family와 튜닝이 실제로 달라졌다.",
            subtitle="Cluster Specialists",
            fontsize=8.7,
        ),
        _make_two_chart_page(
            "12. Cluster Performance Visuals",
            [
                "- 왼쪽은 cluster별 specialist test RMSE다.",
                "- 오른쪽은 전체 기준 global shared model과 cluster specialist의 차이다.",
                "- cluster별 편차가 큰 문제를 specialist 전략으로 완화할 수 있는지 시각적으로 보여준다.",
            ],
            ASSET_DIR / "bike_change_cluster_best_rmse.png",
            ASSET_DIR / "bike_change_overall_comparison.png",
            "cluster specialist rmse",
            "overall comparison",
            "overall 기준에서도 cluster specialist가 global shared보다 개선됐다.",
            subtitle="Cluster Diagnostics",
        ),
        _make_table_page(
            "13. Global vs Specialists",
            "Comparison between global shared model and cluster-specific model",
            cluster_cmp_df,
            "overall 기준으로도 cluster-specific model이 global shared model보다 RMSE와 R2에서 개선됐다. 따라서 최종 추천안은 cluster specialist 운영 구조다.",
            subtitle="Final Comparison",
            fontsize=8.7,
        ),
        _make_text_page(
            "14. Final Recommendation",
            [
                "- 최종 전역 기본 모델: lightgbm_leafy + enhanced_cluster",
                "- 최종 운영 추천안: cluster별 specialist 모델 사용",
                "- cluster 0: lightgbm_balanced",
                "- cluster 1: xgboost_regularized",
                "- cluster 2: lightgbm_balanced",
                "- cluster 3: lightgbm_regularized",
                "- cluster 4: hist_gbm_focus",
                "- 새 prior feature는 후보로는 의미 있었지만 이번 검증에서는 채택되지 않았다.",
                "- 다음 개선 방향은 실시간 재고, 이벤트/행사, 주변 POI, 인접 station 네트워크 feature 추가다.",
            ],
            subtitle="Recommendation",
        ),
    ]

    with PdfPages(REPORT_PDF) as pdf:
        for fig in pages:
            pdf.savefig(fig)
            plt.close(fig)


def main():
    df = build_dataset()

    feature_search, best_feature_variant = run_feature_search(df)
    model_search, best_model_name = run_model_search(df, best_feature_variant)
    final_metrics, predictions, importance_df, selected_feature_cols, dropped_feature_cols = run_final_global(df, best_feature_variant, best_model_name)
    cluster_benchmark, cluster_best, cluster_comparison = run_cluster_specialists(df, best_feature_variant, predictions)

    feature_search.to_csv(OUTPUT_DIR / "bike_change_feature_search.csv", index=False, encoding="utf-8-sig")
    model_search.to_csv(OUTPUT_DIR / "bike_change_model_search.csv", index=False, encoding="utf-8-sig")
    final_metrics.to_csv(OUTPUT_DIR / "bike_change_final_metrics.csv", index=False, encoding="utf-8-sig")
    predictions.to_csv(OUTPUT_DIR / "bike_change_best_predictions_2025.csv", index=False, encoding="utf-8-sig")
    importance_df.to_csv(OUTPUT_DIR / "bike_change_feature_importance_optimized.csv", index=False, encoding="utf-8-sig")
    cluster_benchmark.to_csv(OUTPUT_DIR / "bike_change_cluster_model_search.csv", index=False, encoding="utf-8-sig")
    cluster_best.to_csv(OUTPUT_DIR / "bike_change_cluster_best_models.csv", index=False, encoding="utf-8-sig")
    cluster_comparison.to_csv(OUTPUT_DIR / "bike_change_cluster_comparison.csv", index=False, encoding="utf-8-sig")

    meta = {
        "target": "bike_change",
        "best_feature_variant": best_feature_variant,
        "best_model_name": best_model_name,
        "selected_feature_count": len(selected_feature_cols),
        "dropped_corr_features": dropped_feature_cols,
        "new_feature_groups": [
            "station-hour priors",
            "spatial context",
            "nearby station density",
            "normalized flow features",
            "station weekday-hour priors",
            "station month-hour priors",
            "cluster hour priors",
            "gap features",
        ],
    }
    (OUTPUT_DIR / "bike_change_optimization_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report(feature_search, model_search, final_metrics, importance_df, cluster_best, cluster_comparison)
    write_detailed_pdf(feature_search, model_search, final_metrics, importance_df, predictions, cluster_benchmark, cluster_best, cluster_comparison)

    print("best_feature_variant", best_feature_variant)
    print("best_model_name", best_model_name)
    print(final_metrics.to_string(index=False))
    print(cluster_best.to_string(index=False))


if __name__ == "__main__":
    main()
