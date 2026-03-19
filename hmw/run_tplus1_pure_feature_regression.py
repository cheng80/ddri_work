from __future__ import annotations

import os
import json
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
ASSET_DIR = REPORT_DIR / "tplus1_pure_feature_assets"

TRAIN_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_train_2023.parquet"
VALID_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_valid_2024.parquet"
TEST_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_test_2025.parquet"
FEATURE_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_features.csv"
CORR_PATH = DATA_DIR / "station_hour_bike_change_tplus1_pure_feature_target_correlation.csv"

FINAL_METRICS_PATH = DATA_DIR / "tplus1_pure_feature_final_metrics.csv"
MODEL_BENCHMARK_PATH = DATA_DIR / "tplus1_pure_feature_model_benchmark.csv"
CLUSTER_BEST_PATH = DATA_DIR / "tplus1_pure_feature_cluster_best_models.csv"
CLUSTER_COMPARE_PATH = DATA_DIR / "tplus1_pure_feature_cluster_comparison.csv"
FEATURE_IMPORTANCE_PATH = DATA_DIR / "tplus1_pure_feature_global_feature_importance.csv"
CLUSTER_FEATURE_IMPORTANCE_PATH = DATA_DIR / "tplus1_pure_feature_cluster_feature_importance.csv"
META_PATH = DATA_DIR / "tplus1_pure_feature_model_meta.json"
PREDICTION_PATH = DATA_DIR / "tplus1_pure_feature_test_predictions.parquet"

REPORT_MD = REPORT_DIR / "tplus1_pure_feature_model_report.md"
REPORT_PDF = REPORT_DIR / "tplus1_pure_feature_model_report.pdf"

RANDOM_STATE = base.RANDOM_STATE

REPORT_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


@dataclass
class ModelSpec:
    name: str
    kind: str
    builder: callable
    train_sample: int | None
    notes: str


def load_split(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    if "target_time" in df.columns:
        df["target_time"] = pd.to_datetime(df["target_time"])
    return df.sort_values(["station_id", "time"]).reset_index(drop=True)


def feature_columns(df: pd.DataFrame) -> list[str]:
    features = pd.read_csv(FEATURE_PATH)["feature"].tolist()
    return [col for col in features if col in df.columns]


def model_specs() -> list[ModelSpec]:
    from lightgbm import LGBMRegressor
    from xgboost import XGBRegressor

    return [
        ModelSpec(
            name="histgbm_balanced",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.04,
                max_depth=10,
                max_iter=340,
                min_samples_leaf=60,
                l2_regularization=0.10,
                random_state=RANDOM_STATE,
            ),
            train_sample=220_000,
            notes="histgbm balanced",
        ),
        ModelSpec(
            name="histgbm_deep",
            kind="sklearn",
            builder=lambda: HistGradientBoostingRegressor(
                learning_rate=0.035,
                max_depth=14,
                max_iter=420,
                min_samples_leaf=38,
                l2_regularization=0.05,
                random_state=RANDOM_STATE,
            ),
            train_sample=220_000,
            notes="histgbm deep",
        ),
        ModelSpec(
            name="lightgbm_balanced",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                learning_rate=0.045,
                n_estimators=420,
                max_depth=10,
                num_leaves=63,
                min_child_samples=40,
                subsample=0.85,
                colsample_bytree=0.85,
                reg_alpha=0.05,
                reg_lambda=0.35,
                objective="regression",
                random_state=RANDOM_STATE,
                n_jobs=1,
                verbosity=-1,
            ),
            train_sample=320_000,
            notes="lightgbm balanced",
        ),
        ModelSpec(
            name="lightgbm_leafy",
            kind="lightgbm",
            builder=lambda: LGBMRegressor(
                learning_rate=0.035,
                n_estimators=520,
                max_depth=12,
                num_leaves=127,
                min_child_samples=30,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_alpha=0.02,
                reg_lambda=0.22,
                objective="regression",
                random_state=RANDOM_STATE,
                n_jobs=1,
                verbosity=-1,
            ),
            train_sample=320_000,
            notes="lightgbm leafy",
        ),
        ModelSpec(
            name="xgboost_balanced",
            kind="xgboost",
            builder=lambda: XGBRegressor(
                n_estimators=420,
                learning_rate=0.04,
                max_depth=8,
                min_child_weight=4,
                reg_alpha=0.05,
                reg_lambda=1.2,
                subsample=0.85,
                colsample_bytree=0.85,
                tree_method="hist",
                objective="reg:squarederror",
                random_state=RANDOM_STATE,
                n_jobs=1,
                verbosity=0,
            ),
            train_sample=320_000,
            notes="xgboost balanced",
        ),
        ModelSpec(
            name="xgboost_regularized",
            kind="xgboost",
            builder=lambda: XGBRegressor(
                n_estimators=520,
                learning_rate=0.03,
                max_depth=7,
                min_child_weight=6,
                reg_alpha=0.12,
                reg_lambda=2.0,
                gamma=0.08,
                subsample=0.82,
                colsample_bytree=0.82,
                tree_method="hist",
                objective="reg:squarederror",
                random_state=RANDOM_STATE,
                n_jobs=1,
                verbosity=0,
            ),
            train_sample=320_000,
            notes="xgboost regularized",
        ),
        ModelSpec(
            name="extra_trees",
            kind="sklearn",
            builder=lambda: ExtraTreesRegressor(
                n_estimators=220,
                max_depth=24,
                min_samples_leaf=2,
                n_jobs=1,
                random_state=RANDOM_STATE,
            ),
            train_sample=180_000,
            notes="extra trees",
        ),
        ModelSpec(
            name="random_forest",
            kind="sklearn",
            builder=lambda: RandomForestRegressor(
                n_estimators=220,
                max_depth=22,
                min_samples_leaf=3,
                n_jobs=1,
                random_state=RANDOM_STATE,
            ),
            train_sample=180_000,
            notes="random forest",
        ),
    ]


