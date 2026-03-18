from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"

TRAIN_PATH = DATA_DIR / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
TEST_PATH = DATA_DIR / "ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv"

TARGET_COL = "bike_change_raw"
WEIGHT_COL = "sample_weight"
DROP_COLS = ["date"]


def prepare_xy(df: pd.DataFrame, with_weight: bool) -> tuple[pd.DataFrame, pd.Series, pd.Series | None]:
    drop_cols = [TARGET_COL, *DROP_COLS]
    if with_weight:
        drop_cols.append(WEIGHT_COL)

    X = df.drop(columns=drop_cols)
    y = df[TARGET_COL]
    sample_weight = df[WEIGHT_COL] if with_weight else None
    return X, y, sample_weight


def main() -> None:
    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)

    X_train, y_train, sample_weight = prepare_xy(train_df, with_weight=True)
    X_test, y_test, _ = prepare_xy(test_df, with_weight=False)

    model = RandomForestRegressor(
        n_estimators=120,
        max_depth=18,
        min_samples_leaf=3,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train, sample_weight=sample_weight)

    pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, pred, squared=False)
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)

    print("train_path:", TRAIN_PATH.as_posix())
    print("test_path :", TEST_PATH.as_posix())
    print("X_train shape:", X_train.shape)
    print("X_test shape :", X_test.shape)
    print("sample_weight range:", float(sample_weight.min()), float(sample_weight.max()))
    print("rmse:", float(rmse))
    print("mae :", float(mae))
    print("r2  :", float(r2))


if __name__ == "__main__":
    main()
