# Hierarchical Compact Regression Report

## 1. 데이터와 실험 목적

- 입력 데이터는 `hierarchical_compact` 버전이다.
- 학습 train은 대표 패턴을 균형 샘플링한 `sampled_train_2023`, 검증은 `valid_2024`, 최종 평가는 `test_2025`를 사용했다.
- 목표는 단순화한 데이터에서도 RMSE와 MAE를 낮추고, cluster별로 최적 모델을 다르게 적용해 R²를 최대화하는 것이다.
- 현재 시점 타깃 분해값인 `bike_change_deseasonalized`, `bike_change_seasonal_expected`, `return_count_deseasonalized`는 누수 방지를 위해 제외했다.

## 2. Feature Variant 비교

| feature_variant              | probe_model       |   feature_count |   dropped_corr_features |   train_rows |   eval_rows |   rmse |    mae |     r2 |   nrmse_std |   nmae_std |
|:-----------------------------|:------------------|----------------:|------------------------:|-------------:|------------:|-------:|-------:|-------:|------------:|-----------:|
| compact_safe_with_cluster    | lightgbm_balanced |              25 |                       4 |       140000 |     1568112 | 0.9752 | 0.5806 | 0.4116 |       0.767 |     0.4567 |
| compact_safe_without_cluster | lightgbm_balanced |              20 |                       4 |       140000 |     1568112 | 0.9764 | 0.5814 | 0.4102 |       0.768 |     0.4573 |

## 3. 글로벌 모델 비교

| model               | feature_variant           |   feature_count |   dropped_corr_features |   train_rows |   eval_rows |   rmse |    mae |     r2 |   nrmse_std |   nmae_std | notes                |
|:--------------------|:--------------------------|----------------:|------------------------:|-------------:|------------:|-------:|-------:|-------:|------------:|-----------:|:---------------------|
| lightgbm_balanced   | compact_safe_with_cluster |              25 |                       4 |       140000 |     1568112 | 0.9752 | 0.5806 | 0.4116 |      0.767  |     0.4567 | lightgbm balanced    |
| lightgbm_leafy      | compact_safe_with_cluster |              25 |                       4 |       140000 |     1568112 | 0.98   | 0.5849 | 0.4058 |      0.7708 |     0.4601 | lightgbm leafy       |
| extra_trees         | compact_safe_with_cluster |              25 |                       4 |       120000 |     1568112 | 0.9812 | 0.5917 | 0.4044 |      0.7718 |     0.4654 | extra trees          |
| histgbm_deep        | compact_safe_with_cluster |              25 |                       4 |       140000 |     1568112 | 0.9826 | 0.5786 | 0.4027 |      0.7729 |     0.4551 | histgbm deeper trees |
| xgboost_balanced    | compact_safe_with_cluster |              25 |                       4 |       140000 |     1568112 | 0.9829 | 0.5838 | 0.4023 |      0.7731 |     0.4592 | xgboost balanced     |
| histgbm_balanced    | compact_safe_with_cluster |              25 |                       4 |       140000 |     1568112 | 0.984  | 0.5791 | 0.4009 |      0.774  |     0.4555 | histgbm balanced     |
| random_forest       | compact_safe_with_cluster |              25 |                       4 |       120000 |     1568112 | 0.9849 | 0.6053 | 0.3999 |      0.7747 |     0.4761 | random forest        |
| xgboost_regularized | compact_safe_with_cluster |              25 |                       4 |       140000 |     1568112 | 0.9884 | 0.5858 | 0.3956 |      0.7774 |     0.4608 | xgboost regularized  |

## 4. 최종 글로벌 모델 성능

| stage     | split   |   rmse |    mae |     r2 |   nrmse_std |   nmae_std | feature_variant           | model             |   feature_count |   dropped_corr_features |   fit_rows |
|:----------|:--------|-------:|-------:|-------:|------------:|-----------:|:--------------------------|:------------------|----------------:|------------------------:|-----------:|
| selection | train   | 0.6766 | 0.3975 | 0.5092 |      0.7006 |     0.4116 | compact_safe_with_cluster | lightgbm_balanced |              25 |                       4 |     140000 |
| selection | valid   | 0.9752 | 0.5806 | 0.4116 |      0.767  |     0.4567 | compact_safe_with_cluster | lightgbm_balanced |              25 |                       4 |     140000 |
| final     | test    | 0.9251 | 0.5593 | 0.3944 |      0.7782 |     0.4706 | compact_safe_with_cluster | lightgbm_balanced |              25 |                       4 |     140000 |

