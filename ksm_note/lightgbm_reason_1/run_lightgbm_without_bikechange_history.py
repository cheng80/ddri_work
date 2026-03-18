from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
OUT_DIR = BASE_DIR / "outputs"

TRAIN_PATH = DATA_DIR / "ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv"
TEST_PATH = DATA_DIR / "ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv"

TARGET_COL = "bike_change_raw"
WEIGHT_COL = "sample_weight"
DATE_COL = "date"
REMOVE_FEATURES = [
    "bike_change_lag_1",
    "bike_change_rollmean_24",
    "bike_change_rollstd_24",
    "bike_change_rollmean_168",
    "bike_change_rollstd_168",
]
CATEGORICAL_COLS = ["station_id", "hour", "weekday", "month", "holiday", "cluster"]

BASELINE_SCORES = {
    "valid": {"rmse": 0.354179, "mae": 0.149206, "r2": 0.935107},
    "test": {"rmse": 0.317459, "mae": 0.131086, "r2": 0.934917},
}


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

    drop_cols = [TARGET_COL, DATE_COL, *REMOVE_FEATURES]
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


def fit_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    w_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
) -> lgb.LGBMRegressor:
    X_train_fit = X_train.copy()
    X_valid_fit = X_valid.copy()
    cat_cols = [c for c in CATEGORICAL_COLS if c in X_train_fit.columns]

    for col in cat_cols:
        X_train_fit[col] = X_train_fit[col].astype("category")
        X_valid_fit[col] = X_valid_fit[col].astype("category")

    model = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=800,
        learning_rate=0.05,
        num_leaves=63,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_samples=50,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(
        X_train_fit,
        y_train,
        sample_weight=w_train,
        eval_set=[(X_valid_fit, y_valid)],
        eval_metric="l2",
        categorical_feature=cat_cols,
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
    )
    return model


