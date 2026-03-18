# DDRI 실험 요약본

작성일: 2026-03-18

## 1. 현재 실험 범위

`06_prediction_training`에서는 아래 두 실험만 수행한다.

1. 무필터링 기준선 실험
2. 가중치 기반 실험

이전 샘플링, 원형 인코딩, 군집 분석 실험은 현재 범위에서 제외했다.

## 2. 공통 입력

- 데이터셋: `full161`
- 입력 정본 폴더:
  - [canonical_data_no_multicollinearity](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/canonical_data_no_multicollinearity)
- 입력 파일:
  - `ddri_prediction_canonical_train_2023_2024_no_multicollinearity.csv`
  - `ddri_prediction_canonical_test_2025_no_multicollinearity.csv`

## 3. 공통 학습 정책

- Train: `2023`
- Validation: `2024`
- Validation 기준 우세 모델 선택
- `2023+2024` 재학습
- Test: `2025`

## 4. 공통 타깃과 모델

- 기본 타깃: `bike_change_deseasonalized`
- 비교 가능 타깃: `bike_change_raw`

후보 모델:

- `LightGBM_RMSE`
- `CatBoost_RMSE`
- `StackingRegressor`
- `SoftVotingRegressor`

평가 지표:

- `RMSE`
- `MAE`
- `R²`

## 5. 실험별 차이

### A. 무필터링 기준선

- 행 삭제 없음
- 샘플 가중치 없음
- 입력 정본을 그대로 사용

대표 노트북:

- [04_ddri_prediction_train_eval_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/04_ddri_prediction_train_eval_run_all.ipynb)

### B. 가중치 기반 실험

- 행 삭제 없음
- `2023` 학습 구간에만 가중치 적용
- `2024`, `2025`는 원본 분할 유지
- 반복 패턴이 많은 일자일수록 가중치를 낮춤

현재 기본 규칙:

- `cluster_ratio = 0.7`
- `min_days_per_group = 8`
- `weight_rule = inverse_sqrt_cluster_size`

대표 노트북:

- [06_ddri_sampling_plan2_weighting_start.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/06_ddri_sampling_plan2_weighting_start.ipynb)

## 6. 참고 문서

- [01_ddri_no_filtering_experiment.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/01_ddri_no_filtering_experiment.md)
- [02_ddri_weighting_experiment.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/02_ddri_weighting_experiment.md)
- [03_ddri_prediction_training_policy.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/03_ddri_prediction_training_policy.md)
