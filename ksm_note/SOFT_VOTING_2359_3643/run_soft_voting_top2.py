from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import confusion_matrix, mean_absolute_error, mean_squared_error, r2_score

try:
    from lightgbm import LGBMRegressor

    HAS_LIGHTGBM = True
except Exception:
    HAS_LIGHTGBM = False

try:
    from xgboost import XGBRegressor

    HAS_XGBOOST = True
except Exception:
    HAS_XGBOOST = False


RANDOM_STATE = 42
TARGET_STATIONS = [2359, 3643]
TARGET_COL = "rental_count"
PLOT_FONT = "Malgun Gothic"


@dataclass
class StationSplit:
    station_id: int
    station_name: str
    train_2023: pd.DataFrame
    valid_2024: pd.DataFrame
    test_2025: pd.DataFrame


def find_file(repo_root: Path, filename: str) -> Path:
    matches = list(repo_root.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"Could not find {filename!r} under {repo_root}")
    if len(matches) == 1:
        return matches[0]
    matches = sorted(matches, key=lambda p: ("second_round_data" not in str(p), len(str(p))))
    return matches[0]


def load_source_data(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_path = find_file(repo_root, "ddri_prediction_long_train_2023_2024_second_round_feature_collection.csv")
    test_path = find_file(repo_root, "ddri_prediction_long_test_2025_second_round_feature_collection.csv")
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    return train_df, test_df


def create_station_split(train_df: pd.DataFrame, test_df: pd.DataFrame, station_id: int) -> StationSplit:
    train_station = train_df.loc[train_df["station_id"] == station_id].copy()
    test_station = test_df.loc[test_df["station_id"] == station_id].copy()
    if train_station.empty or test_station.empty:
        raise ValueError(f"No rows found for station {station_id}")

    for df in (train_station, test_station):
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["timestamp"] = df["date"] + pd.to_timedelta(df["hour"], unit="h")
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)

    train_2023 = train_station.loc[train_station["year"] == 2023].copy()
    valid_2024 = train_station.loc[train_station["year"] == 2024].copy()
    test_2025 = test_station.loc[test_station["year"] == 2025].copy()
    if train_2023.empty or valid_2024.empty or test_2025.empty:
        raise ValueError(f"Year split is empty for station {station_id}")

    station_name = train_station["station_name"].iloc[0].strip()
    return StationSplit(
        station_id=station_id,
        station_name=station_name,
        train_2023=train_2023,
        valid_2024=valid_2024,
        test_2025=test_2025,
    )


def select_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    candidate_features = [
        "hour",
        "weekday",
        "month",
        "holiday",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "subway_distance_m",
        "bus_stop_count_300m",
        "station_elevation_m",
        "elevation_diff_nearest_subway_m",
        "distance_naturepark_m",
        "distance_river_boundary_m",
        "is_weekend",
        "is_commute_hour",
        "is_lunch_hour",
        "is_night_hour",
        "is_rainy",
        "heavy_rain_flag",
        "lag_48h",
        "rolling_mean_6h",
        "rolling_std_6h",
        "hour_sin",
        "hour_cos",
        "season",
        "temperature_bin",
    ]
    features = [col for col in candidate_features if col in df.columns]

    categorical_cols = [
        col
        for col in [
            "hour",
            "weekday",
            "month",
            "holiday",
            "is_weekend",
            "is_commute_hour",
            "is_lunch_hour",
            "is_night_hour",
            "is_rainy",
            "heavy_rain_flag",
            "season",
            "temperature_bin",
        ]
        if col in features
    ]
    numeric_cols = [col for col in features if col not in categorical_cols]
    return features, categorical_cols, numeric_cols


