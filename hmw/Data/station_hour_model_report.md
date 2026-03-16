# Station-Hour Regression Report

## 1. Split Protocol

- Train: 2023 only
- Validation: 2024 only
- Test: 2025 only
- Feature selection and model selection are done on validation only.
- Final test score is measured after retraining the selected model on 2023+2024.

## 2. Selected Models

- bike_change: `lightgbm_leafy` with `enhanced`
- bike_count_index: `gbm` with `basic`
- Easier target by final test nRMSE: `bike_count_index`

## 3. Train / Valid / Test Summary

| target           | best_model     | feature_set   |   train_rmse |   valid_rmse |   test_rmse |   train_mae |   valid_mae |   test_mae |   train_r2 |   valid_r2 |   test_r2 |   valid_minus_train_rmse |   test_minus_valid_rmse |
|:-----------------|:---------------|:--------------|-------------:|-------------:|------------:|------------:|------------:|-----------:|-----------:|-----------:|----------:|-------------------------:|------------------------:|
| bike_change      | lightgbm_leafy | enhanced      |       1.067  |       1.1138 |      1.0434 |      0.6025 |      0.6343 |     0.5828 |     0.2457 |     0.224  |    0.222  |                   0.0469 |                 -0.0705 |
| bike_count_index | gbm            | basic         |       1.9643 |     431.766  |    335.476  |      1.2801 |     59.663  |    43.3365 |     1      |     0.9525 |    0.9886 |                 429.801  |                -96.2898 |

## 4. Interpretation

### bike_change

- Train RMSE (fit on 2023, eval on 2023): `1.0670`
- Valid RMSE (fit on 2023, eval on 2024): `1.1138`
- Test RMSE (fit on 2023+2024, eval on 2025): `1.0434`
- Train MAE / Valid MAE / Test MAE: `0.6025` / `0.6343` / `0.5828`
- Train R2 / Valid R2 / Test R2: `0.2457` / `0.2240` / `0.2220`

### bike_count_index

- Train RMSE (fit on 2023, eval on 2023): `1.9643`
- Valid RMSE (fit on 2023, eval on 2024): `431.7657`
- Test RMSE (fit on 2023+2024, eval on 2025): `335.4759`
- Train MAE / Valid MAE / Test MAE: `1.2801` / `59.6630` / `43.3365`
- Train R2 / Valid R2 / Test R2: `1.0000` / `0.9525` / `0.9886`

## 5. Top Feature Importances

### bike_change

- `bike_change_lag_168`: 0.042550
- `bike_change_lag_24`: 0.035767
- `hour_sin`: 0.030556
- `hour`: 0.011480
- `bike_change_rollmean_24`: 0.009682
- `is_weekend_or_holiday`: 0.008187
- `lon`: 0.007249
- `rental_count_lag_1`: 0.006579
- `bike_change_rollstd_168`: 0.006524
- `hour_cos`: 0.005076

### bike_count_index

- `bike_count_index_lag_1`: 2953.147582
- `bike_index_rollmean_3`: 745.211956
- `bike_count_index_lag_2`: 454.132548
- `bike_index_rollmean_24`: 171.975848
- `bike_count_index_lag_24`: 84.392778
- `bike_index_rollmean_168`: 71.537842
- `bike_count_index_lag_168`: 53.583952
- `bike_change_rollmean_24`: 0.036808
- `dayofyear`: 0.031153
- `bike_change_lag_24`: 0.002735
