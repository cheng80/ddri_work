from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import StackingRegressor, VotingRegressor
from sklearn.linear_model import Ridge

try:
    from lightgbm import LGBMRegressor
except Exception:  # pragma: no cover
    LGBMRegressor = None

try:
    from catboost import CatBoostRegressor
except Exception:  # pragma: no cover
    CatBoostRegressor = None


ROOT = Path("/Users/cheng80/Desktop/ddri_work")


@dataclass(frozen=True)
class RunSpec:
    # 각 데이터셋별 학습 입력과 결과 출력 경로를 묶는다.
    name: str
    modeling_dir: Path
    output_dir: Path


SPECS = {
    "rep15": RunSpec(
        name="rep15",
        modeling_dir=ROOT / "3조 공유폴더" / "대표대여소_예측데이터_15개" / "modeling_data",
        output_dir=ROOT / "3조 공유폴더" / "대표대여소_예측데이터_15개" / "training_runs",
    ),
    "full161": RunSpec(
        name="full161",
        modeling_dir=ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "modeling_data",
        output_dir=ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "training_runs",
    ),
}

EXCLUDE_COLS = {
    "date",
    "station_name",
    "station_group",
    "rental_count",
    "bike_change_raw",
    "bike_change_deseasonalized",
}


def metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    # 모든 실험에서 RMSE, MAE, R²를 같이 저장하기로 했으므로
    # 지표 계산은 공통 함수로 고정한다.
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "rmse": float(np.sqrt(mse)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def candidate_models():
    # 현재 비교 후보는 LightGBM, CatBoost, Stacking, SoftVoting으로 고정한다.
    # 일부 라이브러리가 없을 수 있으므로 import 성공 여부를 먼저 확인한다.
    models = []
    lightgbm_model = None
    catboost_model = None

    if LGBMRegressor is not None:
        lightgbm_model = LGBMRegressor(
            objective="regression",
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        models.append(("LightGBM_RMSE", lightgbm_model))

    if CatBoostRegressor is not None:
        catboost_model = CatBoostRegressor(
            loss_function="RMSE",
            iterations=400,
            learning_rate=0.05,
            depth=6,
            random_seed=42,
            verbose=False,
        )
        models.append(("CatBoost_RMSE", catboost_model))

    stacking_estimators = []
    if LGBMRegressor is not None:
        stacking_estimators.append(
            (
                "lgbm",
                LGBMRegressor(
                    objective="regression",
                    n_estimators=250,
                    learning_rate=0.05,
                    num_leaves=31,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                ),
            )
        )
    if CatBoostRegressor is not None:
        stacking_estimators.append(
            (
                "cat",
                CatBoostRegressor(
                    loss_function="RMSE",
                    iterations=300,
                    learning_rate=0.05,
                    depth=6,
                    random_seed=42,
                    verbose=False,
                ),
            )
        )
    if len(stacking_estimators) >= 2:
        models.append(
            (
                "StackingRegressor",
                StackingRegressor(
                    estimators=stacking_estimators,
                    final_estimator=Ridge(alpha=1.0),
                    passthrough=False,
                ),
            )
        )
        models.append(
            (
                "SoftVotingRegressor",
                VotingRegressor(estimators=stacking_estimators),
            )
        )

    if not models:
        raise RuntimeError("LightGBM 또는 CatBoost가 설치되어 있지 않아 후보 모델을 만들 수 없습니다.")
    return models


def build_feature_cols(df: pd.DataFrame) -> list[str]:
    # 타깃과 식별/설명용 컬럼은 제외하고 실제 입력 피처만 남긴다.
    return [c for c in df.columns if c not in EXCLUDE_COLS]


def run(spec: RunSpec, target_col: str) -> dict[str, object]:
    # 결과 폴더를 먼저 만든다.
    spec.output_dir.mkdir(parents=True, exist_ok=True)

    # 무샘플링 baseline cycle은 modeling_data 세 파일을 그대로 읽는다.
    train_df = pd.read_csv(spec.modeling_dir / "ddri_prediction_modeling_train_2023.csv")
    valid_df = pd.read_csv(spec.modeling_dir / "ddri_prediction_modeling_valid_2024.csv")
    test_df = pd.read_csv(spec.modeling_dir / "ddri_prediction_modeling_test_2025.csv")

    # 타깃 결측은 학습/평가에 사용할 수 없으므로 해당 행만 제외한다.
    # 여기서의 제외는 샘플링이 아니라, 타깃 계산 불가 행 제거다.
    train_df = train_df[train_df[target_col].notna()].copy()
    valid_df = valid_df[valid_df[target_col].notna()].copy()
    test_df = test_df[test_df[target_col].notna()].copy()

    # 같은 피처 집합으로 train, valid, test를 맞춘다.
    feature_cols = build_feature_cols(train_df)
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_valid = valid_df[feature_cols]
    y_valid = valid_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    # 2024 validation에서 모든 후보 모델을 비교해 선택 지표를 만든다.
    selection_rows = []
    for name, model in candidate_models():
        model.fit(X_train, y_train)
        pred = model.predict(X_valid)
        row = {"model": name, **metrics(y_valid, pred)}
        selection_rows.append(row)

    # 우선순위는 RMSE, 그다음 MAE, 마지막으로 R²다.
    selection_df = pd.DataFrame(selection_rows).sort_values(["rmse", "mae", "r2"], ascending=[True, True, False]).reset_index(drop=True)
    best_name = selection_df.iloc[0]["model"]

    # 선택이 끝난 뒤에만 2023+2024 전체로 다시 학습해 2025를 평가한다.
    final_X = pd.concat([X_train, X_valid], ignore_index=True)
    final_y = pd.concat([y_train, y_valid], ignore_index=True)
    final_model = dict(candidate_models())[best_name]
    final_model.fit(final_X, final_y)
    test_pred = final_model.predict(X_test)
    test_metrics = metrics(y_test, test_pred)

    # 결과 파일은 선택 지표, 최종 테스트 지표, 예측값, 메타 정보로 나눠 저장한다.
    selection_path = spec.output_dir / f"ddri_{spec.name}_{target_col}_selection_metrics.csv"
    final_path = spec.output_dir / f"ddri_{spec.name}_{target_col}_test_metrics.csv"
    pred_path = spec.output_dir / f"ddri_{spec.name}_{target_col}_test_predictions.csv"
    meta_path = spec.output_dir / f"ddri_{spec.name}_{target_col}_training_meta.json"

    selection_df.to_csv(selection_path, index=False, encoding="utf-8-sig")
    pd.DataFrame([{"model": best_name, **test_metrics}]).to_csv(final_path, index=False, encoding="utf-8-sig")
    pred_df = test_df[["station_id", "date", "hour", target_col]].copy()
    pred_df["prediction"] = test_pred
    pred_df.to_csv(pred_path, index=False, encoding="utf-8-sig")

    meta = {
        "dataset": spec.name,
        "target": target_col,
        "policy": {
            "train": "2023",
            "validation": "2024",
            "refit": "2023+2024",
            "test": "2025",
        },
        "feature_count": len(feature_cols),
        "feature_cols": feature_cols,
        "train_rows_used": int(len(train_df)),
        "valid_rows_used": int(len(valid_df)),
        "test_rows_used": int(len(test_df)),
        "best_model": best_name,
        "selection_output": str(selection_path),
        "test_metrics_output": str(final_path),
        "test_predictions_output": str(pred_path),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    # 노트북과 CLI 양쪽에서 같은 방식으로 실행할 수 있게 인자를 받는다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=sorted(SPECS.keys()), default="rep15")
    parser.add_argument("--target", choices=["bike_change_raw", "bike_change_deseasonalized"], default="bike_change_raw")
    args = parser.parse_args()
    result = run(SPECS[args.dataset], args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
