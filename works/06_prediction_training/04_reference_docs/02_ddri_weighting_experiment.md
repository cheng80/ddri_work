# DDRI 가중치 기반 실험

작성일: 2026-03-18

## 1. 실험 목적

행을 삭제하지 않고 반복 패턴의 영향만 줄여, 기준선 대비 성능 변화가 있는지 확인한다.

## 2. 입력

- 데이터셋: `full161`
- 정본 폴더:
  - [canonical_data_no_multicollinearity](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/canonical_data_no_multicollinearity)
- 입력 파일:
  - `ddri_prediction_canonical_train_2023_2024_no_multicollinearity.csv`
  - `ddri_prediction_canonical_test_2025_no_multicollinearity.csv`

## 3. 처리 원칙

- 행 삭제 없음
- `2023` 학습 구간에만 샘플 가중치 적용
- `2024`, `2025`는 원본 분할 유지
- 존재하는 lag/rolling 컬럼에 대해서만 missing flag를 생성하고 0 대체를 적용한다.

## 4. 가중치 부여 방식

- 같은 `station_id`, 같은 `weekday` 안에서 일 단위 패턴을 묶는다.
- 반복이 많은 패턴일수록 가중치를 낮춘다.
- 현재 기본 규칙:
  - `cluster_ratio = 0.7`
  - `min_days_per_group = 8`
  - `weight_rule = inverse_sqrt_cluster_size`

## 5. 시간 분할

- `2023` 학습
- `2024` 검증
- 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

## 6. 대표 실행 파일

- [06_ddri_sampling_plan2_weighting_start.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/06_ddri_sampling_plan2_weighting_start.ipynb)

## 7. 산출물

- `sampling_plan2_outputs`
- validation 비교표
- test 성능표
- test 예측값
- 가중치 분포 확인 표