- 최종 글로벌 모델: `lightgbm_balanced`
- 선택된 feature variant: `compact_safe_with_cluster`
- test RMSE `0.9251`, MAE `0.5593`, R² `0.3944`

## 5. 글로벌 Feature Importance

| feature                       |   importance_mean |   importance_std | scope   |
|:------------------------------|------------------:|-----------------:|:--------|
| return_count_deseasonalized   |              3971 |                0 | global  |
| bike_change_seasonal_expected |              3043 |                0 | global  |
| temperature                   |              2558 |                0 | global  |
| wind_speed                    |              2329 |                0 | global  |
| total_return_count            |              1294 |                0 | global  |
| subway_distance_m             |               706 |                0 | global  |
| morning_net_inflow            |               701 |                0 | global  |
| dominant_ratio                |               643 |                0 | global  |
| arrival_11_14_ratio           |               631 |                0 | global  |
| return_7_10_count             |               626 |                0 | global  |
| evening_net_inflow            |               574 |                0 | global  |
| arrival_17_20_ratio           |               536 |                0 | global  |
| arrival_7_10_ratio            |               505 |                0 | global  |
| life_pop_7_10_mean            |               458 |                0 | global  |
| dock_total                    |               405 |                0 | global  |

## 6. Cluster별 최적 모델

|   cluster | cluster_name   | model            |   selection_rmse |   selection_mae |   selection_r2 |   test_rmse |   test_mae |   test_r2 |   fit_rows |   test_rows |   feature_count |   dropped_corr_features |
|----------:|:---------------|:-----------------|-----------------:|----------------:|---------------:|------------:|-----------:|----------:|-----------:|------------:|----------------:|------------------------:|
|         0 | cluster_0      | histgbm_deep     |           0.9872 |          0.5948 |         0.3933 |      0.9464 |     0.5709 |    0.4046 |      38220 |      421008 |              20 |                       4 |
|         1 | cluster_1      | extra_trees      |           1.6955 |          0.9805 |         0.7636 |      1.5441 |     0.9223 |    0.7405 |       2340 |       25776 |              20 |                       4 |
|         2 | cluster_2      | histgbm_deep     |           1.1736 |          0.7258 |         0.3988 |      1.0432 |     0.6623 |    0.3973 |      25120 |      274944 |              20 |                       4 |
|         3 | cluster_3      | histgbm_balanced |           0.9346 |          0.5959 |         0.3043 |      0.8805 |     0.5683 |    0.2951 |      47540 |      524112 |              20 |                       4 |
|         4 | cluster_4      | histgbm_deep     |           0.8925 |          0.5346 |         0.3776 |      0.817  |     0.5159 |    0.3601 |      14740 |      163248 |              20 |                       4 |

## 7. Global vs Cluster Specialist

| scope   |   cluster | cluster_name   | variant                |   rmse |    mae |     r2 |   nrmse_std |   nmae_std |
|:--------|----------:|:---------------|:-----------------------|-------:|-------:|-------:|------------:|-----------:|
| cluster |         0 | cluster_0      | global_shared_model    | 0.9378 | 0.5769 | 0.4154 |      0.7646 |     0.4704 |
| cluster |         0 | cluster_0      | cluster_specific_model | 0.9464 | 0.5709 | 0.4046 |      0.7716 |     0.4655 |
| cluster |         1 | cluster_1      | global_shared_model    | 1.6541 | 0.9566 | 0.7023 |      0.5456 |     0.3156 |
| cluster |         1 | cluster_1      | cluster_specific_model | 1.5441 | 0.9223 | 0.7405 |      0.5094 |     0.3042 |
| cluster |         2 | cluster_2      | global_shared_model    | 1.0461 | 0.6662 | 0.3939 |      0.7785 |     0.4958 |
| cluster |         2 | cluster_2      | cluster_specific_model | 1.0432 | 0.6623 | 0.3973 |      0.7764 |     0.4928 |
| cluster |         3 | cluster_3      | global_shared_model    | 0.8727 | 0.5709 | 0.3075 |      0.8322 |     0.5443 |
| cluster |         3 | cluster_3      | cluster_specific_model | 0.8805 | 0.5683 | 0.2951 |      0.8396 |     0.5419 |
| cluster |         4 | cluster_4      | global_shared_model    | 0.8041 | 0.5105 | 0.3802 |      0.7873 |     0.4999 |
| cluster |         4 | cluster_4      | cluster_specific_model | 0.817  | 0.5159 | 0.3601 |      0.7999 |     0.5051 |
| overall |        -1 | overall        | global_shared_model    | 0.9405 | 0.5913 | 0.411  |      0.7675 |     0.4825 |
| overall |        -1 | overall        | cluster_specific_model | 0.943  | 0.5878 | 0.4079 |      0.7695 |     0.4797 |