def fit_predict(spec: ModelSpec, X_train: pd.DataFrame, y_train: pd.Series, X_eval: pd.DataFrame) -> tuple[object, np.ndarray]:
    model = spec.builder()
    train_X, train_y = base.sample_train(X_train, y_train, spec.train_sample)
    model.fit(train_X, train_y)
    pred = model.predict(X_eval)
    return model, pred


def benchmark_models(X_train: pd.DataFrame, y_train: pd.Series, X_valid: pd.DataFrame, y_valid: pd.Series) -> tuple[pd.DataFrame, ModelSpec]:
    rows = []
    best_spec = None
    best_r2 = -np.inf
    for spec in model_specs():
        _, pred = fit_predict(spec, X_train, y_train, X_valid)
        metrics = base.evaluate_predictions(y_valid, pred)
        rows.append({"model_name": spec.name, **metrics, "notes": spec.notes})
        if metrics["r2"] > best_r2:
            best_r2 = metrics["r2"]
            best_spec = spec
    result = pd.DataFrame(rows).sort_values(["r2", "rmse", "mae"], ascending=[False, True, True]).reset_index(drop=True)
    return result, best_spec


def evaluate_all_splits(model: object, X_train: pd.DataFrame, y_train: pd.Series, X_valid: pd.DataFrame, y_valid: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    rows = []
    for split_name, X, y in [
        ("train", X_train, y_train),
        ("valid", X_valid, y_valid),
        ("test", X_test, y_test),
    ]:
        pred = model.predict(X)
        rows.append({"split": split_name, **base.evaluate_predictions(y, pred)})
    return pd.DataFrame(rows)


def compute_global_importance(model: object, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    sample_X = X_test.sample(n=min(5000, len(X_test)), random_state=RANDOM_STATE)
    sample_y = y_test.loc[sample_X.index]
    imp = permutation_importance(
        model,
        sample_X,
        sample_y,
        n_repeats=5,
        random_state=RANDOM_STATE,
        scoring="r2",
    )
    return (
        pd.DataFrame(
            {
                "feature": X_test.columns,
                "importance_mean": imp.importances_mean,
                "importance_std": imp.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )


def cluster_specialists(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    global_pred_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cluster_rows = []
    compare_rows = []
    importance_rows = []
    clusters = sorted(c for c in train_df["cluster"].dropna().unique().tolist() if c >= 0)

    for cluster_id in clusters:
        tr = train_df.loc[train_df["cluster"] == cluster_id].copy()
        va = valid_df.loc[valid_df["cluster"] == cluster_id].copy()
        te = test_df.loc[test_df["cluster"] == cluster_id].copy()
        if min(len(tr), len(va), len(te)) < 2000:
            continue

        X_train = tr[feature_cols]
        y_train = tr["target_bike_change_t_plus_1"]
        X_valid = va[feature_cols]
        y_valid = va["target_bike_change_t_plus_1"]
        X_test = te[feature_cols]
        y_test = te["target_bike_change_t_plus_1"]

        bench, best_spec = benchmark_models(X_train, y_train, X_valid, y_valid)
        best_model, pred_test = fit_predict(best_spec, pd.concat([X_train, X_valid]), pd.concat([y_train, y_valid]), X_test)
        test_metrics = base.evaluate_predictions(y_test, pred_test)
        cluster_rows.append(
            {
                "cluster": int(cluster_id),
                "best_model": best_spec.name,
                **test_metrics,
                "train_rows": len(tr),
                "valid_rows": len(va),
                "test_rows": len(te),
            }
        )

        global_cluster = global_pred_df.loc[global_pred_df["cluster"] == cluster_id]
        specialist_cluster = te[["cluster"]].copy()
        specialist_cluster["y_true"] = y_test.to_numpy()
        specialist_cluster["y_pred"] = pred_test
        compare_rows.append(
            {
                "cluster": int(cluster_id),
                "global_rmse": base.evaluate_predictions(global_cluster["y_true"], global_cluster["y_pred"])["rmse"],
                "global_mae": base.evaluate_predictions(global_cluster["y_true"], global_cluster["y_pred"])["mae"],
                "global_r2": base.evaluate_predictions(global_cluster["y_true"], global_cluster["y_pred"])["r2"],
                "specialist_rmse": test_metrics["rmse"],
                "specialist_mae": test_metrics["mae"],
                "specialist_r2": test_metrics["r2"],
            }
        )

        sample_X = X_test.sample(n=min(3000, len(X_test)), random_state=RANDOM_STATE)
        sample_y = y_test.loc[sample_X.index]
        imp = permutation_importance(
            best_model,
            sample_X,
            sample_y,
            n_repeats=4,
            random_state=RANDOM_STATE,
            scoring="r2",
        )
        imp_df = pd.DataFrame(
            {
                "cluster": int(cluster_id),
                "feature": feature_cols,
                "importance_mean": imp.importances_mean,
                "importance_std": imp.importances_std,
            }
        ).sort_values("importance_mean", ascending=False)
        importance_rows.append(imp_df.head(15))

    cluster_best_df = pd.DataFrame(cluster_rows).sort_values("cluster").reset_index(drop=True)
    cluster_compare_df = pd.DataFrame(compare_rows).sort_values("cluster").reset_index(drop=True)
    cluster_importance_df = pd.concat(importance_rows, ignore_index=True) if importance_rows else pd.DataFrame(columns=["cluster", "feature", "importance_mean", "importance_std"])
    return cluster_best_df, cluster_compare_df, cluster_importance_df


def save_plots(metrics_df: pd.DataFrame, benchmark_df: pd.DataFrame, importance_df: pd.DataFrame, cluster_best_df: pd.DataFrame) -> list[Path]:
    paths: list[Path] = []

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(metrics_df["split"], metrics_df["r2"], color=["#5B8FF9", "#61DDAA", "#65789B"])
    ax.set_title("Train / Valid / Test R²")
    ax.set_ylabel("R²")
    fig.tight_layout()
    p = ASSET_DIR / "split_r2.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    fig, ax = plt.subplots(figsize=(8, 4))
    top = benchmark_df.head(8)
    ax.bar(top["model_name"], top["r2"], color="#5B8FF9")
    ax.set_title("Validation R² by Model")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    p = ASSET_DIR / "model_benchmark_r2.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    fig, ax = plt.subplots(figsize=(8, 5))
    top_imp = importance_df.head(15).iloc[::-1]
    ax.barh(top_imp["feature"], top_imp["importance_mean"], color="#61DDAA")
    ax.set_title("Global Feature Importance")
    fig.tight_layout()
    p = ASSET_DIR / "global_feature_importance.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    if not cluster_best_df.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(cluster_best_df["cluster"].astype(str), cluster_best_df["r2"], color="#F6BD16")
        ax.set_title("Cluster Test R²")
        ax.set_xlabel("Cluster")
        fig.tight_layout()
        p = ASSET_DIR / "cluster_test_r2.png"
        fig.savefig(p, dpi=180)
        plt.close(fig)
        paths.append(p)

    return paths


def build_report(metrics_df: pd.DataFrame, benchmark_df: pd.DataFrame, importance_df: pd.DataFrame, cluster_best_df: pd.DataFrame, corr_df: pd.DataFrame, feature_cols: list[str], best_model_name: str, plot_paths: list[Path]) -> None:
    top_corr = corr_df.head(12)
    top_features = importance_df.head(12)
    lines = [
        "# 6시 정보로 7시를 예측하는 t+1 회귀 결과",
        "",
        "## 분석 정의",
        "- 입력 시점: 현재 시각 t까지 확보 가능한 정보",
        "- 예측 대상: 다음 1시간 뒤 시점 t+1의 `bike_change`",
        "- 데이터 분할: train=2023, valid=2024, test=2025",
        "- 제외 기준: target 시점의 관측값, `bike_change` 직접 변환값, lag/rolling 기반 시계열 feature 제외",
        "",
        "## 최종 선택 모델",
        f"- 글로벌 최종 모델: `{best_model_name}`",
        f"- 최종 feature 수: `{len(feature_cols)}`",
        "",
        "## Train / Valid / Test 성능",
        "",
        "| split | rmse | mae | r2 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in metrics_df.itertuples(index=False):
        lines.append(f"| {row.split} | {row.rmse:.4f} | {row.mae:.4f} | {row.r2:.4f} |")

    lines.extend(
        [
            "",
            "## Validation 모델 비교 상위",
            "",
            "| model | rmse | mae | r2 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in benchmark_df.head(8).itertuples(index=False):
        lines.append(f"| {row.model_name} | {row.rmse:.4f} | {row.mae:.4f} | {row.r2:.4f} |")

    lines.extend(
        [
            "",
            "## 타깃과의 상관계수 상위",
            "",
            "| feature | corr |",
            "| --- | ---: |",
        ]
    )
    for row in top_corr.itertuples(index=False):
        lines.append(f"| {row.feature} | {row.pearson_corr_with_target:.4f} |")

    lines.extend(
        [
            "",
            "## 전역 중요도 상위",
            "",
            "| feature | importance_mean |",
            "| --- | ---: |",
        ]
    )
    for row in top_features.itertuples(index=False):
        lines.append(f"| {row.feature} | {row.importance_mean:.6f} |")

    if not cluster_best_df.empty:
        lines.extend(
            [
                "",
                "## Cluster별 최적 모델",
                "",
                "| cluster | best_model | rmse | mae | r2 |",
                "| ---: | --- | ---: | ---: | ---: |",
            ]
        )
        for row in cluster_best_df.itertuples(index=False):
            lines.append(f"| {row.cluster} | {row.best_model} | {row.rmse:.4f} | {row.mae:.4f} | {row.r2:.4f} |")

    lines.extend(
        [
            "",
            "## 사용한 핵심 feature 범주",
            "- 현재 시점 날씨: `temperature`, `humidity`, `precipitation`, `wind_speed`, `is_rainy`, `heavy_rain`",
            "- 정류소 고정 특성: `dock_total`, `lcd_count`, `qr_count`, `is_qr_mixed`, `lat`, `lon`",
            "- 다음 시각 캘린더 정보: `target_hour`, `target_weekday`, `target_month`, `target_*_sin/cos`",
            "- 외부 정적 feature: `cluster`, 생활인구/유입비율/교통접근성 계열",
            "",
            "## 해석",
            "- 이번 버전은 7시 실제 관측값을 feature에 쓰지 않도록 다시 구성한 안전한 t+1 예측 구조입니다.",
            "- 성능이 이전 직접 row 예측보다 낮아질 수 있지만, 운영 시점의 실제 사용 조건과는 더 잘 맞습니다.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    with PdfPages(REPORT_PDF) as pdf:
        for path in plot_paths:
            img = plt.imread(path)
            fig, ax = plt.subplots(figsize=(11.69, 8.27))
            ax.imshow(img)
            ax.axis("off")
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def main() -> None:
    train_df = load_split(TRAIN_PATH)
    valid_df = load_split(VALID_PATH)
    test_df = load_split(TEST_PATH)
    feature_cols = feature_columns(train_df)

    X_train = train_df[feature_cols]
    y_train = train_df["target_bike_change_t_plus_1"]
    X_valid = valid_df[feature_cols]
    y_valid = valid_df["target_bike_change_t_plus_1"]
    X_test = test_df[feature_cols]
    y_test = test_df["target_bike_change_t_plus_1"]

    benchmark_df, best_spec = benchmark_models(X_train, y_train, X_valid, y_valid)
    best_model, _ = fit_predict(best_spec, pd.concat([X_train, X_valid]), pd.concat([y_train, y_valid]), X_test)
    metrics_df = evaluate_all_splits(best_model, X_train, y_train, X_valid, y_valid, X_test, y_test)
    importance_df = compute_global_importance(best_model, X_test, y_test)

    global_test_pred = best_model.predict(X_test)
    pred_df = test_df[["station_id", "time", "target_time", "cluster"]].copy()
    pred_df["y_true"] = y_test.to_numpy()
    pred_df["y_pred"] = global_test_pred

    cluster_best_df, cluster_compare_df, cluster_importance_df = cluster_specialists(
        train_df,
        valid_df,
        test_df,
        feature_cols,
        pred_df,
    )

    benchmark_df.to_csv(MODEL_BENCHMARK_PATH, index=False, encoding="utf-8-sig")
    metrics_df.to_csv(FINAL_METRICS_PATH, index=False, encoding="utf-8-sig")
    importance_df.to_csv(FEATURE_IMPORTANCE_PATH, index=False, encoding="utf-8-sig")
    cluster_best_df.to_csv(CLUSTER_BEST_PATH, index=False, encoding="utf-8-sig")
    cluster_compare_df.to_csv(CLUSTER_COMPARE_PATH, index=False, encoding="utf-8-sig")
    cluster_importance_df.to_csv(CLUSTER_FEATURE_IMPORTANCE_PATH, index=False, encoding="utf-8-sig")
    pred_df.to_parquet(PREDICTION_PATH, index=False)

    corr_df = pd.read_csv(CORR_PATH)
    plot_paths = save_plots(metrics_df, benchmark_df, importance_df, cluster_best_df)
    build_report(metrics_df, benchmark_df, importance_df, cluster_best_df, corr_df, feature_cols, best_spec.name, plot_paths)

    META_PATH.write_text(
        json.dumps(
            {
                "task_definition": "predict bike_change at t+1 using only information available at time t",
                "best_model": best_spec.name,
                "feature_count": len(feature_cols),
                "train_rows": int(len(train_df)),
                "valid_rows": int(len(valid_df)),
                "test_rows": int(len(test_df)),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
