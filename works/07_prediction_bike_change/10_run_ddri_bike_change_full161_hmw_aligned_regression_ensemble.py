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
from sklearn.base import clone
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
WORK_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = WORK_DIR / "output" / "data"
IMAGE_DIR = WORK_DIR / "output" / "images"

DATA_DIR_CANDIDATES = [
    Path(os.environ["DDRI_HMW_DATA_DIR"]).expanduser()
    for _ in [0]
    if os.environ.get("DDRI_HMW_DATA_DIR")
] + [
    ROOT / "3조 공유폴더" / "station_hour_bike_flow_2023_2025",
    ROOT / "hmw" / "Data",
]

LOOKUP_PATH_CANDIDATES = [
    ROOT / "cheng80" / "api_output" / "ddri_station_id_api_lookup.csv",
]

TARGET = "bike_change"
RANDOM_STATE = 42
TRAIN_VALID_CUTOFF = pd.Timestamp("2024-01-01")

METRICS_PATH = OUTPUT_DIR / "ddri_bike_change_full161_hmw_aligned_model_metrics.csv"
RESIDUAL_PATH = OUTPUT_DIR / "ddri_bike_change_full161_hmw_aligned_residual_summary.csv"
TOP100_PATH = OUTPUT_DIR / "ddri_bike_change_full161_hmw_aligned_top100_errors.csv"
PLOT_PATH = IMAGE_DIR / "ddri_bike_change_full161_hmw_aligned_rmse.png"
SUMMARY_PATH = WORK_DIR / "ddri_bike_change_full161_hmw_aligned_summary.md"
META_PATH = WORK_DIR / "ddri_bike_change_full161_hmw_aligned_meta.json"

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


def resolve_data_paths() -> tuple[Path, Path, Path]:
    for data_dir in DATA_DIR_CANDIDATES:
        train_path = data_dir / "station_hour_bike_flow_train_2023_2024.csv"
        test_path = data_dir / "station_hour_bike_flow_test_2025.csv"
        if train_path.exists() and test_path.exists():
            return data_dir, train_path, test_path
    searched = [str(p) for p in DATA_DIR_CANDIDATES]
    raise FileNotFoundError("flow train/test 입력 파일을 찾지 못했습니다. 확인 경로: " + ", ".join(searched))


def resolve_lookup_path() -> Path:
    for path in LOOKUP_PATH_CANDIDATES:
        if path.exists():
            return path
    searched = [str(p) for p in LOOKUP_PATH_CANDIDATES]
    raise FileNotFoundError("161개 lookup 파일을 찾지 못했습니다. 확인 경로: " + ", ".join(searched))


