# Ridge 회귀 기반 End-to-End 분석 보고서

## 1. 목적
- 최종 전처리된 DDRI 데이터로 해석 가능한 회귀 모델(Ridge)을 학습하고, 시간순 train/valid/test 성능을 평가한다.
- 데이터 정제, 공선성 정리, 누수 점검, 월 유사도 기반 sample weight 반영까지의 과정을 문서화한다.

## 2. 원본 및 최종 데이터
- 학습 데이터: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
- 테스트 데이터: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/data/ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`
- 타깃: `bike_change_raw`
- 최종 학습 feature 수: **16개**
- 최종 학습 feature: `station_id, hour, rental_count, weekday, month, holiday, temperature, humidity, precipitation, wind_speed, cluster, bike_change_lag_1, bike_change_rollmean_24, bike_change_rollstd_24, bike_change_rollmean_168, bike_change_rollstd_168`

## 3. 전처리 요약
- 공선성 제거 후보 PDF 기준으로 주요 중복/선형결합 컬럼을 제거했다.
- 제거 컬럼: `rental_count_deseasonalized, bike_change_trend_1_24, bike_change_trend_24_168, mapped_dong_code, seasonal_mean_2023, bike_change_lag_24, bike_change_lag_168, bike_change_deseasonalized`
- `bike_change_lag_1`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollmean_168`, `bike_change_rollstd_168`는 과거값 기반 파생변수로 확인되었고, 현재/미래값 누수는 없는 것으로 검증했다.
- 등분산성 진단에서는 키 제외 기준으로 여러 feature가 이분산 신호를 보였으며, 대표 위반 컬럼 예시는 `rental_count, temperature, humidity, precipitation, rental_count_deseasonalized, bike_change_lag_1, bike_change_rollmean_24, bike_change_rollstd_24` 이다.

## 4. 월 유사도 기반 sample_weight
- 연-월별 시간 평균선이 너무 유사한 구간은 학습 기여도를 약하게 하기 위해 월 단위 `sample_weight`를 만들었다.
- sample_weight 범위: `0.889208 ~ 0.966489`
- 가중치가 낮은 월 예시:
| year_month   |   overall_month_weight |
|:-------------|-----------------------:|
| 2023-07      |               0.889208 |
| 2023-08      |               0.894102 |
| 2023-03      |               0.90306  |
| 2024-05      |               0.903093 |
| 2024-01      |               0.905062 |

## 5. 데이터 분할
- train: 2023년
- valid: 2024년
- test: 2025년

![split counts](split_row_counts.png)

## 6. 모델링 방법
- 모델: `Ridge(alpha=2.0)`
- 전처리: 결측치는 median imputation, 수치형 feature는 standardization
- 학습 시 `sample_weight` 사용
- 평가 지표: `RMSE`, `MAE`, `R2`

## 7. 회귀 성능

| split   |     rmse |      mae |       r2 |
|:--------|---------:|---------:|---------:|
| train   | 0.726203 | 0.481299 | 0.726576 |
| valid   | 0.734183 | 0.480287 | 0.721155 |
| test    | 0.649735 | 0.433503 | 0.727374 |

![ridge scores](ridge_scores.png)

## 8. 성능 해석
- train R2=0.726576, valid R2=0.721155, test R2=0.727374로 split 간 차이가 크지 않아 과적합은 심하지 않은 편이다.
- valid/test 성능이 train과 유사하게 유지되어 시간순 분할 기준에서도 안정적인 선형 베이스라인으로 볼 수 있다.

## 9. 회귀 계수 해석
- 아래 계수는 표준화 계수 기준이며, 절댓값이 클수록 타깃에 미치는 선형 영향력이 크다.

| feature                  |   standardized_coefficient |   abs_standardized_coefficient |
|:-------------------------|---------------------------:|-------------------------------:|
| rental_count             |                  1.04008   |                      1.04008   |
| bike_change_lag_1        |                 -0.381124  |                      0.381124  |
| bike_change_rollmean_24  |                 -0.369743  |                      0.369743  |
| bike_change_rollmean_168 |                 -0.319655  |                      0.319655  |
| bike_change_rollstd_168  |                 -0.218623  |                      0.218623  |
| hour                     |                 -0.214313  |                      0.214313  |
| bike_change_rollstd_24   |                 -0.201558  |                      0.201558  |
| humidity                 |                  0.0571189 |                      0.0571189 |
| temperature              |                 -0.0392703 |                      0.0392703 |
| weekday                  |                  0.0225105 |                      0.0225105 |
| month                    |                 -0.0140298 |                      0.0140298 |
| precipitation            |                  0.0119273 |                      0.0119273 |

![top coefficients](top_standardized_coefficients.png)

## 10. 종합 결론
- 현재 전처리와 feature 구성으로 Ridge 회귀는 해석 가능성과 성능의 균형이 좋은 모델이다.
- 최고 성능 모델은 아닐 수 있지만, 설명 가능한 기준모델이자 실제 운영 후보로도 검토할 만하다.
- 이후에는 LightGBM과 Ridge를 병행 운영하거나, Ridge를 기준선 모델로 유지하는 전략이 유효하다.

## 11. 참고 산출물
- 선형회귀 계수: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/HMW_linear_regression_coefficients_20260318/outputs/linear_regression_coefficients.csv`
- 선형회귀 점수: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/HMW_linear_regression_coefficients_20260318/outputs/linear_regression_scores.csv`
- 월 가중치 제안: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/HMW_feature_monthly_similarity_weights_20260318/outputs/overall_month_weight_suggestions.csv`
- 공산성 진단: `C:/Users/tj/Documents/GitHub/ddri_work/ksm_note/HMW_heteroscedasticity_diagnosis_20260318/bike_change_target_heteroscedasticity_report_ko.md`