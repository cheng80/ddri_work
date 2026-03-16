# Bike Change Optimization Report

## 1. Goal

- Only `bike_change` is used as the target.
- Objective: lower RMSE and MAE while pushing R2 as high as possible on the 2025 holdout test.

## 2. New Feature Candidates

- `station_hour_mean`, `station_weekday_hour_mean`, `station_month_hour_mean`
- `station_hour_std`, `station_weekday_hour_std`, `station_abs_mean`
- `cluster_hour_mean`, `cluster_weekday_hour_mean`
- `station_hour_gap`, `cluster_hour_gap`, `station_cluster_interaction`

## 3. Feature Search

| feature_variant         | probe_model       |   train_rows |   eval_rows |   rmse |    mae |     r2 |   nrmse_std |   nmae_std |
|:------------------------|:------------------|-------------:|------------:|-------:|-------:|-------:|------------:|-----------:|
| enhanced_cluster        | lightgbm_balanced |       600000 |     1598688 | 1.1102 | 0.6333 | 0.2291 |      0.878  |     0.5009 |
| enhanced_cluster_priors | lightgbm_balanced |       600000 |     1598688 | 1.1554 | 0.6775 | 0.165  |      0.9138 |     0.5358 |

## 4. Validation Model Search

| model                | feature_variant   |   train_rows |   eval_rows |   rmse |    mae |     r2 |   nrmse_std |   nmae_std | notes                         |
|:---------------------|:------------------|-------------:|------------:|-------:|-------:|-------:|------------:|-----------:|:------------------------------|
| lightgbm_leafy       | enhanced_cluster  |       600000 |     1598688 | 1.1097 | 0.6325 | 0.2299 |      0.8776 |     0.5002 | lightgbm deeper leaves tuning |
| lightgbm_balanced    | enhanced_cluster  |       600000 |     1598688 | 1.1102 | 0.6333 | 0.2291 |      0.878  |     0.5009 | lightgbm balanced tuning      |
| lightgbm_regularized | enhanced_cluster  |       600000 |     1598688 | 1.1115 | 0.6344 | 0.2273 |      0.879  |     0.5017 | lightgbm regularized tuning   |
| xgboost_deep         | enhanced_cluster  |       600000 |     1598688 | 1.1136 | 0.6357 | 0.2244 |      0.8807 |     0.5027 | xgboost deeper tree tuning    |
| xgboost_balanced     | enhanced_cluster  |       600000 |     1598688 | 1.118  | 0.6387 | 0.2182 |      0.8842 |     0.5051 | xgboost balanced tuning       |
| hist_gbm_focus       | enhanced_cluster  |       600000 |     1598688 | 1.1185 | 0.6351 | 0.2175 |      0.8846 |     0.5023 | histgbm tuned for bike_change |
| xgboost_regularized  | enhanced_cluster  |       600000 |     1598688 | 1.1188 | 0.6373 | 0.2171 |      0.8848 |     0.504  | xgboost regularized tuning    |

## 5. Final Global Result

| stage     | split   |   rmse |    mae |     r2 |   nrmse_std |   nmae_std |
|:----------|:--------|-------:|-------:|-------:|------------:|-----------:|
| selection | train   | 1.0636 | 0.6012 | 0.2504 |      0.8658 |     0.4893 |
| selection | valid   | 1.1097 | 0.6325 | 0.2299 |      0.8776 |     0.5002 |
| final     | test    | 1.0408 | 0.5819 | 0.2259 |      0.8798 |     0.4919 |

- Final test RMSE: `1.0408`
- Final test MAE: `0.5819`
- Final test R2: `0.2259`

## 6. Top Features In Final Model

| feature                  |   importance |
|:-------------------------|-------------:|
| bike_change_rollstd_168  |         2258 |
| bike_change_rollstd_24   |         2250 |
| bike_change_rollmean_168 |         2183 |
| bike_change_rollmean_24  |         2137 |
| bike_change_lag_168      |         1967 |
| bike_change_lag_1        |         1707 |
| rental_count_lag_1       |         1691 |
| lat                      |         1625 |
| bike_change_rollmean_3   |         1622 |
| temp_x_commute           |         1593 |
| bike_change_lag_24       |         1590 |
| wind_speed               |         1581 |
| hour                     |         1565 |
| return_count_lag_1       |         1560 |
| temperature              |         1553 |
| humidity                 |         1525 |
| lon                      |         1512 |
| hour_sin                 |         1343 |
| return_count_lag_24      |         1266 |
| station_id               |         1259 |

## 7. Cluster Specialists

|   cluster | cluster_name          | model                | feature_variant   |   selection_rmse |   selection_mae |   selection_r2 |   test_rmse |   test_mae |   test_r2 |   train_rows |   eval_rows |
|----------:|:----------------------|:---------------------|:------------------|-----------------:|----------------:|---------------:|------------:|-----------:|----------:|-------------:|------------:|
|         0 | 업무/상업 혼합형      | lightgbm_balanced    | enhanced_cluster  |           1.1304 |          0.6738 |         0.1964 |      1.0707 |     0.6231 |    0.2307 |       600000 |      429240 |
|         1 | 아침 도착 업무 집중형 | xgboost_regularized  | enhanced_cluster  |           1.9393 |          1.1332 |         0.6865 |      1.7316 |     0.9907 |    0.6709 |        52128 |       26280 |
|         2 | 주거 도착형           | lightgbm_balanced    | enhanced_cluster  |           1.3047 |          0.7909 |         0.2483 |      1.166  |     0.6943 |    0.2398 |       556032 |      280320 |
|         3 | 생활·상권 혼합형      | lightgbm_regularized | enhanced_cluster  |           1.0676 |          0.6446 |         0.0839 |      0.9992 |     0.5936 |    0.0839 |       600000 |      534360 |
|         4 | 외곽 주거형           | hist_gbm_focus       | enhanced_cluster  |           1.0071 |          0.5936 |         0.1984 |      0.933  |     0.5447 |    0.1573 |       330144 |      166440 |

## 8. Global vs Cluster-Specific

| scope   |   cluster | cluster_name   | variant                |   rmse |    mae |     r2 |   nrmse_std |   nmae_std |
|:--------|----------:|:---------------|:-----------------------|-------:|-------:|-------:|------------:|-----------:|
| overall |        -1 | overall        | global_shared_model    | 1.0739 | 0.6237 | 0.2249 |      0.8804 |     0.5114 |
| overall |        -1 | overall        | cluster_specific_model | 1.0653 | 0.6237 | 0.2372 |      0.8734 |     0.5113 |
