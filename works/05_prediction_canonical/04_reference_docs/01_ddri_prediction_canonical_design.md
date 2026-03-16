# DDRI 예측 정본 재구축 설계

작성일: 2026-03-16

## 1. 목적

기존 예측 실험 경로를 승계하지 않고, 원천 입력 CSV를 기준으로 `bike_change` 중심 정본을 다시 생성한다.

## 2. 입력 원천

### 2.1 대표 15개

- `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_train_2023_2024.csv`
- `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_test_2025.csv`
- warm-up 계산용:
  - `3조 공유폴더/2022년 12월 강남구 따릉이 이용정보/서울특별시 공공자전거 대여이력 정보_2212.csv`

### 2.2 전체 161개

- `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_train_2023_2024.csv`
- `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_test_2025.csv`

## 3. 정본 원칙

- 타깃 기본값은 `bike_change`
- 원본 행은 유지한다
- `rep15`는 `2022-12`를 계산용 히스토리로만 앞에 붙여 `2023` 시작부 결측을 줄인다
- `2022-12` warm-up 행은 최종 출력에서 제거한다
- `seasonal_mean_2023`는 `2023` 구간만으로 계산
- 계절성 제거 컬럼은 아래 식으로 만든다

`bike_change_deseasonalized = bike_change_raw - seasonal_mean_2023`

## 4. seasonal mean 기준

- 키: `station_id + weekday + hour`
- 계산 구간: `2023-01-01 ~ 2023-12-31`의 `bike_change_raw`
- 적용 구간: `2023`, `2024`, `2025` 전체

## 5. 출력 컬럼

- 원본 CSV 전체 컬럼 유지
- 추가 컬럼:
  - `seasonal_mean_2023`
  - `rental_count_deseasonalized`
  - `bike_change_raw`
  - `bike_change_deseasonalized`
  - `bike_change_lag_1`
  - `bike_change_lag_24`
  - `bike_change_lag_168`
  - `bike_change_rollmean_24`
  - `bike_change_rollstd_24`
  - `bike_change_rollmean_168`
  - `bike_change_rollstd_168`
  - `bike_change_trend_1_24`
  - `bike_change_trend_24_168`

제외 컬럼:

- `hour_sin`
- `hour_cos`
- `is_commute_hour`
- `is_weekend`
- `is_rainy`
- `heavy_rain_flag`

lag/rolling은 모두 같은 `station_id` 내 과거값만 사용한다.  
rolling 계산은 현재 시점 누수를 막기 위해 `shift(1)` 후 계산한다.

## 6. 검증 규칙

- `station_id + date + hour` 중복 0건
- 원본 대비 행 수 동일
- `rep15`는 warm-up 적용 후 `bike_change_raw` 결측이 0건에 가까워져야 한다
- `full161`은 warm-up 미적용 상태이므로 스테이션 첫 시점 결측이 남을 수 있다
- `seasonal_mean_2023` 결측은 `bike_change_raw` 결측 행에서만 허용
- `rental_count_deseasonalized` 결측 0건
- `bike_change_deseasonalized` 결측은 `bike_change_raw` 결측 행에서만 허용

## 7. 결측 처리 원칙

정본 CSV에서는 구조적 결측을 임의로 채우지 않는다.

이유:

- `bike_change_raw`의 시작 결측은 데이터 오류가 아니라 직전 시점 부재 때문이다.
- `lag`, `rolling`, `trend` 결측은 과거 구간이 부족해서 계산 불가한 구조적 결측이다.
- 따라서 정본 단계에서 0 또는 평균으로 덮어쓰면 시계열 의미가 왜곡된다.

모델링 단계 원칙:

1. 정본에서는 `NaN` 유지
2. 학습용 피처셋 생성 시 `missing_flag` 추가
3. 값 대체는 모델 특성에 따라 제한적으로 수행

권장 `missing_flag` 대상:

- `bike_change_lag_1`
- `bike_change_lag_24`
- `bike_change_lag_168`
- `bike_change_rollmean_24`
- `bike_change_rollstd_24`
- `bike_change_rollmean_168`
- `bike_change_rollstd_168`
- `bike_change_trend_1_24`
- `bike_change_trend_24_168`

권장 학습 처리:

- LightGBM 계열:
  - `NaN` 유지 또는 `0 대체 + missing_flag`
- 선형 모델 계열:
  - `0 대체 + missing_flag`

보조 선택지:

- `lag_168`, `roll_168` 중심 모델에서는 `2023` 초반 warm-up 부족 구간을 학습 제외할 수 있다.

## 8. 출력 경로

### 대표 15개

- `3조 공유폴더/대표대여소_예측데이터_15개/canonical_data/ddri_prediction_canonical_train_2023_2024.csv`
- `3조 공유폴더/대표대여소_예측데이터_15개/canonical_data/ddri_prediction_canonical_test_2025.csv`
- `3조 공유폴더/대표대여소_예측데이터_15개/canonical_data/ddri_prediction_canonical_meta.json`

### 전체 161개

- `3조 공유폴더/군집별 데이터_전체 스테이션/canonical_data/ddri_prediction_canonical_train_2023_2024.csv`
- `3조 공유폴더/군집별 데이터_전체 스테이션/canonical_data/ddri_prediction_canonical_test_2025.csv`
- `3조 공유폴더/군집별 데이터_전체 스테이션/canonical_data/ddri_prediction_canonical_meta.json`
