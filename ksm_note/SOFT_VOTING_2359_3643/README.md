# 2359_3643 Soft Voting Retrain Summary

## Goal
- Re-train only stations 2359 and 3643 from scratch.
- Tune soft-voting weights on 2024 validation.
- Refit base models on 2023+2024 and evaluate on 2025.

## Data
- Source: second_round_data train(2023-2024) + test(2025).
- Time split: train=2023, valid=2024, test=2025.

## Ensemble Setup
- Base models: lightgbm (fallback: hist_gbr), xgboost (fallback: extra_trees), random_forest.
- Soft-voting weights searched by grid (step=0.05, sum=1).
- Selection objective: rounded exact-match rate, then bucket accuracy, then RMSE.

## Test Results (2025)
| station_id | station_name | baseline_model | baseline_exact_rate | ensemble_exact_rate | delta_exact_rate | baseline_bucket_acc | ensemble_bucket_acc | delta_bucket_acc | baseline_rmse | ensemble_rmse | delta_rmse |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2359 | 국립국악중,고교 정문 맞은편 | lightgbm | 0.5209 | 0.5212 | +0.0003 | 0.5293 | 0.5295 | +0.0001 | 0.9348 | 0.9318 | -0.0029 |
| 3643 | 더시그넘하우스 앞 | lightgbm | 0.5798 | 0.5788 | -0.0010 | 0.5824 | 0.5812 | -0.0013 | 0.8535 | 0.8530 | -0.0005 |

## Output Files
- `station_2359_valid_model_metrics.csv`, `station_3643_valid_model_metrics.csv`
- `station_2359_soft_weight_grid.csv`, `station_3643_soft_weight_grid.csv`
- `station_2359_best_soft_weight.csv`, `station_3643_best_soft_weight.csv`
- `station_2359_test_model_metrics.csv`, `station_3643_test_model_metrics.csv`
- `station_2359_predictions_2025.csv`, `station_3643_predictions_2025.csv`
- `station_2359_confusion_bucket.csv`, `station_3643_confusion_bucket.csv`
- `station_2359_confusion_exact.csv`, `station_3643_confusion_exact.csv`
- `images/station_2359_confusion_bucket.png`, `images/station_3643_confusion_bucket.png`
- `images/station_2359_confusion_exact.png`, `images/station_3643_confusion_exact.png`