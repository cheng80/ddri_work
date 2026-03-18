# DDRI 실험 결과 요약본

작성일: 2026-03-18

## 1. 실행 범위

이번 결과 요약은 아래 두 실험을 같은 입력 기준에서 비교한 것이다.

- 무필터링 기준선 실험
- 가중치 기반 실험

공통 조건:

- 데이터셋: `full161`
- 입력 정본:
  - [canonical_data_no_multicollinearity](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/canonical_data_no_multicollinearity)
- 타깃: `bike_change_deseasonalized`
- 시간 정책:
  - `2023` 학습
  - `2024` 검증
  - 우세 모델 선택
  - `2023+2024` 재학습
  - `2025` 테스트

## 2. 공통 실행 조건

- 후보 모델:
  - `LightGBM_RMSE`
  - `CatBoost_RMSE`
  - `StackingRegressor`
  - `SoftVotingRegressor`
- 평가 지표:
  - `RMSE`
  - `MAE`
  - `R²`

공통 사용 행 수:

- train `2023`: `1,410,199`
- valid `2024`: `1,414,224`
- test `2025`: `1,410,360`

## 3. Validation 결과 비교


| 실험   | 우세 모델         | RMSE     | MAE      | R²       |
| ---- | ------------- | -------- | -------- | -------- |
| 무필터링 | LightGBM_RMSE | 1.004480 | 0.636488 | 0.433882 |
| 가중치  | LightGBM_RMSE | 1.006018 | 0.643709 | 0.432148 |


## 4. Test 결과 비교


| 실험   | 우세 모델         | RMSE     | MAE      | R²       |
| ---- | ------------- | -------- | -------- | -------- |
| 무필터링 | LightGBM_RMSE | 0.891602 | 0.568187 | 0.461589 |
| 가중치  | LightGBM_RMSE | 0.892781 | 0.572717 | 0.460164 |


## 5. 결과 해석

- 두 실험 모두 우세 모델은 `LightGBM_RMSE`였다.
- validation과 test 모두에서 무필터링이 가중치 실험보다 약간 더 좋았다.
- 가중치 실험은 행을 줄이지 않고 반복 패턴 영향을 완화하려는 목적이었지만, 현재 설정에서는 성능 개선으로 이어지지 않았다.

## 6. 현재 판단

1. 현재 입력 정본과 현재 가중치 규칙에서는 `무필터링`을 기준선이자 우선안으로 유지한다.
2. `가중치 기반 실험`은 유지하되, 현재 설정값(`cluster_ratio = 0.7`, `min_days_per_group = 8`, `inverse_sqrt_cluster_size`)으로는 채택하지 않는다.
3. 다음 비교 실험이 필요하다면 가중치 규칙 자체를 다시 조정한 뒤 별도 재실행한다.

## 7. 결과 파일

- 무필터링 결과:
  - [selection_metrics.csv](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/training_runs/ddri_full161_bike_change_deseasonalized_selection_metrics.csv)
  - [test_metrics.csv](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/training_runs/ddri_full161_bike_change_deseasonalized_test_metrics.csv)
  - [training_meta.json](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/training_runs/ddri_full161_bike_change_deseasonalized_training_meta.json)
- 가중치 결과:
  - [selection_metrics_plan2.csv](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/sampling_plan2_outputs/training_runs/ddri_full161_bike_change_deseasonalized_selection_metrics_plan2.csv)
  - [test_metrics_plan2.csv](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/sampling_plan2_outputs/training_runs/ddri_full161_bike_change_deseasonalized_test_metrics_plan2.csv)
  - [training_meta_plan2.json](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/sampling_plan2_outputs/training_runs/ddri_full161_bike_change_deseasonalized_training_meta_plan2.json)

