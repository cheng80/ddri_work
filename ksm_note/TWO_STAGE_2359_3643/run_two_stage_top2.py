from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import confusion_matrix, mean_absolute_error, mean_squared_error, r2_score

try:
    from lightgbm import LGBMClassifier, LGBMRegressor

    HAS_LIGHTGBM = True
except Exception:
    HAS_LIGHTGBM = False


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
    feature_cols = [col for col in candidate_features if col in df.columns]

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
        if col in feature_cols
    ]
    numeric_cols = [col for col in feature_cols if col not in categorical_cols]
    return feature_cols, categorical_cols, numeric_cols


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
        mode = train[col].mode(dropna=True)
        fill = mode.iloc[0] if not mode.empty else 0
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


def to_bucket(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr)
    return np.where(arr <= 0, 0, np.where(arr == 1, 1, np.where(arr == 2, 2, 3)))


def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(float)
    y_pred = np.asarray(y_pred).astype(float)
    true_int = np.rint(y_true).astype(int)
    pred_round = np.rint(np.clip(y_pred, 0, None)).astype(int)

    exact_hits = int((true_int == pred_round).sum())
    exact_rate = float(exact_hits / len(true_int))
    tol1_rate = float((np.abs(true_int - pred_round) <= 1).mean())
    bucket_acc = float((to_bucket(true_int) == to_bucket(pred_round)).mean())
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "exact_match_hits_rounded": exact_hits,
        "exact_match_rate_rounded": exact_rate,
        "tolerance_1_accuracy_rounded": tol1_rate,
        "bucket_accuracy_0_1_2_3plus": bucket_acc,
        "n_samples": int(len(true_int)),
    }


