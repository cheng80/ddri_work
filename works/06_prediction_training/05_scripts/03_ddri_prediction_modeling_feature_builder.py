from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/cheng80/Desktop/ddri_work")


@dataclass(frozen=True)
class ModelingSpec:
    # 각 데이터셋별로 정본 입력 위치와 모델링용 출력 위치를 묶어 둔다.
    name: str
    canonical_dir: Path
    output_dir: Path


SPECS = [
    ModelingSpec(
        name="rep15",
        canonical_dir=ROOT / "3조 공유폴더" / "대표대여소_예측데이터_15개" / "canonical_data",
        output_dir=ROOT / "3조 공유폴더" / "대표대여소_예측데이터_15개" / "modeling_data",
    ),
    ModelingSpec(
        name="full161",
        canonical_dir=ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "canonical_data",
        output_dir=ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "modeling_data",
    ),
]

MISSING_BASE_COLS = [
    "bike_change_lag_1",
    "bike_change_lag_24",
    "bike_change_lag_168",
    "bike_change_rollmean_24",
    "bike_change_rollstd_24",
    "bike_change_rollmean_168",
    "bike_change_rollstd_168",
    "bike_change_trend_1_24",
    "bike_change_trend_24_168",
]


def add_missing_flags_and_fill(df: pd.DataFrame) -> pd.DataFrame:
    # 정본의 구조적 결측은 그대로 보존하는 것이 원칙이지만,
    # 학습용 데이터에서는 모델이 결측 자체를 구분할 수 있도록
    # `_missing` 플래그를 추가한 뒤 원값은 0으로 대체한다.
    #
    # 여기서 0 대체를 쓰는 이유는:
    # 1) 선형 모델류도 바로 받을 수 있게 하기 위해서이고
    # 2) 트리 모델에서도 missing_flag와 함께 해석할 수 있게 하기 위해서다.
    out = df.copy()
    for col in MISSING_BASE_COLS:
        flag_col = f"{col}_missing"
        out[flag_col] = out[col].isna().astype("int8")
        out[col] = out[col].fillna(0).astype("float32")
    return out


def build_one(spec: ModelingSpec) -> dict[str, object]:
    # 데이터셋별 출력 폴더를 먼저 만든다.
    spec.output_dir.mkdir(parents=True, exist_ok=True)

    # 정본은 2023~2024, 2025 두 파일로 존재하므로 이를 읽어 온다.
    train_path = spec.canonical_dir / "ddri_prediction_canonical_train_2023_2024.csv"
    test_path = spec.canonical_dir / "ddri_prediction_canonical_test_2025.csv"
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # 연도 분할을 위해 날짜형으로 바꾼다.
    train_df["date"] = pd.to_datetime(train_df["date"])
    test_df["date"] = pd.to_datetime(test_df["date"])

    # 학습 정책은 2023 학습, 2024 검증, 2025 테스트이므로
    # 정본 파일에서 다시 연도 기준으로 나눈다.
    train_2023 = train_df[train_df["date"].dt.year == 2023].copy()
    valid_2024 = train_df[train_df["date"].dt.year == 2024].copy()
    test_2025 = test_df.copy()

    # 구조적 결측이 남아 있는 lag/rolling/trend 컬럼에만
    # missing flag와 0 대체를 적용한다.
    train_2023 = add_missing_flags_and_fill(train_2023)
    valid_2024 = add_missing_flags_and_fill(valid_2024)
    test_2025 = add_missing_flags_and_fill(test_2025)

    # 저장 파일에서는 날짜를 다시 문자열로 맞춰 팀원이 열어 보기 쉽게 둔다.
    for frame in [train_2023, valid_2024, test_2025]:
        frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")

    # 산출물은 학습 스크립트가 바로 읽을 수 있도록 연도별 파일로 고정 저장한다.
    train_out = spec.output_dir / "ddri_prediction_modeling_train_2023.csv"
    valid_out = spec.output_dir / "ddri_prediction_modeling_valid_2024.csv"
    test_out = spec.output_dir / "ddri_prediction_modeling_test_2025.csv"
    meta_out = spec.output_dir / "ddri_prediction_modeling_meta.json"

    train_2023.to_csv(train_out, index=False, encoding="utf-8-sig")
    valid_2024.to_csv(valid_out, index=False, encoding="utf-8-sig")
    test_2025.to_csv(test_out, index=False, encoding="utf-8-sig")

    meta = {
        "name": spec.name,
        "canonical_dir": str(spec.canonical_dir),
        "output_dir": str(spec.output_dir),
        "target_primary": "bike_change_raw",
        "target_secondary": "bike_change_deseasonalized",
        "missing_flag_base_cols": MISSING_BASE_COLS,
        "imputation": "0 fill on lag/rolling/trend columns with explicit missing flags",
        "train_rows": int(len(train_2023)),
        "valid_rows": int(len(valid_2024)),
        "test_rows": int(len(test_2025)),
    }
    meta_out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    # 대표 15개와 전체 161개를 한 번에 재생성할 수 있도록 일괄 실행한다.
    metas = [build_one(spec) for spec in SPECS]
    print(json.dumps(metas, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
