# DDRI Bike-Change 실험 설계

## 1. 실험 배경

기존 `rental_count` 실험에서는 `161개 전체 운영 기준선`으로 `static enriched + weather_full interaction`이 가장 안정적이었다.

이후 같은 구조에서 중요도가 낮은 피처를 줄인 결과, `38개 top20_optional` 축소안이 test 기준으로 더 간결하면서도 소폭 우세했다.

이번 실험은 그 `38개 피처`를 출발점으로 삼아, rep15 입력에 실제로 존재하거나 파생 생성 가능한 `36개 피처`를 신규 타깃 `bike_change` 예측에 적용하는 것이 목표다.

참고 문서:
- [16_ddri_full_static_weather_interaction_feature_filtering_summary.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full/16_ddri_full_static_weather_interaction_feature_filtering_summary.md)
- [01_hmw_analysis_summary.md](/Users/cheng80/Desktop/ddri_work/cheng80/Team03_ml_analysis/01_hmw_analysis_summary.md)

## 2. 이번 라운드 고정 조건

- 타깃: `bike_change`
- 범위: `rep15(대표 15개)`
- 모델: `LightGBM regression`
- 피처: `top20_optional` 기준 38개 중 rep15 사용 가능 36개
- 군집 실험: 기존 `cluster00~04` 흐름 재사용

## 3. 단계별 실험 순서

### 3.1 데이터셋 생성

- 기존 `prediction_long` 구조를 따라 `rep15` 입력 데이터셋을 다시 만든다
- 차이점은 타깃이 `rental_count`가 아니라 `bike_change`

산출물 예정:
- `ddri_prediction_bike_change_train_2023_2024.csv`
- `ddri_prediction_bike_change_test_2025.csv`

### 3.2 rep15 전체 baseline

- 군집 분기 없이 `rep15` 전체에 하나의 모델을 먼저 적용한다
- 첫 기준선:
  - `LightGBM regression`
  - `38개 top20_optional`

평가 지표:
- `RMSE`
- `MAE`
- `R²`
- 필요 시 `부호 일치율`

### 3.3 cluster 포함 baseline

- 같은 전체 모델에 `cluster(군집 라벨)`을 보조 피처로 포함했을 때 효과를 확인한다

### 3.4 군집별 실험

- `cluster00~04` 각각에 대해 개별 모델을 돌린다
- 1차에서는 모두 같은 `38개 피처`를 사용한다
- 첫 목적은 “군집별 특화가 bike_change에서도 유리한가”를 확인하는 것이다

## 4. 이번 라운드에서 하지 않는 것

- one-hot encoding 비교
- Poisson objective 비교
- 161개 전체 확장
- 38개보다 더 작은 추가 피처 축소

이 항목들은 첫 baseline과 군집별 결과를 확인한 뒤 다음 단계로 미룬다.

## 5. 기대하는 관찰 포인트

- `bike_change`에서 군집 라벨이 기존보다 더 유효한가
- 업무형 / 주거형 군집에서 방향성 패턴이 더 잘 드러나는가
- 기존 `rental_count`보다 `bike_change`가 재배치 의사결정에 더 직접적인가

## 6. 현재 권장 실행 순서

1. `03_ddri_bike_change_rep15_dataset_builder.ipynb`
2. rep15 전체 baseline 비교 노트북
3. cluster 포함 baseline 비교
4. 군집별 실험 노트북 분기
