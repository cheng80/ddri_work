# LightGBM 고성능 의심 포인트 점검 보고서

## 1. 점검 목적
- `R2 > 0.9` 수준의 성능이 누수나 잘못된 분할에서 나온 것은 아닌지 확인한다.
- 아래 4가지를 점검한다: 타깃과 거의 같은 feature, 미래 정보 혼입, train/test 분할 오류, 연도 간 과도한 패턴 반복.

## 2. 타깃과 거의 같은 정보를 feature로 넣은 경우
- 현재 최종 데이터에서는 `|corr(feature, target)| >= 0.9` 인 feature는 없다.
- 해당 개수: **0개**
- 다만 아래 5개는 타깃의 과거 이력 기반 파생 feature이므로, 누수는 아니더라도 성능을 크게 끌어올릴 수 있는 강한 시계열 feature다.

| feature                  |   correlation_with_target | derived_from_target_history   |
|:-------------------------|--------------------------:|:------------------------------|
| bike_change_rollmean_24  |               -0.421295   | True                          |
| bike_change_rollmean_168 |               -0.417925   | True                          |
| bike_change_lag_1        |               -0.403469   | True                          |
| bike_change_rollstd_24   |               -0.0281863  | True                          |
| bike_change_rollstd_168  |               -0.00463729 | True                          |

![target corr](target_like_feature_correlation.png)

## 3. 미래 정보가 feature에 섞인 경우
- `bike_change_lag_1`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollmean_168`, `bike_change_rollstd_168`를 전체 시계열 기준으로 재계산했다.
- 결과: 현재값/미래값이 아니라 과거값만 사용하는 공식과 완전히 일치했다.

| feature                  |   mismatch_count_vs_past_only_formula | past_only_verified   |
|:-------------------------|--------------------------------------:|:---------------------|
| bike_change_lag_1        |                                     0 | True                 |
| bike_change_rollmean_24  |                                     0 | True                 |
| bike_change_rollstd_24   |                                     0 | True                 |
| bike_change_rollmean_168 |                                     0 | True                 |
| bike_change_rollstd_168  |                                     0 | True                 |

## 4. train/test 분리가 잘못된 경우
- 분할은 시간순으로 되어 있으며, 날짜 구간이 겹치지 않는다.

| split   | min_date   | max_date   |    rows |
|:--------|:-----------|:-----------|--------:|
| train   | 2023-01-01 | 2023-12-31 | 1410360 |
| valid   | 2024-01-01 | 2024-12-31 | 1414224 |
| test    | 2025-01-01 | 2025-12-31 | 1410360 |

- `station_id + date + hour` 기준 split 간 중복 key도 없다.

| left_split   | right_split   |   overlap_key_rows |
|:-------------|:--------------|-------------------:|
| train        | valid         |                  0 |
| train        | test          |                  0 |
| valid        | test          |                  0 |

## 5. 같은 패턴이 train/test에 너무 비슷하게 반복되는 경우
- feature별로 같은 달(예: 1월 vs 1월)의 24시간 평균선을 연도 간 비교했다.
- 기준: `corr >= 0.95` 그리고 `NRMSE <= 0.35` 이면 높은 유사성으로 판단했다.

|   left_year |   right_year |   high_similarity_count |
|------------:|-------------:|------------------------:|
|        2023 |         2024 |                      56 |
|        2023 |         2025 |                      55 |
|        2024 |         2025 |                      58 |

- 즉, 누수는 아니지만 계절성과 반복성이 강한 일부 feature는 연도 간 패턴이 매우 비슷하다.
- 이런 반복성은 특히 트리 모델에서 높은 점수로 이어질 수 있다.

| feature   |   month |   left_year |   right_year |   corr |   nrmse | high_similarity_flag   |
|:----------|--------:|------------:|-------------:|-------:|--------:|:-----------------------|
| holiday   |       2 |        2023 |         2025 |      1 |       0 | True                   |
| holiday   |       4 |        2023 |         2025 |      1 |       0 | True                   |
| holiday   |       6 |        2023 |         2024 |      1 |       0 | True                   |
| holiday   |       6 |        2023 |         2025 |      1 |       0 | True                   |
| holiday   |       6 |        2024 |         2025 |      1 |       0 | True                   |
| holiday   |       7 |        2023 |         2024 |      1 |       0 | True                   |
| holiday   |       7 |        2023 |         2025 |      1 |       0 | True                   |
| holiday   |       7 |        2024 |         2025 |      1 |       0 | True                   |
| holiday   |      11 |        2023 |         2024 |      1 |       0 | True                   |
| holiday   |      11 |        2023 |         2025 |      1 |       0 | True                   |
| holiday   |      11 |        2024 |         2025 |      1 |       0 | True                   |
| month     |       1 |        2023 |         2024 |      1 |       0 | True                   |
| month     |       1 |        2023 |         2025 |      1 |       0 | True                   |
| month     |       1 |        2024 |         2025 |      1 |       0 | True                   |
| month     |       2 |        2023 |         2024 |      1 |       0 | True                   |
| month     |       2 |        2023 |         2025 |      1 |       0 | True                   |
| month     |       2 |        2024 |         2025 |      1 |       0 | True                   |
| month     |       3 |        2023 |         2024 |      1 |       0 | True                   |
| month     |       3 |        2023 |         2025 |      1 |       0 | True                   |
| month     |       3 |        2024 |         2025 |      1 |       0 | True                   |

![repeat counts](repeated_pattern_similarity_counts.png)

## 6. 종합 결론
- **타깃과 거의 동일한 feature 직접 포함**: 확인되지 않음
- **미래 정보 혼입**: 현재 확인 범위에서 발견되지 않음
- **시간 분할 오류**: 발견되지 않음
- **연도 간 반복 패턴**: 일부 feature에서 강하게 존재함
- 따라서 LightGBM의 높은 성능은 현재 기준으로는 `명백한 누수`보다는 `강한 과거 이력 feature + 반복적인 시계열 패턴`의 영향일 가능성이 높다.