from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/cheng80/Desktop/ddri_work")


@dataclass(frozen=True)
class DatasetSpec:
    # 데이터셋별 입력 원천과 최종 정본 출력 위치를 함께 관리한다.
    name: str
    train_source: Path
    test_source: Path
    output_dir: Path
    warmup_event_source: Path | None = None


SPECS = [
    DatasetSpec(
        name="rep15",
        # 현재 재생성 기준 입력은 삭제 전 스냅샷을 보관해 둔 OLD_DATA를 사용한다.
        train_source=ROOT / "3조 공유폴더" / "OLD_DATA" / "대표대여소_예측데이터_15개" / "raw_data" / "ddri_prediction_long_train_2023_2024.csv",
        test_source=ROOT / "3조 공유폴더" / "OLD_DATA" / "대표대여소_예측데이터_15개" / "raw_data" / "ddri_prediction_long_test_2025.csv",
        output_dir=ROOT / "3조 공유폴더" / "대표대여소_예측데이터_15개" / "canonical_data",
        warmup_event_source=ROOT / "3조 공유폴더" / "2022년 12월 강남구 따릉이 이용정보" / "서울특별시 공공자전거 대여이력 정보_2212.csv",
    ),
    DatasetSpec(
        name="full161",
        train_source=ROOT / "3조 공유폴더" / "OLD_DATA" / "군집별 데이터_전체 스테이션" / "full_data" / "ddri_prediction_long_train_2023_2024.csv",
        test_source=ROOT / "3조 공유폴더" / "OLD_DATA" / "군집별 데이터_전체 스테이션" / "full_data" / "ddri_prediction_long_test_2025.csv",
        output_dir=ROOT / "3조 공유폴더" / "군집별 데이터_전체 스테이션" / "canonical_data",
    ),
]

KEY_COLS = ["station_id", "date", "hour"]
SEASONAL_KEY_COLS = ["station_id", "weekday", "hour"]


