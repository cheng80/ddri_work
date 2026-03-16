from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    AdaBoostRegressor,
    BaggingRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
    StackingRegressor,
    VotingRegressor,
)
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.tree import DecisionTreeRegressor


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
DATA_DIR_CANDIDATES = [
    Path(os.environ["DDRI_HMW_DATA_DIR"]).expanduser()
    for _ in [0]
    if os.environ.get("DDRI_HMW_DATA_DIR")
] + [
    ROOT / "3조 공유폴더" / "station_hour_bike_flow_2023_2025",
    ROOT / "hmw" / "Data",
]


def resolve_data_paths() -> tuple[Path, Path, Path]:
    for data_dir in DATA_DIR_CANDIDATES:
        train_path = data_dir / "station_hour_bike_flow_train_2023_2024.csv"
        test_path = data_dir / "station_hour_bike_flow_test_2025.csv"
        if train_path.exists() and test_path.exists():
            return data_dir, train_path, test_path
    searched = [str(p) for p in DATA_DIR_CANDIDATES]
    raise FileNotFoundError(
        "train/test 입력 파일을 찾지 못했습니다. 확인한 경로: "
        + ", ".join(searched)
    )


DATA_DIR, TRAIN_PATH, TEST_PATH = resolve_data_paths()

TARGET = "bike_change"
RANDOM_STATE = 42

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


MODEL_NAME_KR = {
    "ridge_기준선": "릿지(기준선)",
    "random_forest": "랜덤포레스트",
    "extra_trees": "엑스트라트리",
    "gradient_boosting": "그래디언트부스팅",
    "adaboost": "아다부스트",
    "bagging_tree": "배깅트리",
    "soft_voting": "소프트보팅회귀",
    "stacking": "스태킹회귀",
}


def log(message: str) -> None:
    print(message, flush=True)


def sample_xy(x: pd.DataFrame, y: pd.Series, n: int | None):
    if n is None or len(x) <= n:
        return x, y
    idx = x.sample(n=n, random_state=RANDOM_STATE).index
    return x.loc[idx], y.loc[idx]


def make_bagging_regressor() -> BaggingRegressor:
    base_tree = DecisionTreeRegressor(random_state=RANDOM_STATE)
    try:
        return BaggingRegressor(
            estimator=base_tree,
            n_estimators=220,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )
    except TypeError:
        return BaggingRegressor(
            base_estimator=base_tree,
            n_estimators=220,
            random_state=RANDOM_STATE,
            n_jobs=1,
        )


