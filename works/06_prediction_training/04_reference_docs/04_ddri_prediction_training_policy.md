# DDRI 학습 정책 실행 설계

작성일: 2026-03-16

## 1. 목적

`modeling_data`를 사용해 아래 정책을 그대로 실행한다.

- Train: `2023`
- Validation: `2024`
- Test: `2025`
- Validation 기준 우세 모델 선택
- `2023+2024` 재학습
- `2025` 최종 평가

현재 기준선은 `무샘플링`이다.

- 학습 전 행 삭제 없음
- 유사 일/주/월 제거 없음
- 샘플 가중치 없음

실행 원칙:

- 대표 실행 경로는 노트북으로 둔다.
- 파이썬 스크립트는 재생성 및 일괄 실행 보조 도구로만 사용한다.

## 2. 입력

- `modeling_data/ddri_prediction_modeling_train_2023.csv`
- `modeling_data/ddri_prediction_modeling_valid_2024.csv`
- `modeling_data/ddri_prediction_modeling_test_2025.csv`

## 3. 타깃

- 기본 타깃: `bike_change_raw`
- 대안 타깃: `bike_change_deseasonalized`

## 4. 후보 모델

- `LightGBM_RMSE`
- `CatBoost_RMSE`
- `StackingRegressor`
- `SoftVotingRegressor`

## 5. 선택 규칙

- `2024` validation RMSE가 가장 낮은 모델 선택
- 동률이면 MAE가 낮은 모델 우선
- 모든 후보 모델에 대해 validation `RMSE`, `MAE`, `R²`를 항상 계산하고 저장한다.

## 6. 최종 학습

- 선택된 모델을 `2023+2024` 전체로 재학습
- `2025`에서 `RMSE`, `MAE`, `R²`를 항상 계산하고 저장한다.

## 7. 출력

- 모델 비교표
- 최종 test 성능표
- test 예측값 CSV
- 실행 메타 JSON

## 8. 대표 실행 파일

- 대표 노트북:
  - [04_ddri_prediction_train_eval_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/04_ddri_prediction_train_eval_run_all.ipynb)
- 재생성 스크립트:
  - [04_ddri_prediction_train_eval.py](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts/04_ddri_prediction_train_eval.py)