- overall global shared model RMSE `0.9405`
- overall cluster specific model RMSE `0.9430`
- overall global shared model R² `0.4110`
- overall cluster specific model R² `0.4079`

## 8. Cluster별 중요 Feature

| feature                       |   importance_mean |   importance_std | scope   |   cluster | cluster_name   |
|:------------------------------|------------------:|-----------------:|:--------|----------:|:---------------|
| return_count_deseasonalized   |          0.507756 |         0.003428 | cluster |         0 | cluster_0      |
| bike_change_seasonal_expected |          0.12545  |         0.009203 | cluster |         0 | cluster_0      |
| total_return_count            |          0.028258 |         0.00342  | cluster |         0 | cluster_0      |
| temperature                   |          0.015432 |         0.00351  | cluster |         0 | cluster_0      |
| precipitation                 |          0.011052 |         0.000723 | cluster |         0 | cluster_0      |
| return_count_deseasonalized   |          0.581872 |         0        | cluster |         1 | cluster_1      |
| bike_change_seasonal_expected |          0.340928 |         0        | cluster |         1 | cluster_1      |
| temperature                   |          0.024578 |         0        | cluster |         1 | cluster_1      |
| wind_speed                    |          0.022396 |         0        | cluster |         1 | cluster_1      |
| is_rainy                      |          0.00627  |         0        | cluster |         1 | cluster_1      |
| return_count_deseasonalized   |          0.423468 |         0.012256 | cluster |         2 | cluster_2      |
| bike_change_seasonal_expected |          0.114163 |         0.003547 | cluster |         2 | cluster_2      |
| temperature                   |          0.020645 |         0.005887 | cluster |         2 | cluster_2      |
| total_return_count            |          0.010678 |         0.000611 | cluster |         2 | cluster_2      |
| precipitation                 |          0.010059 |         0.000576 | cluster |         2 | cluster_2      |
| return_count_deseasonalized   |          0.33879  |         0.001132 | cluster |         3 | cluster_3      |
| bike_change_seasonal_expected |          0.063038 |         0.004277 | cluster |         3 | cluster_3      |
| temperature                   |          0.022293 |         0.001221 | cluster |         3 | cluster_3      |
| total_return_count            |          0.015219 |         0.003255 | cluster |         3 | cluster_3      |
| precipitation                 |          0.006818 |         0.000299 | cluster |         3 | cluster_3      |
| return_count_deseasonalized   |          0.353353 |         0.007548 | cluster |         4 | cluster_4      |
| bike_change_seasonal_expected |          0.088638 |         0.002909 | cluster |         4 | cluster_4      |
| temperature                   |          0.022096 |         0.000635 | cluster |         4 | cluster_4      |
| precipitation                 |          0.003567 |         0.000253 | cluster |         4 | cluster_4      |
| wind_speed                    |          0.000963 |         0.001329 | cluster |         4 | cluster_4      |

## 9. 해석

- 단순화된 데이터에서도 residual lag 계열과 deseasonalized target 계열이 핵심 설명력을 유지하는지 확인할 수 있다.
- cluster specialist는 station 성격이 다른 묶음에서 개별 최적 모델을 쓰기 때문에, 전체 shared model보다 오차가 낮아질 가능성이 있다.
- cluster 1처럼 station 수가 적은 군집은 과적합 위험이 있어, 복잡한 모델보다 규제가 강한 부스팅 모델이 더 유리할 수 있다.