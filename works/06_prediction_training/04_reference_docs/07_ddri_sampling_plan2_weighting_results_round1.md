# DDRI 가중치 2안 결과 1차 기록

작성일: 2026-03-17

## 0. 상태 메모

이 문서의 수치는 `cluster` 불일치 문제를 보정한 뒤 다시 생성한 정본과 모델링 데이터를 기준으로 재실행한 결과다.

## 1. 실행 범위

이번 1차 실행은 아래 조건으로 수행했다.

- dataset: `rep15`
- target: `bike_change_deseasonalized`
- sampling plan: `plan2_weighting`
- cluster_ratio: `0.7`
- min_days_per_group: `8`
- weight_rule: `inverse_sqrt_cluster_size`

학습 정책은 무샘플링 기준선과 동일하다.

- `2023` 학습
- `2024` 검증
- 검증 기준 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

## 2. 가중치 특성

가중치 방식은 행을 삭제하지 않는다.

| 구분 | 값 |
|---|---:|
| 원본 `2023 train` 행 수 | 131,400 |
| 가중치 적용 후 `2023 train` 행 수 | 131,400 |
| weight min | 0.301225 |
| weight mean | 1.000000 |
| weight max | 1.241983 |

즉, 행 수는 유지하고 반복 패턴이 많은 날짜의 영향만 줄였다.

## 3. 가중치 2안 결과

validation `2024`:

| model | RMSE | MAE | R² |
|---|---:|---:|---:|
| LightGBM_RMSE | 0.374683 | 0.143450 | 0.924945 |

test `2025`:

| model | RMSE | MAE | R² |
|---|---:|---:|---:|
| LightGBM_RMSE | 0.304924 | 0.119275 | 0.942184 |

## 4. 무샘플링 기준선과 비교

비교 기준:

- [05_ddri_no_sampling_baseline_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/05_ddri_no_sampling_baseline_results_round1.md)

무샘플링 `rep15 + bike_change_deseasonalized`:

- valid RMSE `0.372257`
- valid MAE `0.140486`
- valid R² `0.925913`
- test RMSE `0.306413`
- test MAE `0.118805`
- test R² `0.941617`

가중치 2안 `rep15 + bike_change_deseasonalized`:

- valid RMSE `0.374683`
- valid MAE `0.143450`
- valid R² `0.924945`
- test RMSE `0.304924`
- test MAE `0.119275`
- test R² `0.942184`

## 5. 1차 해석

- 가중치 2안은 행을 줄이지 않고도 반복 패턴의 영향만 조정할 수 있었다.
- validation 성능은 무샘플링보다 약간 불리했다.
- test에서는 `RMSE`와 `R²`가 약간 좋아졌고, `MAE`는 약간 나빠졌다.
- 즉, 샘플링 1안보다는 보수적이고 결과도 조금 더 낫지만, 현재 설정만으로는 뚜렷한 개선이라고 보기 어렵다.

## 6. 현재 판단

현재 시점 판단은 아래와 같다.

1. 가중치 2안은 샘플링 1안보다 더 타당하다.
2. 그러나 `rep15 + bike_change_deseasonalized` 기준으로는 개선 폭이 작다.
3. 따라서 다음은 아래 둘 중 하나로 가는 것이 맞다.

- `full161 + bike_change_deseasonalized`에서도 같은 방식으로 비교
- 가중치 공식을 바꿔 재실험

즉, 가중치 방식은 계속 가져갈 가치가 있지만 아직 무샘플링 기준선을 대체할 정도의 이득은 확인되지 않았다.
