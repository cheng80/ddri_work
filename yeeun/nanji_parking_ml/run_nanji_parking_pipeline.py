from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import Ridge


TARGET_COL = "available_spaces"


@dataclass
class SplitFrames:
    train: pd.DataFrame
    valid: pd.DataFrame
    test: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nanji parking availability ML pipeline")
    parser.add_argument("--input", required=True, help="Path to parking CSV")
    parser.add_argument("--output-dir", required=True, help="Directory for outputs")
    return parser.parse_args()


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Input CSV is empty.")

    required_base = {"timestamp", "total_spaces"}
    missing_base = required_base - set(df.columns)
    if missing_base:
        raise ValueError(f"Missing required columns: {sorted(missing_base)}")

    if "available_spaces" not in df.columns and "occupied_spaces" not in df.columns:
        raise ValueError("Input must include either 'available_spaces' or 'occupied_spaces'.")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    if "parking_lot_id" not in df.columns:
        df["parking_lot_id"] = "nanji_main"
    if "parking_lot_name" not in df.columns:
        df["parking_lot_name"] = "난지 한강공원 주차장"
    if "is_holiday" not in df.columns:
        df["is_holiday"] = 0
    if "event_flag" not in df.columns:
        df["event_flag"] = 0

    for col in ["weather_temp_c", "weather_precip_mm", "weather_humidity"]:
        if col not in df.columns:
            df[col] = np.nan

    if "available_spaces" not in df.columns:
        df["available_spaces"] = df["total_spaces"] - df["occupied_spaces"]
    if "occupied_spaces" not in df.columns:
        df["occupied_spaces"] = df["total_spaces"] - df["available_spaces"]

    df["available_spaces"] = pd.to_numeric(df["available_spaces"], errors="coerce")
    df["occupied_spaces"] = pd.to_numeric(df["occupied_spaces"], errors="coerce")
    df["total_spaces"] = pd.to_numeric(df["total_spaces"], errors="coerce")

    df["available_spaces"] = df["available_spaces"].clip(lower=0)
    df["occupied_spaces"] = df["occupied_spaces"].clip(lower=0)
    df["occupancy_rate"] = np.where(
        df["total_spaces"] > 0,
        df["occupied_spaces"] / df["total_spaces"],
        np.nan,
    )
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ts = out["timestamp"]
    out["year"] = ts.dt.year
    out["month"] = ts.dt.month
    out["day"] = ts.dt.day
    out["hour"] = ts.dt.hour
    out["day_of_week"] = ts.dt.dayofweek
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)

    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7)
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12)
    return out


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for lag in [1, 2, 3, 24, 24 * 7]:
        out[f"available_lag_{lag}"] = out[TARGET_COL].shift(lag)

    for window in [3, 6, 24]:
        out[f"available_roll_mean_{window}"] = out[TARGET_COL].shift(1).rolling(window).mean()
        out[f"available_roll_std_{window}"] = out[TARGET_COL].shift(1).rolling(window).std()

    out["occupancy_rate_lag_1"] = out["occupancy_rate"].shift(1)
    return out


def build_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = add_time_features(df)
    out = add_lag_features(out)
    out = out.dropna().reset_index(drop=True)
    numeric_cols = out.select_dtypes(include=[np.number]).columns
    out[numeric_cols] = out[numeric_cols].fillna(out[numeric_cols].median())
    return out


def split_by_time(df: pd.DataFrame) -> SplitFrames:
    n = len(df)
    if n < 30:
        raise ValueError("At least 30 usable rows are needed after feature engineering.")

    train_end = int(n * 0.70)
    valid_end = int(n * 0.85)
    return SplitFrames(
        train=df.iloc[:train_end].copy(),
        valid=df.iloc[train_end:valid_end].copy(),
        test=df.iloc[valid_end:].copy(),
    )


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    exclude = {
        "timestamp",
        "parking_lot_id",
        "parking_lot_name",
        "available_spaces",
        "occupied_spaces",
    }
    return [col for col in df.columns if col not in exclude]