def make_baseline_regressor() -> object:
    if HAS_LIGHTGBM:
        return LGBMRegressor(
            objective="regression",
            n_estimators=700,
            learning_rate=0.04,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    return HistGradientBoostingRegressor(
        max_iter=450,
        learning_rate=0.05,
        max_depth=8,
        l2_regularization=0.1,
        random_state=RANDOM_STATE,
    )


def make_stage1_classifier() -> object:
    if HAS_LIGHTGBM:
        return LGBMClassifier(
            objective="binary",
            n_estimators=600,
            learning_rate=0.04,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    return HistGradientBoostingClassifier(
        max_iter=450,
        learning_rate=0.05,
        max_depth=8,
        l2_regularization=0.1,
        random_state=RANDOM_STATE,
    )


def make_stage2_regressor() -> object:
    if HAS_LIGHTGBM:
        return LGBMRegressor(
            objective="regression",
            n_estimators=700,
            learning_rate=0.04,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=RANDOM_STATE + 7,
            n_jobs=1,
        )
    return HistGradientBoostingRegressor(
        max_iter=450,
        learning_rate=0.05,
        max_depth=8,
        l2_regularization=0.1,
        random_state=RANDOM_STATE + 7,
    )


def tune_two_stage_params(
    y_valid: np.ndarray,
    p_nonzero_valid: np.ndarray,
    pred_positive_valid: np.ndarray,
) -> tuple[pd.DataFrame, pd.Series]:
    rows = []
    thresholds = np.arange(0.10, 0.91, 0.02)
    scales = np.arange(0.70, 1.31, 0.02)
    biases = np.arange(-0.40, 0.41, 0.05)

    for threshold in thresholds:
        mask_nonzero = p_nonzero_valid >= threshold
        for scale in scales:
            scaled_positive = np.clip(pred_positive_valid * scale, 0.0, None)
            for bias in biases:
                positive_pred = np.clip(scaled_positive + bias, 0.0, None)
                pred = np.where(mask_nonzero, positive_pred, 0.0)
                metrics = evaluate_regression(y_valid, pred)
                rows.append(
                    {
                        "threshold_nonzero": round(float(threshold), 4),
                        "scale_positive": round(float(scale), 4),
                        "bias_positive": round(float(bias), 4),
                        **metrics,
                    }
                )

    grid_df = pd.DataFrame(rows)
    best = grid_df.sort_values(
        [
            "exact_match_rate_rounded",
            "tolerance_1_accuracy_rounded",
            "bucket_accuracy_0_1_2_3plus",
            "rmse",
            "mae",
        ],
        ascending=[False, False, False, True, True],
    ).iloc[0]
    return grid_df, best


def apply_two_stage(
    p_nonzero: np.ndarray,
    pred_positive: np.ndarray,
    threshold: float,
    scale: float,
    bias: float,
) -> np.ndarray:
    positive_pred = np.clip(pred_positive * scale + bias, 0.0, None)
    return np.where(p_nonzero >= threshold, positive_pred, 0.0)


def build_confusion_outputs(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    true_int = np.rint(np.asarray(y_true)).astype(int)
    pred_int = np.rint(np.clip(np.asarray(y_pred), 0, None)).astype(int)

    exact_labels = sorted(set(true_int.tolist()) | set(pred_int.tolist()))
    exact_cm = confusion_matrix(true_int, pred_int, labels=exact_labels)
    exact_cm_df = pd.DataFrame(exact_cm, index=exact_labels, columns=exact_labels)
    exact_cm_df.index.name = "actual"
    exact_cm_df.columns.name = "predicted"

    bucket_true = to_bucket(true_int)
    bucket_pred = to_bucket(pred_int)
    bucket_cm = confusion_matrix(bucket_true, bucket_pred, labels=[0, 1, 2, 3])
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
    ax.set_xlabel("예측값")
    ax.set_ylabel("실제값")
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


def train_two_stage_and_evaluate(
    split: StationSplit,
    out_dir: Path,
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
    y_train_nonzero = (y_train > 0).astype(int)
    train_pos_mask = y_train > 0

    baseline_valid_model = make_baseline_regressor()
    baseline_valid_model.fit(x_train, y_train)
    pred_valid_baseline = np.asarray(baseline_valid_model.predict(x_valid), dtype=float)
    baseline_valid_metrics = evaluate_regression(y_valid, pred_valid_baseline)

    stage1_valid_model = make_stage1_classifier()
    stage1_valid_model.fit(x_train, y_train_nonzero)
    p_nonzero_valid = np.asarray(stage1_valid_model.predict_proba(x_valid)[:, 1], dtype=float)

    stage2_valid_model = make_stage2_regressor()
    if int(train_pos_mask.sum()) == 0:
        pred_positive_valid = np.zeros(len(x_valid), dtype=float)
    else:
        stage2_valid_model.fit(x_train.loc[train_pos_mask], y_train[train_pos_mask])
        pred_positive_valid = np.asarray(stage2_valid_model.predict(x_valid), dtype=float)
    pred_positive_valid = np.clip(pred_positive_valid, 0.0, None)

    tuning_grid_df, best_row = tune_two_stage_params(y_valid, p_nonzero_valid, pred_positive_valid)
    tuning_grid_df.to_csv(out_dir / f"station_{split.station_id}_validation_tuning_grid.csv", index=False)
    pd.DataFrame([best_row]).to_csv(out_dir / f"station_{split.station_id}_best_tuned_params.csv", index=False)

    tuned_valid_pred = apply_two_stage(
        p_nonzero=p_nonzero_valid,
        pred_positive=pred_positive_valid,
        threshold=float(best_row["threshold_nonzero"]),
        scale=float(best_row["scale_positive"]),
        bias=float(best_row["bias_positive"]),
    )
    tuned_valid_metrics = evaluate_regression(y_valid, tuned_valid_pred)
    validation_compare_df = pd.DataFrame(
        [
            {"model": "baseline_single_regressor", "split": "validation_2024", **baseline_valid_metrics},
            {"model": "two_stage_tuned", "split": "validation_2024", **tuned_valid_metrics},
        ]
    )
    validation_compare_df.to_csv(out_dir / f"station_{split.station_id}_validation_comparison.csv", index=False)

    train_valid_df = pd.concat([train_df, valid_df], ignore_index=True)
    x_train_valid, x_test = one_hot_align(
        train_df=train_valid_df,
        other_dfs=[test_df],
        feature_cols=feature_cols,
        categorical_cols=categorical_cols,
    )
    y_train_valid = train_valid_df[TARGET_COL].values.astype(float)
    y_test = test_df[TARGET_COL].values.astype(float)

    baseline_test_model = make_baseline_regressor()
    baseline_test_model.fit(x_train_valid, y_train_valid)
    pred_test_baseline = np.asarray(baseline_test_model.predict(x_test), dtype=float)
    baseline_test_metrics = evaluate_regression(y_test, pred_test_baseline)

    y_train_valid_nonzero = (y_train_valid > 0).astype(int)
    train_valid_pos_mask = y_train_valid > 0

    stage1_test_model = make_stage1_classifier()
    stage1_test_model.fit(x_train_valid, y_train_valid_nonzero)
    p_nonzero_test = np.asarray(stage1_test_model.predict_proba(x_test)[:, 1], dtype=float)

    stage2_test_model = make_stage2_regressor()
    if int(train_valid_pos_mask.sum()) == 0:
        pred_positive_test = np.zeros(len(x_test), dtype=float)
    else:
        stage2_test_model.fit(x_train_valid.loc[train_valid_pos_mask], y_train_valid[train_valid_pos_mask])
        pred_positive_test = np.asarray(stage2_test_model.predict(x_test), dtype=float)
    pred_positive_test = np.clip(pred_positive_test, 0.0, None)

    tuned_test_pred = apply_two_stage(
        p_nonzero=p_nonzero_test,
        pred_positive=pred_positive_test,
        threshold=float(best_row["threshold_nonzero"]),
        scale=float(best_row["scale_positive"]),
        bias=float(best_row["bias_positive"]),
    )
    tuned_test_metrics = evaluate_regression(y_test, tuned_test_pred)

    test_compare_df = pd.DataFrame(
        [
            {"model": "baseline_single_regressor", "split": "test_2025", **baseline_test_metrics},
            {"model": "two_stage_tuned", "split": "test_2025", **tuned_test_metrics},
        ]
    )
    test_compare_df.to_csv(out_dir / f"station_{split.station_id}_test_comparison.csv", index=False)

    pred_df = pd.DataFrame(
        {
            "station_id": split.station_id,
            "station_name": split.station_name,
            "date": test_df["date"].dt.strftime("%Y-%m-%d"),
            "hour": test_df["hour"].astype(int),
            "actual_rental_count": np.rint(y_test).astype(int),
            "pred_baseline_continuous": pred_test_baseline,
            "pred_baseline_rounded": np.rint(np.clip(pred_test_baseline, 0, None)).astype(int),
            "pred_two_stage_continuous": tuned_test_pred,
            "pred_two_stage_rounded": np.rint(np.clip(tuned_test_pred, 0, None)).astype(int),
            "pred_nonzero_probability": p_nonzero_test,
            "pred_positive_regressor": pred_positive_test,
            "actual_bucket_0_1_2_3plus": to_bucket(np.rint(y_test).astype(int)),
            "pred_two_stage_bucket_0_1_2_3plus": to_bucket(np.rint(np.clip(tuned_test_pred, 0, None)).astype(int)),
        }
    )
    pred_df.to_csv(out_dir / f"station_{split.station_id}_predictions_2025.csv", index=False)

    exact_cm_df, bucket_cm_df = build_confusion_outputs(y_test, tuned_test_pred)
    exact_cm_df.to_csv(out_dir / f"station_{split.station_id}_confusion_exact.csv")
    bucket_cm_df.to_csv(out_dir / f"station_{split.station_id}_confusion_bucket.csv")

    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    plot_confusion_matrix(
        bucket_cm_df,
        title=f"대여소 {split.station_id} 버킷 혼동행렬 (2단계 튜닝)",
        output_path=img_dir / f"station_{split.station_id}_confusion_bucket.png",
    )
    plot_confusion_matrix(
        exact_cm_df,
        title=f"대여소 {split.station_id} 정수 혼동행렬 (2단계 튜닝)",
        output_path=img_dir / f"station_{split.station_id}_confusion_exact.png",
    )

    return {
        "station_id": split.station_id,
        "station_name": split.station_name,
        "feature_count_after_onehot": int(x_train.shape[1]),
        "n_train_2023": int(len(train_df)),
        "n_valid_2024": int(len(valid_df)),
        "n_test_2025": int(len(test_df)),
        "best_threshold_nonzero": float(best_row["threshold_nonzero"]),
        "best_scale_positive": float(best_row["scale_positive"]),
        "best_bias_positive": float(best_row["bias_positive"]),
        "baseline_valid_metrics": baseline_valid_metrics,
        "tuned_valid_metrics": tuned_valid_metrics,
        "baseline_test_metrics": baseline_test_metrics,
        "tuned_test_metrics": tuned_test_metrics,
    }


def write_summary_files(summary_rows: list[dict[str, object]], out_dir: Path) -> None:
    summary_df = pd.DataFrame(summary_rows).sort_values("station_id").reset_index(drop=True)
    summary_df.to_csv(out_dir / "two_stage_top2_summary.csv", index=False)

    md_lines = [
        "# 2359·3643 2단계 모델 + 튜닝 결과",
        "",
        "## 수행 방식",
        "- 대상: 2359, 3643 대여소만 별도 학습",
        "- 분할: train=2023, valid=2024, test=2025",
        "- 모델 구조: 1단계(0대/양수 분류) + 2단계(양수 건수 회귀)",
        "- 튜닝: valid에서 `threshold_nonzero`, `scale_positive`, `bias_positive` 탐색",
        "- 최종평가: train+valid 재학습 후 test(2025) 평가",
        "",
        "## Test(2025) 결과 요약",
        "| station_id | station_name | baseline exact | two_stage exact | delta exact | baseline ±1 | two_stage ±1 | delta ±1 | baseline bucket | two_stage bucket | delta bucket | baseline rmse | two_stage rmse | delta rmse |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        md_lines.append(
            "| {station_id} | {station_name} | {b_exact:.4f} | {t_exact:.4f} | {d_exact:+.4f} | {b_tol1:.4f} | {t_tol1:.4f} | {d_tol1:+.4f} | {b_bucket:.4f} | {t_bucket:.4f} | {d_bucket:+.4f} | {b_rmse:.4f} | {t_rmse:.4f} | {d_rmse:+.4f} |".format(
                station_id=row["station_id"],
                station_name=row["station_name"],
                b_exact=row["baseline_test_exact_rate_rounded"],
                t_exact=row["two_stage_test_exact_rate_rounded"],
                d_exact=row["delta_test_exact_rate_rounded"],
                b_tol1=row["baseline_test_tol1"],
                t_tol1=row["two_stage_test_tol1"],
                d_tol1=row["delta_test_tol1"],
                b_bucket=row["baseline_test_bucket"],
                t_bucket=row["two_stage_test_bucket"],
                d_bucket=row["delta_test_bucket"],
                b_rmse=row["baseline_test_rmse"],
                t_rmse=row["two_stage_test_rmse"],
                d_rmse=row["delta_test_rmse"],
            )
        )

    md_lines.extend(
        [
            "",
            "## 파일 목록",
            "- `two_stage_top2_summary.csv`",
            "- `station_2359_validation_tuning_grid.csv`, `station_3643_validation_tuning_grid.csv`",
            "- `station_2359_best_tuned_params.csv`, `station_3643_best_tuned_params.csv`",
            "- `station_2359_validation_comparison.csv`, `station_3643_validation_comparison.csv`",
            "- `station_2359_test_comparison.csv`, `station_3643_test_comparison.csv`",
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
    summary_rows: list[dict[str, object]] = []

    for station_id in TARGET_STATIONS:
        split = create_station_split(train_df, test_df, station_id)
        result = train_two_stage_and_evaluate(split, out_dir=out_dir)
        summary_rows.append(
            {
                "station_id": result["station_id"],
                "station_name": result["station_name"],
                "feature_count_after_onehot": result["feature_count_after_onehot"],
                "n_train_2023": result["n_train_2023"],
                "n_valid_2024": result["n_valid_2024"],
                "n_test_2025": result["n_test_2025"],
                "best_threshold_nonzero": result["best_threshold_nonzero"],
                "best_scale_positive": result["best_scale_positive"],
                "best_bias_positive": result["best_bias_positive"],
                "baseline_valid_exact_rate_rounded": result["baseline_valid_metrics"]["exact_match_rate_rounded"],
                "two_stage_valid_exact_rate_rounded": result["tuned_valid_metrics"]["exact_match_rate_rounded"],
                "delta_valid_exact_rate_rounded": result["tuned_valid_metrics"]["exact_match_rate_rounded"]
                - result["baseline_valid_metrics"]["exact_match_rate_rounded"],
                "baseline_valid_tol1": result["baseline_valid_metrics"]["tolerance_1_accuracy_rounded"],
                "two_stage_valid_tol1": result["tuned_valid_metrics"]["tolerance_1_accuracy_rounded"],
                "delta_valid_tol1": result["tuned_valid_metrics"]["tolerance_1_accuracy_rounded"]
                - result["baseline_valid_metrics"]["tolerance_1_accuracy_rounded"],
                "baseline_test_exact_rate_rounded": result["baseline_test_metrics"]["exact_match_rate_rounded"],
                "two_stage_test_exact_rate_rounded": result["tuned_test_metrics"]["exact_match_rate_rounded"],
                "delta_test_exact_rate_rounded": result["tuned_test_metrics"]["exact_match_rate_rounded"]
                - result["baseline_test_metrics"]["exact_match_rate_rounded"],
                "baseline_test_tol1": result["baseline_test_metrics"]["tolerance_1_accuracy_rounded"],
                "two_stage_test_tol1": result["tuned_test_metrics"]["tolerance_1_accuracy_rounded"],
                "delta_test_tol1": result["tuned_test_metrics"]["tolerance_1_accuracy_rounded"]
                - result["baseline_test_metrics"]["tolerance_1_accuracy_rounded"],
                "baseline_test_bucket": result["baseline_test_metrics"]["bucket_accuracy_0_1_2_3plus"],
                "two_stage_test_bucket": result["tuned_test_metrics"]["bucket_accuracy_0_1_2_3plus"],
                "delta_test_bucket": result["tuned_test_metrics"]["bucket_accuracy_0_1_2_3plus"]
                - result["baseline_test_metrics"]["bucket_accuracy_0_1_2_3plus"],
                "baseline_test_rmse": result["baseline_test_metrics"]["rmse"],
                "two_stage_test_rmse": result["tuned_test_metrics"]["rmse"],
                "delta_test_rmse": result["tuned_test_metrics"]["rmse"] - result["baseline_test_metrics"]["rmse"],
            }
        )

    write_summary_files(summary_rows, out_dir)
    print("Done. Outputs written to:", out_dir)


if __name__ == "__main__":
    main()
