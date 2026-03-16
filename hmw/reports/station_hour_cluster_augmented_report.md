# Station-Hour Bike Availability Analysis

## 1. Split Protocol

- Train: `2023`
- Validation: `2024`
- Test: `2025`
- Feature selection and model selection used only the 2024 validation split. The 2025 test split was held out until the final retraining step on 2023+2024.

## 2. Train / Valid / Test Summary

| target           | best_model     | feature_set   |   train_rmse |   valid_rmse |   test_rmse |   train_mae |   valid_mae |   test_mae |   train_r2 |   valid_r2 |   test_r2 |   valid_minus_train_rmse |   test_minus_valid_rmse |
|:-----------------|:---------------|:--------------|-------------:|-------------:|------------:|------------:|------------:|-----------:|-----------:|-----------:|----------:|-------------------------:|------------------------:|
| bike_change      | lightgbm_leafy | enhanced      |       1.067  |       1.1138 |      1.0434 |      0.6025 |      0.6343 |     0.5828 |     0.2457 |     0.224  |    0.222  |                   0.0469 |                 -0.0705 |
| bike_count_index | gbm            | basic         |       1.9643 |     431.766  |    335.476  |      1.2801 |     59.663  |    43.3365 |     1      |     0.9525 |    0.9886 |                 429.801  |                -96.2898 |

## 3. Validation Benchmark For Model Selection

### bike_change top 5

|   rank | model                |   rmse |    mae |     r2 | notes                         |
|-------:|:---------------------|-------:|-------:|-------:|:------------------------------|
|      1 | lightgbm_leafy       | 1.1138 | 0.6343 | 0.224  | lightgbm deeper leaves tuning |
|      2 | lightgbm_balanced    | 1.1149 | 0.6348 | 0.2226 | lightgbm balanced tuning      |
|      3 | lightgbm_regularized | 1.1157 | 0.6348 | 0.2214 | lightgbm regularized tuning   |
|      4 | xgboost_deep         | 1.1181 | 0.6368 | 0.2182 | xgboost deeper tree tuning    |
|      5 | xgboost_balanced     | 1.1225 | 0.6395 | 0.212  | xgboost balanced tuning       |

### bike_count_index top 5

|   rank | model    |    rmse |     mae |     r2 | notes                       |
|-------:|:---------|--------:|--------:|-------:|:----------------------------|
|      1 | gbm      | 431.766 |  59.663 | 0.9525 | classic gradient boosting   |
|      2 | lightgbm | 622.966 | 135.332 | 0.9012 | lightgbm gradient boosting  |
|      3 | hist_gbm | 650.687 | 152.833 | 0.8922 | histogram gradient boosting |
|      4 | xgboost  | 658.894 | 157.818 | 0.8895 | xgboost histogram booster   |

## 4. Final Metrics By Stage

| target           | best_model     | feature_set   | evaluation_stage   | fit_period            | data_split   |     rmse |     mae |     r2 |
|:-----------------|:---------------|:--------------|:-------------------|:----------------------|:-------------|---------:|--------:|-------:|
| bike_change      | lightgbm_leafy | enhanced      | selection          | train_2023            | train        |   1.067  |  0.6025 | 0.2457 |
| bike_change      | lightgbm_leafy | enhanced      | selection          | train_2023            | valid        |   1.1138 |  0.6343 | 0.224  |
| bike_change      | lightgbm_leafy | enhanced      | final              | train_valid_2023_2024 | test         |   1.0434 |  0.5828 | 0.222  |
| bike_count_index | gbm            | basic         | selection          | train_2023            | train        |   1.9643 |  1.2801 | 1      |
| bike_count_index | gbm            | basic         | selection          | train_2023            | valid        | 431.766  | 59.663  | 0.9525 |
| bike_count_index | gbm            | basic         | final              | train_valid_2023_2024 | test         | 335.476  | 43.3365 | 0.9886 |

## 5. Cluster Feature Effect

- bike_change without cluster: RMSE `1.0543`, MAE `0.5870`
- bike_change with cluster: RMSE `1.0508`, MAE `0.5860`
- RMSE change: `-0.0035`
- MAE change: `-0.0010`

