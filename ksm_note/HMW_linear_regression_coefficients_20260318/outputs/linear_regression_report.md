# 선형 회귀 계수 보고서

## 1. 분석 설정
- 데이터: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`, `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/data/ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`
- 분할: 2023년=train, 2024년=valid, 2025년=test
- 행 수: train=1,410,199, valid=1,414,224, test=1,410,360
- 타깃: `bike_change_raw`
- 학습 가중치: `sample_weight`
- 모델: Ridge(alpha=2.0), median imputation + standardization

## 2. 성능

| split   |     rmse |      mae |       r2 |
|:--------|---------:|---------:|---------:|
| train   | 0.726203 | 0.481299 | 0.726576 |
| valid   | 0.734183 | 0.480287 | 0.721155 |
| test    | 0.649735 | 0.433503 | 0.727374 |

## 3. 절편

- intercept: `-0.000188`

## 4. 양(+)의 영향이 큰 feature

| feature       |   standardized_coefficient |   abs_standardized_coefficient |
|:--------------|---------------------------:|-------------------------------:|
| rental_count  |                 1.04008    |                     1.04008    |
| humidity      |                 0.0571189  |                     0.0571189  |
| weekday       |                 0.0225105  |                     0.0225105  |
| precipitation |                 0.0119273  |                     0.0119273  |
| holiday       |                 0.00500907 |                     0.00500907 |
| cluster       |                 0.00452221 |                     0.00452221 |
| wind_speed    |                 0.00262277 |                     0.00262277 |
| station_id    |                 0.00198222 |                     0.00198222 |
| month         |                -0.0140298  |                     0.0140298  |
| temperature   |                -0.0392703  |                     0.0392703  |

## 5. 음(-)의 영향이 큰 feature

| feature                  |   standardized_coefficient |   abs_standardized_coefficient |
|:-------------------------|---------------------------:|-------------------------------:|
| bike_change_lag_1        |                -0.381124   |                     0.381124   |
| bike_change_rollmean_24  |                -0.369743   |                     0.369743   |
| bike_change_rollmean_168 |                -0.319655   |                     0.319655   |
| bike_change_rollstd_168  |                -0.218623   |                     0.218623   |
| hour                     |                -0.214313   |                     0.214313   |
| bike_change_rollstd_24   |                -0.201558   |                     0.201558   |
| temperature              |                -0.0392703  |                     0.0392703  |
| month                    |                -0.0140298  |                     0.0140298  |
| station_id               |                 0.00198222 |                     0.00198222 |
| wind_speed               |                 0.00262277 |                     0.00262277 |

## 6. 해석 주의사항
- 표준화 계수이므로 절댓값이 클수록 타깃에 미치는 선형 영향력이 크다고 볼 수 있습니다.
- 이는 인과효과가 아니라, 현재 데이터와 분할 기준에서 관측된 선형 관계입니다.
- 계수 부호는 다른 feature를 함께 통제한 상태에서의 방향입니다.