DATA_DIR, TRAIN_PATH, TEST_PATH = resolve_data_paths()
LOOKUP_PATH = resolve_lookup_path()


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
    sign_accuracy = float(((pd.Series(y_pred) >= 0) == (y_true.reset_index(drop=True) >= 0)).mean())
    return {
        "RMSE": rmse,
        "MAE": mae,
        "R2": r2,
        "nRMSE_std": rmse / std if std else np.nan,
        "nMAE_std": mae / std if std else np.nan,
        "sign_accuracy": sign_accuracy,
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


FEATURE_COLS = [
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


def prepare_xy(feature_df: pd.DataFrame, medians: pd.Series | None = None):
    x = feature_df[FEATURE_COLS].copy()
    y = feature_df[TARGET].copy()
    if medians is None:
        medians = x.median(numeric_only=True)
    x = x.fillna(medians)
    y = y.fillna(0)
    return x, y, medians


def load_service_station_ids() -> set[int]:
    lookup_df = pd.read_csv(LOOKUP_PATH)
    return set(lookup_df["station_id"].astype(int).tolist())


def load_filtered_flow_csv(path: Path, service_station_ids: set[int]) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    total_read = 0
    total_kept = 0
    for chunk_idx, chunk in enumerate(pd.read_csv(path, parse_dates=["time"], chunksize=300_000), start=1):
        total_read += len(chunk)
        filtered = chunk[chunk["station_id"].isin(service_station_ids)].copy()
        total_kept += len(filtered)
        parts.append(filtered)
        log(
            f"    chunk {chunk_idx:02d}: read_rows={len(chunk):,}, "
            f"kept_rows={len(filtered):,}, kept_cumulative={total_kept:,}"
        )
    if not parts:
        raise ValueError(f"필터 후 데이터가 비었습니다: {path}")
    log(f"    완료: source_rows={total_read:,}, filtered_rows={total_kept:,}")
    return pd.concat(parts, ignore_index=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    t_all0 = time.perf_counter()
    service_station_ids = load_service_station_ids()

    log("[1/5] 원본 flow 로드 + 161개 서비스 대상 필터링")
    train_valid_df = load_filtered_flow_csv(TRAIN_PATH, service_station_ids)
    test_df = load_filtered_flow_csv(TEST_PATH, service_station_ids)
    log(f"  filtered train_valid rows={len(train_valid_df):,}, test rows={len(test_df):,}")
    log(f"  filtered unique stations train_valid={train_valid_df['station_id'].nunique()}, test={test_df['station_id'].nunique()}")

    log("[2/5] HMW 정렬 피처 생성(lag/time)")
    train_valid_df = train_valid_df.sort_values(["station_id", "time"]).reset_index(drop=True)
    test_df = test_df.sort_values(["station_id", "time"]).reset_index(drop=True)
    train_valid_df = add_time_features(train_valid_df)
    test_df = add_time_features(test_df)
    train_valid_feat, test_feat = add_lag_features(train_valid_df, test_df)
    log(f"  feature_cols={len(FEATURE_COLS)}")

    train_2023_feat = train_valid_feat[train_valid_feat["time"] < TRAIN_VALID_CUTOFF].copy()
    valid_2024_feat = train_valid_feat[train_valid_feat["time"] >= TRAIN_VALID_CUTOFF].copy()
    log(f"  train_2023 rows={len(train_2023_feat):,}, validation_2024 rows={len(valid_2024_feat):,}, test_2025 rows={len(test_feat):,}")

    x_train_2023, y_train_2023, med_train_2023 = prepare_xy(train_2023_feat)
    x_valid_2024, y_valid_2024, _ = prepare_xy(valid_2024_feat, med_train_2023)
    x_full_train, y_full_train, med_full = prepare_xy(train_valid_feat)
    x_test_2025, y_test_2025, _ = prepare_xy(test_feat, med_full)
    log(f"  x_train_2023={x_train_2023.shape}, x_valid_2024={x_valid_2024.shape}, x_test_2025={x_test_2025.shape}")

    log("[3/5] 회귀앙상블 학습/평가")
    rows: list[dict[str, object]] = []
    fail_rows: list[dict[str, object]] = []
    best_rmse = float("inf")
    best_name_kr = None
    best_pred = None

    configs = model_configs()
    total_models = len(configs)
    for model_idx, (name, model_proto, cap) in enumerate(configs, start=1):
        name_kr = MODEL_NAME_KR.get(name, name)
        log(f"  - [{model_idx}/{total_models}] {name_kr} ...")
        try:
            model_valid = clone(model_proto)
            xv_fit, yv_fit = sample_xy(x_train_2023, y_train_2023, cap)
            t_fit0 = time.perf_counter()
            model_valid.fit(xv_fit, yv_fit)
            fit_valid_s = time.perf_counter() - t_fit0

            pred_train = model_valid.predict(x_train_2023)
            pred_valid = model_valid.predict(x_valid_2024)
            train_metrics = evaluate(y_train_2023, pred_train)
            valid_metrics = evaluate(y_valid_2024, pred_valid)
            rows.append({
                "model": name_kr,
                "split": "train_2023",
                "fit_context": "fit_2023_only",
                "train_rows_used": len(xv_fit),
                "eval_rows": len(x_train_2023),
                "fit_seconds": fit_valid_s,
                **train_metrics,
            })
            rows.append({
                "model": name_kr,
                "split": "validation_2024",
                "fit_context": "fit_2023_only",
                "train_rows_used": len(xv_fit),
                "eval_rows": len(x_valid_2024),
                "fit_seconds": fit_valid_s,
                **valid_metrics,
            })

            model_test = clone(model_proto)
            xt_fit, yt_fit = sample_xy(x_full_train, y_full_train, cap)
            t_fit1 = time.perf_counter()
            model_test.fit(xt_fit, yt_fit)
            fit_test_s = time.perf_counter() - t_fit1
            pred_test = model_test.predict(x_test_2025)
            test_metrics = evaluate(y_test_2025, pred_test)
            rows.append({
                "model": name_kr,
                "split": "test_2025_refit",
                "fit_context": "fit_2023_2024_full",
                "train_rows_used": len(xt_fit),
                "eval_rows": len(x_test_2025),
                "fit_seconds": fit_test_s,
                **test_metrics,
            })
            progress_pct = model_idx / total_models * 100
            log(
                "    "
                + f"valid RMSE={valid_metrics['RMSE']:.6f}, "
                + f"test RMSE={test_metrics['RMSE']:.6f}, "
                + f"test sign_acc={test_metrics['sign_accuracy']:.4f}, "
                + f"progress={progress_pct:.1f}%"
            )

            if test_metrics["RMSE"] < best_rmse:
                best_rmse = test_metrics["RMSE"]
                best_name_kr = name_kr
                best_pred = pred_test
        except Exception as e:  # noqa: BLE001
            fail_rows.append({"model": name_kr, "error": str(e)})
            progress_pct = model_idx / total_models * 100
            log(f"    실패: {e} | progress={progress_pct:.1f}%")

    result_df = pd.DataFrame(rows)
    result_df.to_csv(METRICS_PATH, index=False, encoding="utf-8-sig")
    if fail_rows:
        pd.DataFrame(fail_rows).to_csv(
            OUTPUT_DIR / "ddri_bike_change_full161_hmw_aligned_failures.csv",
            index=False,
            encoding="utf-8-sig",
        )

    if best_pred is None or best_name_kr is None:
        raise RuntimeError("모든 모델 학습이 실패했습니다.")

    pred_df = test_feat[["station_id", "time"]].reset_index(drop=True).copy()
    pred_df["actual"] = y_test_2025.reset_index(drop=True)
    pred_df["predicted"] = best_pred
    pred_df["absolute_error"] = (pred_df["actual"] - pred_df["predicted"]).abs()
    pred_df.sort_values("absolute_error", ascending=False).head(100).to_csv(TOP100_PATH, index=False, encoding="utf-8-sig")

    residual = pred_df["actual"] - pred_df["predicted"]
    residual_summary = pd.DataFrame(
        {
            "항목": [
                "평균잔차",
                "잔차표준편차",
                "잔차최소",
                "잔차 1사분위",
                "잔차 중앙값",
                "잔차 3사분위",
                "잔차최대",
                "최적모델 MAE",
                "최적모델 RMSE",
                "최적모델 R²",
            ],
            "값": [
                float(residual.mean()),
                float(residual.std()),
                float(residual.min()),
                float(residual.quantile(0.25)),
                float(residual.median()),
                float(residual.quantile(0.75)),
                float(residual.max()),
                float(mean_absolute_error(pred_df["actual"], pred_df["predicted"])),
                float(root_mean_squared_error(pred_df["actual"], pred_df["predicted"])),
                float(r2_score(pred_df["actual"], pred_df["predicted"])),
            ],
        }
    )
    residual_summary.to_csv(RESIDUAL_PATH, index=False, encoding="utf-8-sig")

    test_view = result_df[result_df["split"] == "test_2025_refit"].sort_values(["RMSE", "MAE"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(test_view["model"], test_view["RMSE"], color="#3a78b4")
    ax.invert_yaxis()
    ax.set_title("DDRI bike_change full161 HMW 정렬 회귀앙상블 Test RMSE")
    ax.set_xlabel("RMSE")
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=170)
    plt.close(fig)

    elapsed = time.perf_counter() - t_all0
    meta = {
        "service_station_count": len(service_station_ids),
        "filtered_train_valid_rows": len(train_valid_df),
        "filtered_test_rows": len(test_df),
        "train_2023_rows": len(train_2023_feat),
        "validation_2024_rows": len(valid_2024_feat),
        "test_2025_rows": len(test_feat),
        "x_train_2023_shape": list(x_train_2023.shape),
        "x_valid_2024_shape": list(x_valid_2024.shape),
        "x_full_train_shape": list(x_full_train.shape),
        "x_test_2025_shape": list(x_test_2025.shape),
        "best_model": best_name_kr,
        "best_test_rmse": float(best_rmse),
        "elapsed_seconds": float(elapsed),
        "input_files": {
            "train_valid": str(TRAIN_PATH),
            "test": str(TEST_PATH),
            "lookup": str(LOOKUP_PATH),
        },
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    top3 = test_view.head(3).copy()
    top3_fmt = top3[["model", "RMSE", "MAE", "R2", "sign_accuracy", "fit_seconds"]].copy()
    for c in ["RMSE", "MAE", "R2", "sign_accuracy", "fit_seconds"]:
        top3_fmt[c] = top3_fmt[c].map(lambda v: f"{v:.6f}")
    lines = [
        "# DDRI bike_change full161 HMW 정렬 회귀앙상블 요약",
        "",
        "## 1) 실험 목적",
        "",
        "- `station_hour_bike_flow` 원본 기준 피처 체계를 유지한다",
        "- 서비스 대상 `161개` 대여소만 필터링한다",
        "- `bike_change`를 타깃으로 HMW 정렬 기준 비교 실험을 수행한다",
        "",
        "## 2) 실험 설정",
        "",
        f"- train_valid rows: `{len(train_valid_df):,}`",
        f"- test rows: `{len(test_df):,}`",
        f"- train_2023 rows: `{len(train_2023_feat):,}`",
        f"- validation_2024 rows: `{len(valid_2024_feat):,}`",
        f"- feature shape(train_2023): `{x_train_2023.shape}`",
        f"- feature shape(test_2025): `{x_test_2025.shape}`",
        "",
        "## 3) 상위 3개 모델 (test_2025_refit RMSE 기준)",
        "",
        top3_fmt.to_markdown(index=False),
        "",
        f"- 최적 모델: `{best_name_kr}`",
        f"- 최적 test RMSE: `{best_rmse:.6f}`",
        "",
        "## 4) 생성 파일",
        "",
        f"- `{METRICS_PATH.name}`",
        f"- `{RESIDUAL_PATH.name}`",
        f"- `{TOP100_PATH.name}`",
        f"- `{PLOT_PATH.name}`",
        f"- `{META_PATH.name}`",
    ]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")

    log("[4/5] 결과 파일 저장 완료")
    log(test_view.to_csv(index=False))
    log(f"best_model={best_name_kr}, best_test_rmse={best_rmse:.6f}")
    log(f"elapsed_sec={elapsed:.2f}")
    log(f"output_dir={OUTPUT_DIR}")
    log("[5/5] 완료")


if __name__ == "__main__":
    main()