## 6. Cluster-Specific Best Models

| cluster_name          | model                |   selection_rmse |   test_rmse |   test_mae |   test_r2 |   train_rows |   eval_rows |
|:----------------------|:---------------------|-----------------:|------------:|-----------:|----------:|-------------:|------------:|
| 업무/상업 혼합형      | lightgbm_regularized |           1.1345 |      1.0777 |     0.6305 |    0.2205 |       220000 |      429240 |
| 아침 도착 업무 집중형 | xgboost_regularized  |           1.9455 |      1.7291 |     0.9903 |    0.6718 |        52128 |       26280 |
| 주거 도착형           | lightgbm_regularized |           1.3034 |      1.1707 |     0.6967 |    0.2336 |       220000 |      280320 |
| 생활·상권 혼합형      | lightgbm_balanced    |           1.0754 |      1.0049 |     0.5978 |    0.0734 |       220000 |      534360 |
| 외곽 주거형           | hist_gbm_focus       |           1.0071 |      0.9351 |     0.5446 |    0.1536 |       180000 |      166440 |

## 7. Representative Stations

| cluster_name          |   station_id | station_name                 |   rental_total_2025 |   mean_abs_error | selection_reason                     |
|:----------------------|-------------:|:-----------------------------|--------------------:|-----------------:|:-------------------------------------|
| 업무/상업 혼합형      |         2335 | 3호선 매봉역 3번출구앞       |               16974 |         1.34065  | usage 16974, center 0.765, mae 1.341 |
| 업무/상업 혼합형      |         2340 | 삼호물산버스정류장(23370) 옆 |               12637 |         1.24256  | usage 12637, center 0.765, mae 1.243 |
| 업무/상업 혼합형      |         2414 | 도곡역 아카데미스위트 앞     |               11818 |         1.14046  | usage 11818, center 0.765, mae 1.140 |
| 아침 도착 업무 집중형 |         2377 | 수서역 5번출구               |               15966 |         1.42834  | usage 15966, center 2.648, mae 1.428 |
| 아침 도착 업무 집중형 |         2348 | 포스코사거리(기업은행)       |               12923 |         1.31819  | usage 12923, center 3.345, mae 1.318 |
| 아침 도착 업무 집중형 |         2323 | 주식회사 오뚜기 정문 앞      |                1234 |         0.21356  | usage 1234, center 3.269, mae 0.214  |
| 주거 도착형           |         2404 | 대모산입구역 4번 출구 앞     |               13681 |         1.23208  | usage 13681, center 1.062, mae 1.232 |
| 주거 도착형           |         2384 | 자곡사거리                   |               12508 |         1.19218  | usage 12508, center 1.062, mae 1.192 |
| 주거 도착형           |         2306 | 압구정역 2번 출구 옆         |               12541 |         1.09614  | usage 12541, center 1.062, mae 1.096 |
| 생활·상권 혼합형      |         2332 | 선릉역3번출구                |               12215 |         1.11435  | usage 12215, center 0.796, mae 1.114 |
| 생활·상권 혼합형      |         2431 | 대치역 7번출구               |               11597 |         1.13156  | usage 11597, center 0.807, mae 1.132 |
| 생활·상권 혼합형      |         3614 | 은마아파트 입구 사거리       |               10332 |         1.01011  | usage 10332, center 0.796, mae 1.010 |
| 외곽 주거형           |         3643 | 더시그넘하우스 앞            |                4762 |         0.647292 | usage 4762, center 0.731, mae 0.647  |
| 외곽 주거형           |         2387 | 래미안강남힐즈 사거리        |                8066 |         0.895762 | usage 8066, center 1.356, mae 0.896  |
| 외곽 주거형           |         3642 | LH강남힐스테이트아파트       |                7276 |         0.809124 | usage 7276, center 1.356, mae 0.809  |

## 8. Notes

- Cluster changed stations: `35` / `161`
- Test metrics are final holdout results, not model-selection results.
- Validation benchmark charts in the PDF correspond to the model-selection stage.