def validate_input(df: pd.DataFrame, source: Path) -> None:
    # 정본 생성 전 최소 필수 컬럼과 키 중복 여부를 먼저 확인한다.
    required = {"station_id", "date", "hour", "rental_count", "weekday"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{source} missing columns: {missing}")
    dup_count = int(df.duplicated(KEY_COLS).sum())
    if dup_count:
        raise ValueError(f"{source} duplicate rows on {KEY_COLS}: {dup_count}")


def build_cluster_master(train_df: pd.DataFrame) -> pd.DataFrame:
    # 군집 라벨은 train 스냅샷을 기준 마스터로 본다.
    # station_id별 cluster가 하나로 고정돼 있어야 이후 train/test에 같은 라벨을 다시 붙일 수 있다.
    cluster_master = train_df[["station_id", "cluster"]].drop_duplicates().copy()
    dup_station = cluster_master["station_id"].duplicated().sum()
    if dup_station:
        raise ValueError(f"cluster master has duplicated station_id rows: {int(dup_station)}")
    return cluster_master


def apply_cluster_master(df: pd.DataFrame, cluster_master: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    # train 기준 cluster 매핑을 다시 붙여 test의 흔들린 라벨을 보정한다.
    original_cluster = df["cluster"].copy() if "cluster" in df.columns else pd.Series([pd.NA] * len(df))
    out = df.drop(columns=["cluster"], errors="ignore").merge(
        cluster_master,
        on="station_id",
        how="left",
        validate="many_to_one",
    )
    if out["cluster"].isna().any():
        missing_station_count = int(out.loc[out["cluster"].isna(), "station_id"].nunique())
        raise ValueError(f"cluster master missing station_id for {missing_station_count} stations")
    changed_rows = int((original_cluster.fillna(-9999).to_numpy() != out["cluster"].fillna(-9999).to_numpy()).sum())
    return out, changed_rows


def add_bike_change(df: pd.DataFrame) -> pd.DataFrame:
    # bike_change의 기본 정의는 같은 station_id 안에서 rental_count의 시차 차분이다.
    out = df.copy()
    out = out.sort_values(KEY_COLS).reset_index(drop=True)
    out["bike_change_raw"] = (
        out.groupby("station_id", sort=False)["rental_count"].diff().astype("float32")
    )
    return out


def build_rep15_warmup_frame(spec: DatasetSpec, train_df: pd.DataFrame) -> pd.DataFrame:
    # rep15는 2022-12 대여이력을 계산용 히스토리로만 붙여
    # 2023 시작부 lag/rolling 결측을 줄인다.
    if spec.warmup_event_source is None:
        return pd.DataFrame()
    station_base = (
        train_df[["station_id", "station_name", "station_group", "cluster", "mapped_dong_code"]]
        .drop_duplicates("station_id")
        .copy()
    )
    weather_cols = ["date", "hour", "weekday", "month", "holiday", "temperature", "humidity", "precipitation", "wind_speed"]
    weather_base = (
        train_df.loc[train_df["date"].astype(str).str.startswith("2023-12-"), weather_cols]
        .drop_duplicates(["date", "hour"])
        .copy()
    )
    weather_base["date"] = pd.to_datetime(weather_base["date"])
    weather_base["date"] = weather_base["date"] - pd.DateOffset(years=1)

    event_df = pd.read_csv(
        spec.warmup_event_source,
        encoding="cp949",
        usecols=["대여일시", "대여 대여소번호", "이용시간(분)", "이용거리(M)"],
    )
    event_df["대여일시"] = pd.to_datetime(event_df["대여일시"], errors="coerce")
    event_df["대여 대여소번호"] = pd.to_numeric(event_df["대여 대여소번호"], errors="coerce")
    event_df["이용시간(분)"] = pd.to_numeric(event_df["이용시간(분)"], errors="coerce")
    event_df["이용거리(M)"] = pd.to_numeric(event_df["이용거리(M)"], errors="coerce")
    event_df = event_df[
        event_df["대여 대여소번호"].isin(station_base["station_id"])
        & event_df["대여일시"].notna()
        & (event_df["이용시간(분)"] > 0)
        & (event_df["이용거리(M)"] > 0)
    ].copy()
    event_df["date"] = event_df["대여일시"].dt.normalize()
    event_df["hour"] = event_df["대여일시"].dt.hour

    agg = (
        event_df.groupby(["대여 대여소번호", "date", "hour"], as_index=False)
        .size()
        .rename(columns={"대여 대여소번호": "station_id", "size": "rental_count"})
    )

    grid = pd.MultiIndex.from_product(
        [
            sorted(station_base["station_id"].tolist()),
            pd.date_range("2022-12-01", "2022-12-31", freq="D"),
            range(24),
        ],
        names=["station_id", "date", "hour"],
    ).to_frame(index=False)
    out = grid.merge(agg, on=["station_id", "date", "hour"], how="left")
    out["rental_count"] = out["rental_count"].fillna(0).astype(int)
    out = out.merge(station_base, on="station_id", how="left", validate="many_to_one")
    out = out.merge(weather_base, on=["date", "hour"], how="left", validate="many_to_one")
    out["weekday"] = out["date"].dt.weekday
    out["month"] = out["date"].dt.month
    out["holiday"] = out["holiday"].fillna(0).astype(int)
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    cols = train_df.columns.tolist()
    return out[cols]


def build_seasonal_map(train_df: pd.DataFrame) -> pd.DataFrame:
    # 시간패턴 평균은 2023 구간에서만 계산해 이후 전체 구간에 적용한다.
    train_2023 = add_bike_change(train_df)
    train_2023 = train_2023[train_2023["date"] < pd.Timestamp("2024-01-01")].copy()
    seasonal_map = (
        train_2023.dropna(subset=["bike_change_raw"])
        .groupby(SEASONAL_KEY_COLS, as_index=False)["bike_change_raw"]
        .mean()
        .rename(columns={"bike_change_raw": "seasonal_mean_2023"})
    )
    return seasonal_map


def apply_canonical_transform(df: pd.DataFrame, seasonal_map: pd.DataFrame) -> pd.DataFrame:
    # 정본의 핵심 파생 컬럼을 한 번에 생성한다.
    # 순서는 bike_change -> seasonal merge -> deseasonalized -> lag/rolling/trend다.
    out = add_bike_change(df)
    out = out.merge(seasonal_map, on=SEASONAL_KEY_COLS, how="left", validate="many_to_one")
    missing_mask = out["seasonal_mean_2023"].isna()
    bad_missing = missing_mask & out["bike_change_raw"].notna()
    if bad_missing.any():
        missing_count = int(bad_missing.sum())
        raise ValueError(f"seasonal_mean_2023 missing rows with non-null bike_change_raw: {missing_count}")
    out["rental_count_deseasonalized"] = (
        out["rental_count"] - out["seasonal_mean_2023"]
    ).astype("float32")
    out["bike_change_deseasonalized"] = (
        out["bike_change_raw"] - out["seasonal_mean_2023"]
    ).astype("float32")
    grouped = out.groupby("station_id", sort=False)["bike_change_raw"]
    shifted = grouped.shift(1)
    out["bike_change_lag_1"] = grouped.shift(1).astype("float32")
    out["bike_change_lag_24"] = grouped.shift(24).astype("float32")
    out["bike_change_lag_168"] = grouped.shift(168).astype("float32")
    out["bike_change_rollmean_24"] = (
        shifted.groupby(out["station_id"]).rolling(24, min_periods=24).mean().reset_index(level=0, drop=True).astype("float32")
    )
    out["bike_change_rollstd_24"] = (
        shifted.groupby(out["station_id"]).rolling(24, min_periods=24).std().reset_index(level=0, drop=True).astype("float32")
    )
    out["bike_change_rollmean_168"] = (
        shifted.groupby(out["station_id"]).rolling(168, min_periods=168).mean().reset_index(level=0, drop=True).astype("float32")
    )
    out["bike_change_rollstd_168"] = (
        shifted.groupby(out["station_id"]).rolling(168, min_periods=168).std().reset_index(level=0, drop=True).astype("float32")
    )
    out["bike_change_trend_1_24"] = (out["bike_change_lag_1"] - out["bike_change_lag_24"]).astype("float32")
    out["bike_change_trend_24_168"] = (out["bike_change_lag_24"] - out["bike_change_lag_168"]).astype("float32")
    return out


def build_one(spec: DatasetSpec) -> dict[str, object]:
    # 데이터셋 하나를 읽고, 변환하고, 저장하고, 메타를 남긴다.
    spec.output_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(spec.train_source)
    test_df = pd.read_csv(spec.test_source)
    validate_input(train_df, spec.train_source)
    validate_input(test_df, spec.test_source)

    # train 기준 station_id -> cluster 매핑을 마스터로 고정한다.
    cluster_master = build_cluster_master(train_df)
    train_df, train_cluster_changed_rows = apply_cluster_master(train_df, cluster_master)
    test_df, test_cluster_changed_rows = apply_cluster_master(test_df, cluster_master)

    train_df["date"] = pd.to_datetime(train_df["date"])
    test_df["date"] = pd.to_datetime(test_df["date"])

    # rep15만 warm-up을 붙이고, full161은 현재 입력 스냅샷만 사용한다.
    warmup_df = build_rep15_warmup_frame(spec, train_df)
    if not warmup_df.empty:
        warmup_df["date"] = pd.to_datetime(warmup_df["date"])
        history_df = pd.concat([warmup_df, train_df, test_df], ignore_index=True)
    else:
        history_df = pd.concat([train_df, test_df], ignore_index=True)

    # 파생은 연속 시계열 전체에서 먼저 만들고, 마지막에 기간별로 다시 자른다.
    seasonal_map = build_seasonal_map(train_df)
    history_out = apply_canonical_transform(history_df, seasonal_map)
    train_out = history_out[
        (history_out["date"] >= pd.Timestamp("2023-01-01")) & (history_out["date"] <= pd.Timestamp("2024-12-31"))
    ].copy()
    test_out = history_out[history_out["date"] >= pd.Timestamp("2025-01-01")].copy()

    train_out = train_out.sort_values(KEY_COLS).reset_index(drop=True)
    test_out = test_out.sort_values(KEY_COLS).reset_index(drop=True)
    train_out["date"] = train_out["date"].dt.strftime("%Y-%m-%d")
    test_out["date"] = test_out["date"].dt.strftime("%Y-%m-%d")

    train_path = spec.output_dir / "ddri_prediction_canonical_train_2023_2024.csv"
    test_path = spec.output_dir / "ddri_prediction_canonical_test_2025.csv"
    meta_path = spec.output_dir / "ddri_prediction_canonical_meta.json"

    train_out.to_csv(train_path, index=False, encoding="utf-8-sig")
    test_out.to_csv(test_path, index=False, encoding="utf-8-sig")

    meta = {
        "name": spec.name,
        "train_source": str(spec.train_source),
        "test_source": str(spec.test_source),
        "train_output": str(train_path),
        "test_output": str(test_path),
        "policy": {
            "train": "2023",
            "validation": "2024",
            "test": "2025",
            "target": "bike_change",
        },
        "added_columns": [
            "seasonal_mean_2023",
            "rental_count_deseasonalized",
            "bike_change_raw",
            "bike_change_deseasonalized",
            "bike_change_lag_1",
            "bike_change_lag_24",
            "bike_change_lag_168",
            "bike_change_rollmean_24",
            "bike_change_rollstd_24",
            "bike_change_rollmean_168",
            "bike_change_rollstd_168",
            "bike_change_trend_1_24",
            "bike_change_trend_24_168",
        ],
        "train_rows_in": int(len(train_df)),
        "train_rows_out": int(len(train_out)),
        "test_rows_in": int(len(test_df)),
        "test_rows_out": int(len(test_out)),
        "train_unique_stations": int(train_df["station_id"].nunique()),
        "test_unique_stations": int(test_df["station_id"].nunique()),
        "cluster_master_source": str(spec.train_source),
        "cluster_remap_applied": True,
        "train_cluster_changed_rows": train_cluster_changed_rows,
        "test_cluster_changed_rows": test_cluster_changed_rows,
        "seasonal_group_count": int(len(seasonal_map)),
        "warmup_used": bool(not warmup_df.empty),
        "warmup_rows": int(len(warmup_df)),
        "train_bike_change_null_rows": int(train_out["bike_change_raw"].isna().sum()),
        "test_bike_change_null_rows": int(test_out["bike_change_raw"].isna().sum()),
        "train_date_min": str(train_out["date"].min()),
        "train_date_max": str(train_out["date"].max()),
        "test_date_min": str(test_out["date"].min()),
        "test_date_max": str(test_out["date"].max()),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    # 스크립트 실행 시 대표 15개와 전체 161개를 한 번에 재생성한다.
    all_meta = [build_one(spec) for spec in SPECS]
    print(json.dumps(all_meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
