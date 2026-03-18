from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
TRAIN_PATH = DATA_DIR / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
TEST_PATH = DATA_DIR / "ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv"
OUT_DIR = BASE_DIR / "outputs"

TARGET_COL = "bike_change_raw"
WEIGHT_COL = "sample_weight"
DATE_COL = "date"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)
    train[DATE_COL] = pd.to_datetime(train[DATE_COL])
    test[DATE_COL] = pd.to_datetime(test[DATE_COL])
    return train, test


def split_data(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_split = train_df[train_df[DATE_COL].dt.year.eq(2023)].copy()
    valid_split = train_df[train_df[DATE_COL].dt.year.eq(2024)].copy()
    test_split = test_df.copy()
    return train_split, valid_split, test_split


def prepare_xy(df: pd.DataFrame, has_weight: bool) -> tuple[pd.DataFrame, pd.Series, pd.Series | None]:
    df = df[df[TARGET_COL].notna()].copy()
    if has_weight:
        df = df[df[WEIGHT_COL].notna()].copy()

    drop_cols = [TARGET_COL, DATE_COL]
    if has_weight:
        drop_cols.append(WEIGHT_COL)

    X = df.drop(columns=drop_cols)
    y = df[TARGET_COL]
    w = df[WEIGHT_COL] if has_weight else None
    return X, y, w


def evaluate(y_true: pd.Series, pred: pd.Series) -> dict[str, float]:
    return {
        "rmse": float(mean_squared_error(y_true, pred) ** 0.5),
        "mae": float(mean_absolute_error(y_true, pred)),
        "r2": float(r2_score(y_true, pred)),
    }


def build_pipeline(feature_names: list[str]) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                feature_names,
            )
        ],
        remainder="drop",
    )

    model = Ridge(alpha=2.0, random_state=42)
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("ridge", model),
        ]
    )


def coefficient_table(model: Pipeline, feature_names: list[str]) -> pd.DataFrame:
    ridge = model.named_steps["ridge"]
    coef = ridge.coef_
    coef_df = pd.DataFrame(
        {
            "feature": feature_names,
            "standardized_coefficient": coef,
            "abs_standardized_coefficient": pd.Series(coef).abs(),
        }
    ).sort_values("abs_standardized_coefficient", ascending=False)
    return coef_df.reset_index(drop=True)


def build_report(
    train_rows: int,
    valid_rows: int,
    test_rows: int,
    score_df: pd.DataFrame,
    coef_df: pd.DataFrame,
    intercept: float,
) -> str:
    top_pos = coef_df.sort_values("standardized_coefficient", ascending=False).head(10)
    top_neg = coef_df.sort_values("standardized_coefficient", ascending=True).head(10)

    lines: list[str] = []
    lines.append("# 선형 회귀 계수 보고서")
    lines.append("")
    lines.append("## 1. 분석 설정")
    lines.append(f"- 데이터: `{TRAIN_PATH.as_posix()}`, `{TEST_PATH.as_posix()}`")
    lines.append("- 분할: 2023년=train, 2024년=valid, 2025년=test")
    lines.append(f"- 행 수: train={train_rows:,}, valid={valid_rows:,}, test={test_rows:,}")
    lines.append(f"- 타깃: `{TARGET_COL}`")
    lines.append(f"- 학습 가중치: `{WEIGHT_COL}`")
    lines.append("- 모델: Ridge(alpha=2.0), median imputation + standardization")
    lines.append("")
    lines.append("## 2. 성능")
    lines.append("")
    lines.append(score_df.to_markdown(index=False))
    lines.append("")
    lines.append(f"## 3. 절편")
    lines.append("")
    lines.append(f"- intercept: `{intercept:.6f}`")
    lines.append("")
    lines.append("## 4. 양(+)의 영향이 큰 feature")
    lines.append("")
    lines.append(top_pos.to_markdown(index=False))
    lines.append("")
    lines.append("## 5. 음(-)의 영향이 큰 feature")
    lines.append("")
    lines.append(top_neg.to_markdown(index=False))
    lines.append("")
    lines.append("## 6. 해석 주의사항")
    lines.append("- 표준화 계수이므로 절댓값이 클수록 타깃에 미치는 선형 영향력이 크다고 볼 수 있습니다.")
    lines.append("- 이는 인과효과가 아니라, 현재 데이터와 분할 기준에서 관측된 선형 관계입니다.")
    lines.append("- 계수 부호는 다른 feature를 함께 통제한 상태에서의 방향입니다.")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df, test_df = load_data()
    train_split, valid_split, test_split = split_data(train_df, test_df)

    X_train, y_train, w_train = prepare_xy(train_split, has_weight=True)
    X_valid, y_valid, _ = prepare_xy(valid_split, has_weight=True)
    X_test, y_test, _ = prepare_xy(test_split, has_weight=False)

    feature_names = X_train.columns.tolist()
    model = build_pipeline(feature_names)
    model.fit(X_train, y_train, ridge__sample_weight=w_train)

    scores = []
    for split_name, X_split, y_split in [
        ("train", X_train, y_train),
        ("valid", X_valid, y_valid),
        ("test", X_test, y_test),
    ]:
        pred = model.predict(X_split)
        scores.append({"split": split_name, **evaluate(y_split, pred)})

    score_df = pd.DataFrame(scores)
    coef_df = coefficient_table(model, feature_names)
    intercept = float(model.named_steps["ridge"].intercept_)

    score_df.to_csv(OUT_DIR / "linear_regression_scores.csv", index=False, encoding="utf-8-sig")
    coef_df.to_csv(OUT_DIR / "linear_regression_coefficients.csv", index=False, encoding="utf-8-sig")

    meta = {
        "train_path": TRAIN_PATH.as_posix(),
        "test_path": TEST_PATH.as_posix(),
        "feature_count": len(feature_names),
        "features": feature_names,
        "target_col": TARGET_COL,
        "weight_col": WEIGHT_COL,
        "intercept": intercept,
    }
    (OUT_DIR / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "linear_regression_report.md").write_text(
        build_report(len(X_train), len(X_valid), len(X_test), score_df, coef_df, intercept),
        encoding="utf-8",
    )

    print(score_df.to_string(index=False))
    print(coef_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
