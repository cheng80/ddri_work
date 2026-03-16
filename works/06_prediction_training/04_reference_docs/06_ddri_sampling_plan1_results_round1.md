# DDRI 샘플링 1안 결과 1차 기록

작성일: 2026-03-17

## 0. 상태 메모

이 문서의 수치는 `cluster` 불일치 문제를 보정한 뒤 다시 생성한 정본과 모델링 데이터를 기준으로 재실행한 결과다.

## 1. 실행 범위

이번 1차 실행은 아래 조건으로 수행했다.

- dataset: `rep15`
- target: `bike_change_deseasonalized`
- sampling plan: `plan1_day_profile`
- retain_ratio: `0.7`
- min_days_per_group: `8`

학습 정책은 무샘플링 기준선과 동일하다.

- `2023` 학습
- `2024` 검증
- 검증 기준 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

## 2. 행 수 변화

| 구분 | 행 수 |
|---|---:|
| 원본 `2023 train` | 131,400 |
| 샘플링 1안 적용 후 `2023 train` | 93,600 |
| 감소 행 수 | 37,800 |
| 실제 유지율 | 0.712329 |

## 3. 샘플링 1안 결과

validation `2024`:

| model | RMSE | MAE | R² |
|---|---:|---:|---:|
| LightGBM_RMSE | 0.375739 | 0.144283 | 0.924521 |

test `2025`:

| model | RMSE | MAE | R² |
|---|---:|---:|---:|
| LightGBM_RMSE | 0.305396 | 0.119608 | 0.942004 |

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

샘플링 1안 `rep15 + bike_change_deseasonalized`:

- valid RMSE `0.375739`
- valid MAE `0.144283`
- valid R² `0.924521`
- test RMSE `0.305396`
- test MAE `0.119608`
- test R² `0.942004`

## 5. 1차 해석

- 샘플링 1안은 `2023 train` 행 수를 약 `28.8%` 줄였다.
- validation은 무샘플링보다 불리했다.
- test는 `RMSE`, `R²`가 약간 좋아졌지만 `MAE`는 약간 나빠졌다.
- 즉, 행 감소 효과는 있었지만 안정적으로 우세하다고 볼 정도는 아니다.

## 6. 현재 판단

현재 시점 판단은 아래와 같다.

1. 샘플링 1안은 현재 기준에서도 정상 작동한다.
2. `rep15 + bike_change_deseasonalized` 기준으로는 테스트 지표 일부 개선이 있지만, validation이 더 나빠 안정적 개선으로 보기 어렵다.
3. 따라서 다음은 아래 둘 중 하나로 가는 것이 맞다.

- `retain_ratio`를 더 보수적으로 조정해 재실험
- `full161 + bike_change_deseasonalized`에서도 같은 방식으로 비교

즉, 샘플링 1안은 계속 검토할 수는 있지만 아직 무샘플링 기준선을 대체할 근거는 부족하다.