def impute_features(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    categorical_cols: list[str],
    numeric_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = train_df.copy()
    valid = valid_df.copy()
    test = test_df.copy()

    for col in numeric_cols:
        fill = train[col].median()
        if pd.isna(fill):
            fill = 0.0
        train[col] = train[col].fillna(fill)
        valid[col] = valid[col].fillna(fill)
        test[col] = test[col].fillna(fill)

    for col in categorical_cols:
        modes = train[col].mode(dropna=True)
        fill = modes.iloc[0] if not modes.empty else 0
        train[col] = train[col].fillna(fill)
        valid[col] = valid[col].fillna(fill)
        test[col] = test[col].fillna(fill)

    return train, valid, test


def one_hot_align(
    train_df: pd.DataFrame,
    other_dfs: list[pd.DataFrame],
    feature_cols: list[str],
    categorical_cols: list[str],
) -> list[pd.DataFrame]:
    x_train = pd.get_dummies(train_df[feature_cols], columns=categorical_cols, dtype=float)
    aligned = [x_train]
    for df in other_dfs:
        x = pd.get_dummies(df[feature_cols], columns=categorical_cols, dtype=float)
        x = x.reindex(columns=x_train.columns, fill_value=0.0)
        aligned.append(x)
    return aligned


def build_model_factories() -> dict[str, Callable[[], object]]:
    factories: dict[str, Callable[[], object]] = {}
    if HAS_LIGHTGBM:
        factories["lightgbm"] = lambda: LGBMRegressor(
            objective="regression",
            n_estimators=700,
            learning_rate=0.04,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    else:
        factories["hist_gbr"] = lambda: HistGradientBoostingRegressor(
            max_iter=450,
            learning_rate=0.05,
            max_depth=8,
            l2_regularization=0.1,
            random_state=RANDOM_STATE,
        )

    if HAS_XGBOOST:
        factories["xgboost"] = lambda: XGBRegressor(
            objective="reg:squarederror",
            n_estimators=700,
            max_depth=6,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    else:
        factories["extra_trees"] = lambda: ExtraTreesRegressor(
            n_estimators=500,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    factories["random_forest"] = lambda: RandomForestRegressor(
        n_estimators=500,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    return factories


def to_bucket(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr)
    return np.where(arr <= 0, 0, np.where(arr == 1, 1, np.where(arr == 2, 2, 3)))


def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(float)
    y_pred = np.asarray(y_pred).astype(float)
    pred_rounded = np.rint(np.clip(y_pred, a_min=0, a_max=None)).astype(int)
    true_int = np.rint(y_true).astype(int)
    exact_hits = int((true_int == pred_rounded).sum())
    exact_rate = exact_hits / len(true_int)
    bucket_acc = float((to_bucket(true_int) == to_bucket(pred_rounded)).mean())
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "exact_match_hits_rounded": exact_hits,
        "exact_match_rate_rounded": float(exact_rate),
        "bucket_accuracy_0_1_2_3plus": bucket_acc,
        "n_samples": int(len(true_int)),
    }


def generate_weight_grid(step: float = 0.05) -> list[tuple[float, float, float]]:
    vals = np.arange(0.0, 1.0 + 1e-9, step)
    combos = []
    for w1, w2 in itertools.product(vals, vals):
        w3 = 1.0 - w1 - w2
        if w3 < -1e-9:
            continue
        if w3 < 0:
            w3 = 0.0
        combos.append((round(float(w1), 4), round(float(w2), 4), round(float(w3), 4)))
    return combos


def find_best_soft_weights(
    valid_true: np.ndarray,
    valid_preds: dict[str, np.ndarray],
    step: float = 0.05,
) -> tuple[pd.DataFrame, pd.Series]:
    model_names = list(valid_preds.keys())
    if len(model_names) != 3:
        raise ValueError("This pipeline expects exactly 3 base models for soft voting.")

    rows = []
    for w1, w2, w3 in generate_weight_grid(step=step):
        blended = w1 * valid_preds[model_names[0]] + w2 * valid_preds[model_names[1]] + w3 * valid_preds[model_names[2]]
        metrics = evaluate_regression(valid_true, blended)
        rows.append(
            {
                "weight_" + model_names[0]: w1,
                "weight_" + model_names[1]: w2,
                "weight_" + model_names[2]: w3,
                **metrics,
            }
        )

    grid_df = pd.DataFrame(rows)
    sort_cols = ["exact_match_rate_rounded", "bucket_accuracy_0_1_2_3plus", "rmse", "mae"]
    ascending = [False, False, True, True]
    best = grid_df.sort_values(sort_cols, ascending=ascending).iloc[0]
    return grid_df, best


def build_confusion_outputs(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    true_int = np.rint(np.asarray(y_true)).astype(int)
    pred_int = np.rint(np.clip(np.asarray(y_pred), 0, None)).astype(int)

    exact_labels = sorted(set(true_int.tolist()) | set(pred_int.tolist()))
    exact_cm = confusion_matrix(true_int, pred_int, labels=exact_labels)
    exact_cm_df = pd.DataFrame(exact_cm, index=exact_labels, columns=exact_labels)
    exact_cm_df.index.name = "actual"
    exact_cm_df.columns.name = "predicted"

    bucket_true = to_bucket(true_int)
    bucket_pred = to_bucket(pred_int)
    bucket_labels = [0, 1, 2, 3]
    bucket_cm = confusion_matrix(bucket_true, bucket_pred, labels=bucket_labels)
    bucket_cm_df = pd.DataFrame(bucket_cm, index=["0", "1", "2", "3+"], columns=["0", "1", "2", "3+"])
    bucket_cm_df.index.name = "actual"
    bucket_cm_df.columns.name = "predicted"
    return exact_cm_df, bucket_cm_df


def plot_confusion_matrix(df_cm: pd.DataFrame, title: str, output_path: Path) -> None:
    plt.rcParams["font.family"] = PLOT_FONT
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    matrix = df_cm.values
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks(range(len(df_cm.columns)))
    ax.set_xticklabels([str(c) for c in df_cm.columns], rotation=30, ha="right")
    ax.set_yticks(range(len(df_cm.index)))
    ax.set_yticklabels([str(i) for i in df_cm.index])

    max_val = matrix.max() if matrix.size > 0 else 1
    threshold = max_val * 0.55
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = int(matrix[i, j])
            color = "white" if value > threshold else "black"
            ax.text(j, i, f"{value}", ha="center", va="center", color=color, fontsize=9)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def run_for_station(
    split: StationSplit,
    out_dir: Path,
    model_factories: dict[str, Callable[[], object]],
) -> dict[str, object]:
    feature_cols, categorical_cols, numeric_cols = select_feature_columns(split.train_2023)
    train_df, valid_df, test_df = impute_features(
        split.train_2023,
        split.valid_2024,
        split.test_2025,
        categorical_cols=categorical_cols,
        numeric_cols=numeric_cols,
    )

    x_train, x_valid = one_hot_align(
        train_df=train_df,
        other_dfs=[valid_df],
        feature_cols=feature_cols,
        categorical_cols=categorical_cols,
    )
    y_train = train_df[TARGET_COL].values.astype(float)
    y_valid = valid_df[TARGET_COL].values.astype(float)

    valid_preds: dict[str, np.ndarray] = {}
    valid_model_rows = []
    for model_name, factory in model_factories.items():
        model = factory()
        model.fit(x_train, y_train)
        pred = np.asarray(model.predict(x_valid), dtype=float)
        valid_preds[model_name] = pred
        row = {"model": model_name, "split": "validation_2024", **evaluate_regression(y_valid, pred)}
        valid_model_rows.append(row)

    valid_model_df = pd.DataFrame(valid_model_rows).sort_values("rmse").reset_index(drop=True)
    valid_model_df.to_csv(out_dir / f"station_{split.station_id}_valid_model_metrics.csv", index=False)

    weight_grid_df, best_weight_row = find_best_soft_weights(y_valid, valid_preds, step=0.05)
    weight_grid_df.to_csv(out_dir / f"station_{split.station_id}_soft_weight_grid.csv", index=False)
    pd.DataFrame([best_weight_row]).to_csv(out_dir / f"station_{split.station_id}_best_soft_weight.csv", index=False)

    train_valid_df = pd.concat([train_df, valid_df], ignore_index=True)
    x_train_valid, x_test = one_hot_align(
        train_df=train_valid_df,
        other_dfs=[test_df],
        feature_cols=feature_cols,
        categorical_cols=categorical_cols,
    )
    y_train_valid = train_valid_df[TARGET_COL].values.astype(float)
    y_test = test_df[TARGET_COL].values.astype(float)

    test_preds: dict[str, np.ndarray] = {}
    for model_name, factory in model_factories.items():
        model = factory()
        model.fit(x_train_valid, y_train_valid)
        test_preds[model_name] = np.asarray(model.predict(x_test), dtype=float)

    model_names = list(model_factories.keys())
    w = [best_weight_row[f"weight_{name}"] for name in model_names]
    pred_ensemble = w[0] * test_preds[model_names[0]] + w[1] * test_preds[model_names[1]] + w[2] * test_preds[model_names[2]]

    test_metric_rows = []
    for model_name, pred in test_preds.items():
        test_metric_rows.append({"model": model_name, "split": "test_2025", **evaluate_regression(y_test, pred)})
    test_metric_rows.append({"model": "soft_voting_ensemble", "split": "test_2025", **evaluate_regression(y_test, pred_ensemble)})
    test_metrics_df = pd.DataFrame(test_metric_rows).sort_values("rmse").reset_index(drop=True)
    test_metrics_df.to_csv(out_dir / f"station_{split.station_id}_test_model_metrics.csv", index=False)

    pred_frame = pd.DataFrame(
        {
            "station_id": split.station_id,
            "station_name": split.station_name,
            "date": test_df["date"].dt.strftime("%Y-%m-%d"),
            "hour": test_df["hour"].astype(int),
            "actual_rental_count": y_test.astype(int),
            f"pred_{model_names[0]}": test_preds[model_names[0]],
            f"pred_{model_names[1]}": test_preds[model_names[1]],
            f"pred_{model_names[2]}": test_preds[model_names[2]],
            "pred_soft_voting": pred_ensemble,
            "pred_soft_voting_rounded": np.rint(np.clip(pred_ensemble, 0, None)).astype(int),
            "actual_bucket_0_1_2_3plus": to_bucket(y_test.astype(int)),
            "pred_bucket_0_1_2_3plus": to_bucket(np.rint(np.clip(pred_ensemble, 0, None)).astype(int)),
        }
    )
    pred_frame.to_csv(out_dir / f"station_{split.station_id}_predictions_2025.csv", index=False)

    exact_cm_df, bucket_cm_df = build_confusion_outputs(y_test, pred_ensemble)
    exact_cm_df.to_csv(out_dir / f"station_{split.station_id}_confusion_exact.csv")
    bucket_cm_df.to_csv(out_dir / f"station_{split.station_id}_confusion_bucket.csv")

    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    plot_confusion_matrix(
        bucket_cm_df,
        title=f"Station {split.station_id} Bucket Confusion (Soft Voting)",
        output_path=img_dir / f"station_{split.station_id}_confusion_bucket.png",
    )
    plot_confusion_matrix(
        exact_cm_df,
        title=f"Station {split.station_id} Exact Count Confusion (Soft Voting)",
        output_path=img_dir / f"station_{split.station_id}_confusion_exact.png",
    )

    baseline_name = "lightgbm" if "lightgbm" in test_preds else model_names[0]
    baseline_metrics = evaluate_regression(y_test, test_preds[baseline_name])
    ensemble_metrics = evaluate_regression(y_test, pred_ensemble)
    return {
        "station_id": split.station_id,
        "station_name": split.station_name,
        "model_names": model_names,
        "best_weights": {name: float(best_weight_row[f"weight_{name}"]) for name in model_names},
        "baseline_model": baseline_name,
        "baseline_metrics": baseline_metrics,
        "ensemble_metrics": ensemble_metrics,
        "feature_count_after_onehot": int(x_train.shape[1]),
        "n_train_2023": int(len(train_df)),
        "n_valid_2024": int(len(valid_df)),
        "n_test_2025": int(len(test_df)),
    }


def write_summary(summary_rows: list[dict[str, object]], out_dir: Path) -> None:
    summary_df = pd.DataFrame(summary_rows).sort_values("station_id").reset_index(drop=True)
    summary_df.to_csv(out_dir / "soft_voting_top2_summary.csv", index=False)

    md_lines = [
        "# 2359_3643 Soft Voting Retrain Summary",
        "",
        "## Goal",
        "- Re-train only stations 2359 and 3643 from scratch.",
        "- Tune soft-voting weights on 2024 validation.",
        "- Refit base models on 2023+2024 and evaluate on 2025.",
        "",
        "## Data",
        "- Source: second_round_data train(2023-2024) + test(2025).",
        "- Time split: train=2023, valid=2024, test=2025.",
        "",
        "## Ensemble Setup",
        "- Base models: lightgbm (fallback: hist_gbr), xgboost (fallback: extra_trees), random_forest.",
        "- Soft-voting weights searched by grid (step=0.05, sum=1).",
        "- Selection objective: rounded exact-match rate, then bucket accuracy, then RMSE.",
        "",
        "## Test Results (2025)",
        "| station_id | station_name | baseline_model | baseline_exact_rate | ensemble_exact_rate | delta_exact_rate | baseline_bucket_acc | ensemble_bucket_acc | delta_bucket_acc | baseline_rmse | ensemble_rmse | delta_rmse |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        md_lines.append(
            "| {station_id} | {station_name} | {baseline_model} | {baseline_exact:.4f} | {ensemble_exact:.4f} | {delta_exact:+.4f} | {baseline_bucket:.4f} | {ensemble_bucket:.4f} | {delta_bucket:+.4f} | {baseline_rmse:.4f} | {ensemble_rmse:.4f} | {delta_rmse:+.4f} |".format(
                station_id=row["station_id"],
                station_name=row["station_name"],
                baseline_model=row["baseline_model"],
                baseline_exact=row["baseline_exact_rate_rounded"],
                ensemble_exact=row["ensemble_exact_rate_rounded"],
                delta_exact=row["delta_exact_rate_rounded"],
                baseline_bucket=row["baseline_bucket_accuracy"],
                ensemble_bucket=row["ensemble_bucket_accuracy"],
                delta_bucket=row["delta_bucket_accuracy"],
                baseline_rmse=row["baseline_rmse"],
                ensemble_rmse=row["ensemble_rmse"],
                delta_rmse=row["delta_rmse"],
            )
        )

    md_lines.extend(
        [
            "",
            "## Output Files",
            "- `station_2359_valid_model_metrics.csv`, `station_3643_valid_model_metrics.csv`",
            "- `station_2359_soft_weight_grid.csv`, `station_3643_soft_weight_grid.csv`",
            "- `station_2359_best_soft_weight.csv`, `station_3643_best_soft_weight.csv`",
            "- `station_2359_test_model_metrics.csv`, `station_3643_test_model_metrics.csv`",
            "- `station_2359_predictions_2025.csv`, `station_3643_predictions_2025.csv`",
            "- `station_2359_confusion_bucket.csv`, `station_3643_confusion_bucket.csv`",
            "- `station_2359_confusion_exact.csv`, `station_3643_confusion_exact.csv`",
            "- `images/station_2359_confusion_bucket.png`, `images/station_3643_confusion_bucket.png`",
            "- `images/station_2359_confusion_exact.png`, `images/station_3643_confusion_exact.png`",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(md_lines), encoding="utf-8")


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    repo_root = Path(__file__).resolve().parents[2]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "images").mkdir(parents=True, exist_ok=True)

    train_df, test_df = load_source_data(repo_root)
    model_factories = build_model_factories()

    summary_rows: list[dict[str, object]] = []
    for station_id in TARGET_STATIONS:
        split = create_station_split(train_df, test_df, station_id)
        result = run_for_station(split, out_dir=out_dir, model_factories=model_factories)

        summary_rows.append(
            {
                "station_id": result["station_id"],
                "station_name": result["station_name"],
                "baseline_model": result["baseline_model"],
                "baseline_exact_rate_rounded": result["baseline_metrics"]["exact_match_rate_rounded"],
                "ensemble_exact_rate_rounded": result["ensemble_metrics"]["exact_match_rate_rounded"],
                "delta_exact_rate_rounded": result["ensemble_metrics"]["exact_match_rate_rounded"]
                - result["baseline_metrics"]["exact_match_rate_rounded"],
                "baseline_bucket_accuracy": result["baseline_metrics"]["bucket_accuracy_0_1_2_3plus"],
                "ensemble_bucket_accuracy": result["ensemble_metrics"]["bucket_accuracy_0_1_2_3plus"],
                "delta_bucket_accuracy": result["ensemble_metrics"]["bucket_accuracy_0_1_2_3plus"]
                - result["baseline_metrics"]["bucket_accuracy_0_1_2_3plus"],
                "baseline_rmse": result["baseline_metrics"]["rmse"],
                "ensemble_rmse": result["ensemble_metrics"]["rmse"],
                "delta_rmse": result["ensemble_metrics"]["rmse"] - result["baseline_metrics"]["rmse"],
                "best_weight_" + result["model_names"][0]: result["best_weights"][result["model_names"][0]],
                "best_weight_" + result["model_names"][1]: result["best_weights"][result["model_names"][1]],
                "best_weight_" + result["model_names"][2]: result["best_weights"][result["model_names"][2]],
                "feature_count_after_onehot": result["feature_count_after_onehot"],
                "n_train_2023": result["n_train_2023"],
                "n_valid_2024": result["n_valid_2024"],
                "n_test_2025": result["n_test_2025"],
            }
        )

    write_summary(summary_rows, out_dir)
    print("Done. Outputs written to:", out_dir)


if __name__ == "__main__":
    main()