def evaluate(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def clip_predictions(pred: np.ndarray, total_spaces: pd.Series) -> np.ndarray:
    pred = np.asarray(pred, dtype=float)
    clipped = np.clip(pred, 0, total_spaces.to_numpy(dtype=float))
    return clipped


def train_and_compare(split_frames: SplitFrames, feature_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, RandomForestRegressor]:
    train_df = split_frames.train
    valid_df = split_frames.valid
    test_df = split_frames.test

    x_train = train_df[feature_cols]
    y_train = train_df[TARGET_COL]
    x_valid = valid_df[feature_cols]
    y_valid = valid_df[TARGET_COL]
    x_test = test_df[feature_cols]
    y_test = test_df[TARGET_COL]

    baseline_valid = clip_predictions(valid_df["available_lag_1"], valid_df["total_spaces"])
    baseline_test = clip_predictions(test_df["available_lag_1"], test_df["total_spaces"])

    rf = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )
    rf.fit(x_train, y_train)

    ridge = Ridge(alpha=1.0)
    ridge.fit(x_train, y_train)

    model_rows = []
    prediction_frames = []
    candidates = [
        ("baseline_lag1", baseline_valid, baseline_test, None),
        ("random_forest", clip_predictions(rf.predict(x_valid), valid_df["total_spaces"]), clip_predictions(rf.predict(x_test), test_df["total_spaces"]), rf),
        ("ridge", clip_predictions(ridge.predict(x_valid), valid_df["total_spaces"]), clip_predictions(ridge.predict(x_test), test_df["total_spaces"]), None),
    ]

    for model_name, valid_pred, test_pred, _ in candidates:
        valid_metrics = evaluate(y_valid, valid_pred)
        test_metrics = evaluate(y_test, test_pred)
        model_rows.append(
            {
                "model_name": model_name,
                "valid_rmse": valid_metrics["rmse"],
                "valid_mae": valid_metrics["mae"],
                "valid_r2": valid_metrics["r2"],
                "test_rmse": test_metrics["rmse"],
                "test_mae": test_metrics["mae"],
                "test_r2": test_metrics["r2"],
            }
        )
        prediction_frames.append(
            pd.DataFrame(
                {
                    "timestamp": test_df["timestamp"],
                    "parking_lot_id": test_df["parking_lot_id"],
                    "parking_lot_name": test_df["parking_lot_name"],
                    "actual_available_spaces": y_test,
                    "predicted_available_spaces": test_pred,
                    "total_spaces": test_df["total_spaces"],
                    "model_name": model_name,
                }
            )
        )

    metrics_df = pd.DataFrame(model_rows).sort_values(["valid_rmse", "test_rmse"]).reset_index(drop=True)
    predictions_df = pd.concat(prediction_frames, ignore_index=True)
    return metrics_df, predictions_df, rf


def build_feature_importance(model: RandomForestRegressor, feature_cols: list[str]) -> pd.DataFrame:
    importance_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    importance_df["importance_ratio"] = importance_df["importance"] / importance_df["importance"].sum()
    return importance_df.reset_index(drop=True)


def build_db_output(predictions_df: pd.DataFrame, best_model_name: str) -> pd.DataFrame:
    out = predictions_df[predictions_df["model_name"] == best_model_name].copy()
    out["predicted_available_spaces"] = out["predicted_available_spaces"].round().astype(int)
    out["actual_available_spaces"] = out["actual_available_spaces"].round().astype(int)
    out["predicted_occupied_spaces"] = (out["total_spaces"] - out["predicted_available_spaces"]).clip(lower=0).round().astype(int)
    out["predicted_occupancy_rate"] = np.where(
        out["total_spaces"] > 0,
        out["predicted_occupied_spaces"] / out["total_spaces"],
        np.nan,
    )
    out["predicted_for"] = pd.to_datetime(out["timestamp"])
    out["created_at"] = pd.Timestamp.now()
    return out[
        [
            "parking_lot_id",
            "parking_lot_name",
            "predicted_for",
            "actual_available_spaces",
            "predicted_available_spaces",
            "predicted_occupied_spaces",
            "predicted_occupancy_rate",
            "model_name",
            "created_at",
        ]
    ].reset_index(drop=True)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_df = load_data(input_path)
    model_df = build_model_frame(raw_df)
    split_frames = split_by_time(model_df)
    feature_cols = get_feature_columns(model_df)

    metrics_df, predictions_df, rf_model = train_and_compare(split_frames, feature_cols)
    best_model_name = metrics_df.iloc[0]["model_name"]
    db_output_df = build_db_output(predictions_df, best_model_name)
    importance_df = build_feature_importance(rf_model, feature_cols)

    metrics_df.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")
    predictions_df.to_csv(output_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
    db_output_df.to_csv(output_dir / "db_prediction_output.csv", index=False, encoding="utf-8-sig")
    importance_df.to_csv(output_dir / "feature_importance.csv", index=False, encoding="utf-8-sig")

    print("Pipeline completed.")
    print(f"Input rows: {len(raw_df):,}")
    print(f"Usable rows after feature engineering: {len(model_df):,}")
    print(f"Best model: {best_model_name}")
    print(f"Outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