def predict_scores(
    model: lgb.LGBMRegressor,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> pd.DataFrame:
    rows = []
    for split_name, X_split, y_split in [
        ("train", X_train, y_train),
        ("valid", X_valid, y_valid),
        ("test", X_test, y_test),
    ]:
        X_eval = X_split.copy()
        cat_cols = [c for c in CATEGORICAL_COLS if c in X_eval.columns]
        for col in cat_cols:
            X_eval[col] = X_eval[col].astype("category")
        scores = evaluate(y_split, model.predict(X_eval))
        rows.append({"split": split_name, **scores})
    return pd.DataFrame(rows)


def make_comparison(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["valid", "test"]:
        current = scores[scores["split"].eq(split)].iloc[0]
        base = BASELINE_SCORES[split]
        rows.append(
            {
                "split": split,
                "baseline_rmse": base["rmse"],
                "new_rmse": current["rmse"],
                "rmse_change": current["rmse"] - base["rmse"],
                "baseline_mae": base["mae"],
                "new_mae": current["mae"],
                "mae_change": current["mae"] - base["mae"],
                "baseline_r2": base["r2"],
                "new_r2": current["r2"],
                "r2_change": current["r2"] - base["r2"],
            }
        )
    return pd.DataFrame(rows)


def save_score_plot(scores: pd.DataFrame) -> Path:
    path = OUT_DIR / "lightgbm_without_history_scores.png"
    long_df = scores.melt(id_vars=["split"], value_vars=["rmse", "mae", "r2"], var_name="metric", value_name="value")
    plt.figure(figsize=(9, 5.2))
    sns.barplot(data=long_df, x="split", y="value", hue="metric", palette=["#c26a2e", "#5d8aa8", "#4f7942"])
    plt.title("LightGBM Without bike_change-history Features")
    plt.xlabel("")
    plt.ylabel("score")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def save_comparison_plot(comp: pd.DataFrame) -> Path:
    path = OUT_DIR / "baseline_vs_without_history_r2.png"
    plot_df = comp.melt(
        id_vars=["split"],
        value_vars=["baseline_r2", "new_r2"],
        var_name="model_version",
        value_name="r2",
    )
    plt.figure(figsize=(7, 4.8))
    sns.barplot(data=plot_df, x="split", y="r2", hue="model_version", palette=["#1f4e79", "#c26a2e"])
    plt.title("R2 Comparison: Baseline vs Without bike_change-history")
    plt.xlabel("")
    plt.ylabel("r2")
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def build_report(scores: pd.DataFrame, comp: pd.DataFrame, feature_names: list[str], img_scores: Path, img_comp: Path) -> str:
    lines: list[str] = []
    lines.append("# LightGBM 재실험 보고서: bike_change 파생 feature 제거")
    lines.append("")
    lines.append("## 1. 실험 목적")
    lines.append("- LightGBM의 매우 높은 성능이 `bike_change` 과거 이력 파생 feature에 과도하게 의존한 결과인지 확인한다.")
    lines.append("- 아래 5개 feature를 제거하고 다시 학습한다.")
    lines.append("")
    lines.append(f"- 제거 feature: `{', '.join(REMOVE_FEATURES)}`")
    lines.append("")
    lines.append("## 2. 데이터 분할")
    lines.append("- train: 2023년")
    lines.append("- valid: 2024년")
    lines.append("- test: 2025년")
    lines.append("- train에는 기존 `sample_weight`를 동일하게 사용")
    lines.append("")
    lines.append(f"## 3. 남은 학습 feature ({len(feature_names)}개)")
    lines.append("")
    lines.append(f"`{', '.join(feature_names)}`")
    lines.append("")
    lines.append("## 4. 재실험 성능")
    lines.append("")
    lines.append(scores.to_markdown(index=False))
    lines.append("")
    lines.append(f"![scores]({img_scores.name})")
    lines.append("")
    lines.append("## 5. 기존 LightGBM 대비 변화")
    lines.append("")
    lines.append(comp.to_markdown(index=False))
    lines.append("")
    lines.append(f"![comparison]({img_comp.name})")
    lines.append("")
    lines.append("## 6. 해석")
    valid_row = comp[comp["split"].eq("valid")].iloc[0]
    test_row = comp[comp["split"].eq("test")].iloc[0]
    lines.append(
        f"- valid 기준 R2는 `{valid_row['baseline_r2']:.6f}` -> `{valid_row['new_r2']:.6f}`로 변했다."
    )
    lines.append(
        f"- test 기준 R2는 `{test_row['baseline_r2']:.6f}` -> `{test_row['new_r2']:.6f}`로 변했다."
    )
    lines.append("- 만약 성능이 크게 떨어졌다면, 기존 고성능은 과거 타깃 이력 feature의 영향이 매우 컸다는 뜻이다.")
    lines.append("- 반대로 성능이 여전히 높다면, 순수한 시간/기상/수요 수준 feature만으로도 충분한 설명력이 있다는 뜻이다.")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    train_df, test_df = load_data()
    train_split, valid_split, test_split = split_data(train_df, test_df)

    X_train, y_train, w_train = prepare_xy(train_split, has_weight=True)
    X_valid, y_valid, _ = prepare_xy(valid_split, has_weight=True)
    X_test, y_test, _ = prepare_xy(test_split, has_weight=False)

    model = fit_model(X_train, y_train, w_train, X_valid, y_valid)
    scores = predict_scores(model, X_train, y_train, X_valid, y_valid, X_test, y_test)
    comp = make_comparison(scores)

    scores.to_csv(OUT_DIR / "lightgbm_without_history_scores.csv", index=False, encoding="utf-8-sig")
    comp.to_csv(OUT_DIR / "lightgbm_without_history_comparison.csv", index=False, encoding="utf-8-sig")

    img_scores = save_score_plot(scores)
    img_comp = save_comparison_plot(comp)

    report = build_report(scores, comp, X_train.columns.tolist(), img_scores, img_comp)
    report_path = OUT_DIR / "lightgbm_without_history_report.md"
    report_path.write_text(report, encoding="utf-8")

    meta = {
        "train_path": TRAIN_PATH.as_posix(),
        "test_path": TEST_PATH.as_posix(),
        "removed_features": REMOVE_FEATURES,
        "remaining_feature_count": len(X_train.columns),
        "best_iteration": int(model.best_iteration_) if getattr(model, "best_iteration_", None) else None,
    }
    (OUT_DIR / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(scores.to_string(index=False))
    print(comp.to_string(index=False))


if __name__ == "__main__":
    main()
