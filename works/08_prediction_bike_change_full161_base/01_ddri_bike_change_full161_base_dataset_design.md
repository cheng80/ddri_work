# DDRI bike_change full161 기본피처 데이터셋 설계

작성일: 2026-03-16  
목적: `161개` 정본 데이터를 사용해, 추가 피처 없이 `bike_change` 타깃 정제 데이터를 다시 생성하는 기준을 고정한다.

## 1. 입력 정본

- 경로:
  - `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/`
- 파일:
  - `ddri_prediction_long_train_2023_2024.csv`
  - `ddri_prediction_long_test_2025.csv`

## 2. 사용 컬럼

정본 CSV에 이미 존재하는 기본 컬럼만 사용한다.

- `station_id`
- `date`
- `hour`
- `rental_count`
- `cluster`
- `mapped_dong_code`
- `weekday`
- `month`
- `holiday`
- `temperature`
- `humidity`
- `precipitation`
- `wind_speed`

## 3. 타깃 생성

### 3.1 `bike_change_raw`

- 정의:
  - 같은 `station_id` 내 시간순 `rental_count.diff()`

### 3.2 `bike_change_deseasonalized`

- 정의:
  - `bike_change_raw - seasonal_mean_train_2023`
- `seasonal_mean_train_2023` 계산 기준:
  - `Train 2023`
  - `station_id + weekday + hour`

중요:

- `seasonal_mean`은 `2024`, `2025`를 사용하지 않는다
- 그래야 타깃 변환 단계에서 미래 정보 누수를 막을 수 있다

## 4. 정제 규칙

- `station_id + date + hour` 중복이 있으면 중단
- 타깃 생성 후 `bike_change_raw`가 `NaN`인 첫 시점 행만 제거
- 추가 파생 피처(`lag`, `rolling`, `return_count`, `bike_count_index`)는 붙이지 않는다

## 5. 출력 파일

- `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/data/ddri_prediction_bike_change_full161_base_train_2023_2024.csv`
- `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/data/ddri_prediction_bike_change_full161_base_test_2025.csv`
- `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/data/ddri_prediction_bike_change_full161_base_feature_summary.csv`
- `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/reports/ddri_prediction_bike_change_full161_base_feature_meta.json`
