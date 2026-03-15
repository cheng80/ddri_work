# 2359·3643 2단계 모델 + 튜닝 결과

## 수행 방식
- 대상: 2359, 3643 대여소만 별도 학습
- 분할: train=2023, valid=2024, test=2025
- 모델 구조: 1단계(0대/양수 분류) + 2단계(양수 건수 회귀)
- 튜닝: valid에서 `threshold_nonzero`, `scale_positive`, `bias_positive` 탐색
- 최종평가: train+valid 재학습 후 test(2025) 평가

## Test(2025) 결과 요약
| station_id | station_name | baseline exact | two_stage exact | delta exact | baseline ±1 | two_stage ±1 | delta ±1 | baseline bucket | two_stage bucket | delta bucket | baseline rmse | two_stage rmse | delta rmse |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2359 | 국립국악중,고교 정문 맞은편 | 0.5209 | 0.5747 | +0.0538 | 0.9005 | 0.8305 | -0.0700 | 0.5293 | 0.5763 | +0.0469 | 0.9348 | 1.2092 | +0.2744 |
| 3643 | 더시그넘하우스 앞 | 0.5798 | 0.6712 | +0.0914 | 0.9239 | 0.8921 | -0.0317 | 0.5824 | 0.6716 | +0.0892 | 0.8535 | 0.9632 | +0.1096 |

## 파일 목록
- `two_stage_top2_summary.csv`
- `station_2359_validation_tuning_grid.csv`, `station_3643_validation_tuning_grid.csv`
- `station_2359_best_tuned_params.csv`, `station_3643_best_tuned_params.csv`
- `station_2359_validation_comparison.csv`, `station_3643_validation_comparison.csv`
- `station_2359_test_comparison.csv`, `station_3643_test_comparison.csv`
- `station_2359_predictions_2025.csv`, `station_3643_predictions_2025.csv`
- `station_2359_confusion_bucket.csv`, `station_3643_confusion_bucket.csv`
- `station_2359_confusion_exact.csv`, `station_3643_confusion_exact.csv`
- `images/station_2359_confusion_bucket.png`, `images/station_3643_confusion_bucket.png`
- `images/station_2359_confusion_exact.png`, `images/station_3643_confusion_exact.png`