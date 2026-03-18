# DDRI 학습 정책 실행 설계

작성일: 2026-03-18

## 1. 목적

`full161` 데이터에 대해 아래 두 실험만 수행한다.

1. 무필터링 기준선 실험
2. 가중치 기반 실험

두 실험은 같은 입력 정본과 같은 시간 분할 정책을 공유한다.

## 2. 입력

- 입력 정본 폴더:
  - [canonical_data_no_multicollinearity](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/canonical_data_no_multicollinearity)
- 입력 파일:
  - `ddri_prediction_canonical_train_2023_2024_no_multicollinearity.csv`
  - `ddri_prediction_canonical_test_2025_no_multicollinearity.csv`

## 3. 시간 정책

- Train: `2023`
- Validation: `2024`
- Validation 기준 우세 모델 선택
- `2023+2024` 재학습
- Test: `2025`

## 4. 타깃

- 기본 타깃: `bike_change_deseasonalized`
- 필요 시 비교 타깃: `bike_change_raw`

## 5. 후보 모델

- `LightGBM_RMSE`
- `CatBoost_RMSE`
- `StackingRegressor`
- `SoftVotingRegressor`

## 6. 선택 규칙

- `2024` validation RMSE가 가장 낮은 모델 선택
- 동률이면 MAE가 낮은 모델 우선
- 모든 후보 모델에 대해 validation `RMSE`, `MAE`, `R²`를 같이 저장한다.

## 7. 실험 구분

### A. 무필터링 기준선

- 입력 정본을 그대로 사용한다.
- 행 삭제 없음
- 샘플 가중치 없음

### B. 가중치 기반 실험

- 입력 정본은 동일하게 유지한다.
- 행 삭제 없음
- `2023` 학습 구간에만 샘플 가중치를 적용한다.
- `2024`, `2025`는 원본 분할 그대로 사용한다.

## 8. 출력

- 모델 비교표
- 최종 test 성능표
- test 예측값 CSV
- 실행 메타 JSON

## 9. 대표 실행 파일

- 무필터링 노트북:
  - [04_ddri_prediction_train_eval_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/04_ddri_prediction_train_eval_run_all.ipynb)
- 가중치 노트북:
  - [06_ddri_sampling_plan2_weighting_start.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/06_ddri_sampling_plan2_weighting_start.ipynb)
