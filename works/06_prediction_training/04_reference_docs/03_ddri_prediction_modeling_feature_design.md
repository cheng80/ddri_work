# DDRI 모델링용 피처셋 설계

작성일: 2026-03-16

## 1. 목적

`canonical_data`를 바로 학습 가능한 `modeling_data`로 변환한다.

현재 기준은 `무샘플링 baseline cycle`이다.

- 행 삭제 없음
- 샘플 가중치 없음
- 정본 전체를 그대로 사용

## 2. 입력

- `canonical_data/ddri_prediction_canonical_train_2023_2024.csv`
- `canonical_data/ddri_prediction_canonical_test_2025.csv`

## 3. 대상 타깃

- 기본 타깃: `bike_change_raw`
- 보조 타깃: `bike_change_deseasonalized`

## 4. 결측 처리 원칙

- 정본 `NaN`는 유지하지 않고, 모델링용 피처셋에서만 처리한다.
- 구조적 결측 컬럼에는 `missing_flag`를 추가한다.
- 원값 컬럼은 `0`으로 대체한다.

대상 컬럼:

- `bike_change_lag_1`
- `bike_change_lag_24`
- `bike_change_lag_168`
- `bike_change_rollmean_24`
- `bike_change_rollstd_24`
- `bike_change_rollmean_168`
- `bike_change_rollstd_168`
- `bike_change_trend_1_24`
- `bike_change_trend_24_168`

예:

- `bike_change_lag_24`는 유지
- `bike_change_lag_24_missing` 추가
- 결측은 `0` 대체

## 5. 분할

- train: `2023`
- valid: `2024`
- test: `2025`

## 6. 출력

각 데이터셋(`rep15`, `full161`)별로 아래를 저장한다.

- `train_2023.csv`
- `valid_2024.csv`
- `test_2025.csv`
- `meta.json`
