# DDRI Bike-Change Prediction

이 폴더는 신규 타깃 `bike_change(시간별 자전거 변화량)` 예측 실험의 정본 작업 경로다.

## 0. 용어 정리

- `bike_change`(시간별 자전거 변화량)
  - 현재 시간의 자전거 수가 직전 시간 대비 얼마나 늘었거나 줄었는지를 나타내는 타깃
- `feature`(입력 변수)
  - 모델이 예측에 사용하는 입력값
- `lag`(과거 시점 값)
  - 직전 몇 시간, 며칠 전 같은 과거 값을 가져온 피처
- `rolling`(이동 통계)
  - 최근 일정 구간의 평균, 표준편차처럼 움직이는 통계값
- `baseline`(기준선 모델)
  - 추가 보강 없이 먼저 비교하는 기본 모델
- `cluster`(군집 라벨)
  - 대여소를 이용 패턴별로 묶은 보조 피처

## 1. 이번 실험의 고정 기준

- 기존 `rental_count` 실험 구조를 최대한 유지한다
- 신규 타깃은 `bike_change`로 바꾼다
- 입력 피처는 `top20_optional` 기준 `38개`를 출발점으로 삼되, rep15 입력에 없는 `morning_net_inflow`, `evening_net_inflow`를 제외한 `36개 사용 가능 피처`를 우선 사용한다
- 첫 라운드는 `rep15(대표 15개)`부터 시작한다
- 첫 모델은 `LightGBM regression` 기준으로 비교한다

## 2. 먼저 볼 문서

1. [01_ddri_bike_change_target_definition.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/01_ddri_bike_change_target_definition.md)
2. [02_ddri_bike_change_experiment_design.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/02_ddri_bike_change_experiment_design.md)
3. [03_ddri_bike_change_rep15_dataset_builder.ipynb](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/03_ddri_bike_change_rep15_dataset_builder.ipynb)
4. [08_ddri_bike_change_rep15_first_round_summary.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/08_ddri_bike_change_rep15_first_round_summary.md)

## 3. 입력 기준

- 원본 입력은 대표 15개 공유폴더와 기존 `prediction_long` 입력 구조를 그대로 참조한다
- 필터링된 38개 피처 정의는 아래 문서를 기준으로 삼는다
  - [16_ddri_full_static_weather_interaction_feature_filtering_summary.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full/16_ddri_full_static_weather_interaction_feature_filtering_summary.md)

## 4. 폴더 역할

### 루트

- `01`: bike_change 타깃 정의
- `02`: 실험 설계
- `03`: rep15 데이터셋 빌더
- 이후:
  - rep15 baseline 비교
  - 군집 포함 baseline
  - 군집별 실험

### `output/`

- `data/`: 실험 결과 CSV
- `images/`: 비교 차트와 시각화 산출물

### `cheng80/`

- 군집별 세부 실험과 후속 요약 정리 경로

## 5. 현재 1차 결론

- `rep15` 기준 baseline(기준선 모델) 최선은 `LightGBM_RMSE + cluster 포함`
- 현재 test 기준선은 `RMSE 0.8992`, `MAE 0.5482`, `R² 0.5490`, `sign_accuracy 0.8908`
- `cluster`를 제거하면 test RMSE가 `0.9001`로 약간 나빠진다
- 군집별 2차 실험에서는 `cluster00~04` 모두 `축소 피처 조합`보다 `full_36` 유지가 더 안정적이었다
- `hmw` 보고서 기준으로 빠져 있던 `weather interaction`, `cluster one-hot`, `bike_change 전용 lag/rolling`, `holiday 주변 변수`를 다시 넣어도 `full_36`을 넘지 못했다

## 5-1. 현재 상태

- `rep15 bike_change 1차 실험`은 마감 상태다
- 현재 권장안은 `LightGBM_RMSE + cluster 포함 + full_36`로 고정한다
- 세부 수치와 군집별 권장 수치는 [08_ddri_bike_change_rep15_first_round_summary.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/08_ddri_bike_change_rep15_first_round_summary.md) 기준으로 본다
- 다음 확장 작업은 별도 단계로 분리한다
  - `summary_aggregation` 집계
  - `161개 확장`
  - `return_count` 또는 재고 계열 입력 추가 실험

## 6. 현재 읽기 순서

1. 타깃 정의: [01_ddri_bike_change_target_definition.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/01_ddri_bike_change_target_definition.md)
2. 실험 설계: [02_ddri_bike_change_experiment_design.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/02_ddri_bike_change_experiment_design.md)
3. 데이터셋 생성: [03_ddri_bike_change_rep15_dataset_builder.ipynb](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/03_ddri_bike_change_rep15_dataset_builder.ipynb)
4. baseline 비교: [04_ddri_bike_change_rep15_model_comparison.ipynb](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/04_ddri_bike_change_rep15_model_comparison.ipynb)
5. cluster 효과 비교: [05_ddri_bike_change_rep15_cluster_effect_comparison.ipynb](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/05_ddri_bike_change_rep15_cluster_effect_comparison.ipynb)
6. 군집 baseline 비교: [06_ddri_bike_change_cluster_baseline_comparison.ipynb](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/06_ddri_bike_change_cluster_baseline_comparison.ipynb)
7. 확장 피처 재실험: [07_ddri_bike_change_rep15_augmented_feature_recheck.py](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/07_ddri_bike_change_rep15_augmented_feature_recheck.py)
8. 1차 요약: [08_ddri_bike_change_rep15_first_round_summary.md](/Users/cheng80/Desktop/ddri_work/works/07_prediction_bike_change/08_ddri_bike_change_rep15_first_round_summary.md)
