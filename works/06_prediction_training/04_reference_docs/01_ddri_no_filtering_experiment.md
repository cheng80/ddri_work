# DDRI 무필터링 기준선 실험

작성일: 2026-03-18

## 1. 실험 목적

공선성 제거 버전 정본을 그대로 사용했을 때의 기준 성능을 확보한다.

이 실험은 이후 모든 비교의 기준선이다.

## 2. 입력

- 데이터셋: `full161`
- 정본 폴더:
  - [canonical_data_no_multicollinearity](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/canonical_data_no_multicollinearity)
- 입력 파일:
  - `ddri_prediction_canonical_train_2023_2024_no_multicollinearity.csv`
  - `ddri_prediction_canonical_test_2025_no_multicollinearity.csv`

## 3. 처리 원칙

- 행 삭제 없음
- 샘플 가중치 없음
- 존재하는 lag/rolling 컬럼에 대해서만 missing flag를 생성하고 0 대체를 적용한다.

## 4. 시간 분할

- `2023` 학습
- `2024` 검증
- 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

## 5. 대표 실행 파일

- [04_ddri_prediction_train_eval_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/04_ddri_prediction_train_eval_run_all.ipynb)

## 6. 산출물

- `modeling_data`
- `training_runs`
- validation 비교표
- test 성능표
- test 예측값