def model_configs() -> list[tuple[str, object, int | None]]:
    return [
        ("ridge_기준선", Ridge(alpha=2.0, random_state=RANDOM_STATE), 450_000),
        (
            "random_forest",
            RandomForestRegressor(
                n_estimators=220,
                max_depth=20,
                min_samples_leaf=3,
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
            140_000,
        ),
        (
            "extra_trees",
            ExtraTreesRegressor(
                n_estimators=260,
                max_depth=24,
                min_samples_leaf=2,
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
            140_000,
        ),
        (
            "gradient_boosting",
            GradientBoostingRegressor(
                n_estimators=280,
                learning_rate=0.05,
                max_depth=3,
                random_state=RANDOM_STATE,
            ),
            250_000,
        ),
        (
            "adaboost",
            AdaBoostRegressor(
                n_estimators=260,
                learning_rate=0.05,
                random_state=RANDOM_STATE,
            ),
            200_000,
        ),
        ("bagging_tree", make_bagging_regressor(), 140_000),
        (
            "soft_voting",
            VotingRegressor(
                estimators=[
                    (
                        "rf",
                        RandomForestRegressor(
                            n_estimators=180,
                            max_depth=18,
                            min_samples_leaf=3,
                            random_state=RANDOM_STATE,
                            n_jobs=1,
                        ),
                    ),
                    (
                        "et",
                        ExtraTreesRegressor(
                            n_estimators=220,
                            max_depth=20,
                            min_samples_leaf=2,
                            random_state=RANDOM_STATE,
                            n_jobs=1,
                        ),
                    ),
                    (
                        "gbr",
                        GradientBoostingRegressor(
                            n_estimators=220,
                            learning_rate=0.05,
                            max_depth=3,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
            160_000,
        ),
        (
            "stacking",
            StackingRegressor(
                estimators=[
                    (
                        "rf",
                        RandomForestRegressor(
                            n_estimators=140,
                            max_depth=18,
                            min_samples_leaf=3,
                            random_state=RANDOM_STATE,
                            n_jobs=1,
                        ),
                    ),
                    (
                        "et",
                        ExtraTreesRegressor(
                            n_estimators=180,
                            max_depth=20,
                            min_samples_leaf=2,
                            random_state=RANDOM_STATE,
                            n_jobs=1,
                        ),
                    ),
                    (
                        "gbr",
                        GradientBoostingRegressor(
                            n_estimators=180,
                            learning_rate=0.05,
                            max_depth=3,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ],
                final_estimator=Ridge(alpha=1.2, random_state=RANDOM_STATE),
                cv=3,
                n_jobs=1,
                passthrough=False,
            ),
            120_000,
        ),
    ]


def evaluate(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    rmse = float(root_mean_squared_error(y_true, y_pred))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    std = float(np.std(y_true))
    return {
        "RMSE": rmse,
        "MAE": mae,
        "R2": r2,
        "nRMSE_std": rmse / std if std else np.nan,
        "nMAE_std": mae / std if std else np.nan,
    }


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24).astype("float32")
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24).astype("float32")
    out["weekday_sin"] = np.sin(2 * np.pi * out["weekday"] / 7).astype("float32")
    out["weekday_cos"] = np.cos(2 * np.pi * out["weekday"] / 7).astype("float32")
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12).astype("float32")
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12).astype("float32")
    out["is_weekend"] = (out["weekday"] >= 5).astype("int8")
    out["is_commute_hour"] = out["hour"].isin([7, 8, 9, 17, 18, 19]).astype("int8")
    return out


def add_lag_features(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = pd.concat([train_df, test_df], axis=0, ignore_index=True)
    merged = merged.sort_values(["station_id", "time"]).reset_index(drop=True)
    grp = merged.groupby("station_id", sort=False)

    for col in ["bike_change", "bike_count_index", "rental_count", "return_count"]:
        for lag in [1, 2, 24, 168]:
            merged[f"{col}_lag_{lag}"] = grp[col].shift(lag).astype("float32")

    shift_change = grp["bike_change"].shift(1)
    merged["bike_change_rollmean_24"] = (
        shift_change.groupby(merged["station_id"]).rolling(24).mean().reset_index(level=0, drop=True).astype("float32")
    )
    merged["bike_change_rollstd_24"] = (
        shift_change.groupby(merged["station_id"]).rolling(24).std().reset_index(level=0, drop=True).fillna(0).astype("float32")
    )

    train_len = len(train_df)
    train_feat = merged.iloc[:train_len].copy()
    test_feat = merged.iloc[train_len:].copy()
    return train_feat, test_feat


def prepare_xy(train_df: pd.DataFrame, test_df: pd.DataFrame):
    train_df = add_time_features(train_df)
    test_df = add_time_features(test_df)
    train_df, test_df = add_lag_features(train_df, test_df)

    feature_cols = [
        "station_id",
        "year",
        "month",
        "day",
        "weekday",
        "hour",
        "hour_sin",
        "hour_cos",
        "weekday_sin",
        "weekday_cos",
        "month_sin",
        "month_cos",
        "is_weekend",
        "is_commute_hour",
        "bike_change_lag_1",
        "bike_change_lag_2",
        "bike_change_lag_24",
        "bike_change_lag_168",
        "bike_count_index_lag_1",
        "bike_count_index_lag_24",
        "bike_count_index_lag_168",
        "rental_count_lag_1",
        "rental_count_lag_24",
        "return_count_lag_1",
        "return_count_lag_24",
        "bike_change_rollmean_24",
        "bike_change_rollstd_24",
    ]

    x_train = train_df[feature_cols].copy()
    x_test = test_df[feature_cols].copy()
    y_train = train_df[TARGET].copy()
    y_test = test_df[TARGET].copy()

    med = x_train.median(numeric_only=True)
    x_train = x_train.fillna(med)
    x_test = x_test.fillna(med)
    y_train = y_train.fillna(0)
    y_test = y_test.fillna(0)

    return x_train, y_train, x_test, y_test, test_df[["station_id", "time"]].copy()


def main() -> None:
    t_all0 = time.perf_counter()
    if not TRAIN_PATH.exists() or not TEST_PATH.exists():
        raise FileNotFoundError("train/test flow 파일이 없습니다.")

    log("[1/4] train/test 파일 로드")
    train_df = pd.read_csv(TRAIN_PATH, parse_dates=["time"])
    test_df = pd.read_csv(TEST_PATH, parse_dates=["time"])
    log(f"  train rows={len(train_df):,}, test rows={len(test_df):,}")

    log("[2/4] 빠른 피처 생성(lag/time)")
    x_train, y_train, x_test, y_test, test_meta = prepare_xy(train_df, test_df)
    log(f"  x_train={x_train.shape}, x_test={x_test.shape}")

    log("[3/4] 회귀 앙상블 학습/평가")
    rows: list[dict[str, object]] = []
    fail_rows: list[dict[str, object]] = []
    best_rmse = float("inf")
    best_name_kr = None
    best_pred = None

    configs = model_configs()
    total_models = len(configs)
    for model_idx, (name, model, cap) in enumerate(configs, start=1):
        name_kr = MODEL_NAME_KR.get(name, name)
        log(f"  - [{model_idx}/{total_models}] {name_kr} ...")
        try:
            xf, yf = sample_xy(x_train, y_train, cap)
            t_fit0 = time.perf_counter()
            model.fit(xf, yf)
            fit_s = time.perf_counter() - t_fit0

            t_pr0 = time.perf_counter()
            pred = model.predict(x_test)
            pr_s = time.perf_counter() - t_pr0

            m = evaluate(y_test, pred)
            row = {
                "모델": name_kr,
                "학습행수": len(xf),
                "테스트행수": len(x_test),
                "학습시간(초)": fit_s,
                "예측시간(초)": pr_s,
                **m,
            }
            rows.append(row)
            progress_pct = model_idx / total_models * 100
            log(
                f"    RMSE={m['RMSE']:.6f}, MAE={m['MAE']:.6f}, "
                f"R²={m['R2']:.6f}, progress={progress_pct:.1f}%"
            )

            if m["RMSE"] < best_rmse:
                best_rmse = m["RMSE"]
                best_name_kr = name_kr
                best_pred = pred
        except Exception as e:  # noqa: BLE001
            fail_rows.append({"모델": name_kr, "오류": str(e)})
            progress_pct = model_idx / total_models * 100
            log(f"    실패: {e} | progress={progress_pct:.1f}%")

    result_df = pd.DataFrame(rows).sort_values(["RMSE", "MAE"], ascending=[True, True]).reset_index(drop=True)
    result_df.to_csv(OUT_DIR / "회귀앙상블_모델비교_전체재학습.csv", index=False, encoding="utf-8-sig")
    if fail_rows:
        pd.DataFrame(fail_rows).to_csv(OUT_DIR / "회귀앙상블_학습실패목록.csv", index=False, encoding="utf-8-sig")

    pred_df = test_meta.reset_index(drop=True)
    pred_df["실제값"] = y_test.reset_index(drop=True)
    pred_df["예측값"] = best_pred
    pred_df["절대오차"] = (pred_df["실제값"] - pred_df["예측값"]).abs()
    pred_df.sort_values("절대오차", ascending=False).head(100).to_csv(
        OUT_DIR / "최적모델_오차상위100_전체재학습.csv",
        index=False,
        encoding="utf-8-sig",
    )

    residual = y_test.to_numpy() - best_pred
    residual_df = pd.DataFrame(
        [
            {"항목": "평균잔차", "값": float(np.mean(residual))},
            {"항목": "잔차표준편차", "값": float(np.std(residual))},
            {"항목": "잔차최소", "값": float(np.min(residual))},
            {"항목": "잔차 1사분위", "값": float(np.quantile(residual, 0.25))},
            {"항목": "잔차 중앙값", "값": float(np.median(residual))},
            {"항목": "잔차 3사분위", "값": float(np.quantile(residual, 0.75))},
            {"항목": "잔차최대", "값": float(np.max(residual))},
            {"항목": "최적모델 MAE", "값": float(mean_absolute_error(y_test, best_pred))},
            {"항목": "최적모델 RMSE", "값": float(root_mean_squared_error(y_test, best_pred))},
            {"항목": "최적모델 R²", "값": float(r2_score(y_test, best_pred))},
        ]
    )
    residual_df.to_csv(OUT_DIR / "최적모델_잔차요약_전체재학습.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(11, 6))
    pd_plot = result_df.sort_values("RMSE", ascending=True)
    ax.barh(pd_plot["모델"], pd_plot["RMSE"], color="#2b6cb0")
    ax.set_title("bike_change 회귀 앙상블 비교 (train/test 직접 사용)")
    ax.set_xlabel("RMSE")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "회귀앙상블_RMSE비교_전체재학습.png", dpi=170)
    plt.close(fig)

    elapsed = time.perf_counter() - t_all0
    meta = {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "x_train_shape": list(x_train.shape),
        "x_test_shape": list(x_test.shape),
        "best_model": best_name_kr,
        "best_rmse": float(best_rmse),
        "elapsed_seconds": float(elapsed),
        "input_files": {
            "train": str(TRAIN_PATH),
            "test": str(TEST_PATH),
        },
    }
    (OUT_DIR / "실험메타_전체재학습.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    top3 = result_df.head(3).copy()
    top3_fmt = top3[["모델", "RMSE", "MAE", "R2", "학습시간(초)"]].copy()
    for c in ["RMSE", "MAE", "R2"]:
        top3_fmt[c] = top3_fmt[c].map(lambda v: f"{v:.6f}")
    top3_fmt["학습시간(초)"] = top3_fmt["학습시간(초)"].map(lambda v: f"{v:.2f}")

    lines = [
        "# HMW station-hour 회귀 앙상블 (train/test 직접 사용)",
        "",
        "## 1) 왜 빨라졌는가",
        "",
        f"- `{TRAIN_PATH.name}`, `{TEST_PATH.name}`를 직접 사용",
        "- 이전처럼 전체 raw에서 weather/meta를 재머지하고 전체 피처를 재생성하는 단계 생략",
        "",
        "## 2) 실험 설정",
        "",
        "- 타깃: `bike_change`",
        f"- train rows: `{len(train_df):,}`",
        f"- test rows: `{len(test_df):,}`",
        f"- feature shape: train `{x_train.shape}`, test `{x_test.shape}`",
        "",
        "## 3) 상위 3개 모델 (RMSE 기준)",
        "",
        top3_fmt.to_markdown(index=False),
        "",
        f"- 최적 모델: `{best_name_kr}`",
        f"- 최적 RMSE: `{best_rmse:.6f}`",
        "",
        "## 4) 생성 파일",
        "",
        "- `회귀앙상블_모델비교_전체재학습.csv`",
        "- `최적모델_잔차요약_전체재학습.csv`",
        "- `최적모델_오차상위100_전체재학습.csv`",
        "- `회귀앙상블_RMSE비교_전체재학습.png`",
        "- `실험메타_전체재학습.json`",
    ]
    (OUT_DIR / "분석요약_전체재학습.md").write_text("\n".join(lines), encoding="utf-8")

    log("[4/4] 완료")
    log(result_df.to_csv(index=False))
    log(f"best_model={best_name_kr}, rmse={best_rmse:.6f}")
    log(f"elapsed_sec={elapsed:.2f}")
    log(f"output_dir={OUT_DIR}")


if __name__ == "__main__":
    main()
