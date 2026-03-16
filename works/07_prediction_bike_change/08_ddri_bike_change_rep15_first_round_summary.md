# DDRI bike_change rep15 1차 실험 요약

## 0. 용어 설명과 기준 피처

### 주요 용어

- `bike_change`(시간별 대여량 변화량)
  - 현재 시간의 대여량이 직전 시간 대비 얼마나 늘었거나 줄었는지를 뜻하는 타깃
- `feature`(입력 변수)
  - 모델이 예측에 사용하는 입력값
- `lag`(과거 시점 값)
  - 직전 몇 시간, 며칠 전 같은 과거 값을 가져온 피처
- `rolling`(이동 통계)
  - 최근 일정 구간의 평균, 표준편차처럼 움직이는 통계값
- `baseline`(기준선 모델)
  - 추가 보강 없이 먼저 비교하는 기본 모델
- `cluster`(군집 라벨)
  - 대여소를 이용 패턴별로 묶은 보조 피처
- `sign_accuracy`(방향 일치율)
  - 예측한 변화 방향(`+/-`)이 실제 변화 방향과 일치한 비율

### 현재 기준선 피처: `full_36`

현재 1차 권장안 `LightGBM_RMSE + cluster 포함 + full_36`에 들어간 피처는 아래 35개다.


| 영문 컬럼명                            | 한글 설명             |
| --------------------------------- | ----------------- |
| `station_id`                      | 대여소 ID            |
| `cluster`                         | 군집 라벨             |
| `mapped_dong_code`                | 행정동 코드            |
| `hour`                            | 시각                |
| `weekday`                         | 요일                |
| `month`                           | 월                 |
| `holiday`                         | 공휴일 여부            |
| `temperature`                     | 기온                |
| `humidity`                        | 습도                |
| `precipitation`                   | 강수량               |
| `wind_speed`                      | 풍속                |
| `lag_1h`                          | 1시간 전 대여량         |
| `lag_24h`                         | 24시간 전 대여량        |
| `lag_168h`                        | 168시간 전 대여량       |
| `rolling_mean_24h`                | 최근 24시간 대여량 평균    |
| `rolling_std_24h`                 | 최근 24시간 대여량 표준편차  |
| `rolling_mean_168h`               | 최근 168시간 대여량 평균   |
| `rolling_std_168h`                | 최근 168시간 대여량 표준편차 |
| `rolling_mean_6h`                 | 최근 6시간 대여량 평균     |
| `is_weekend`                      | 주말 여부             |
| `is_night_hour`                   | 야간 시간대 여부         |
| `is_commute_hour`                 | 출퇴근 시간대 여부        |
| `hour_sin`                        | 시각 사인값            |
| `is_rainy`                        | 비 여부              |
| `hour_cos`                        | 시각 코사인값           |
| `commute_morning_flag`            | 아침 출근 시간대 여부      |
| `commute_evening_flag`            | 저녁 퇴근 시간대 여부      |
| `subway_distance_m`               | 가까운 지하철역까지 거리     |
| `distance_naturepark_m`           | 자연공원까지 거리         |
| `restaurant_count_300m`           | 300m 안 음식점 수      |
| `convenience_store_count_300m`    | 300m 안 편의점 수      |
| `bus_stop_count_300m`             | 300m 안 버스정류장 수    |
| `cafe_count_300m`                 | 300m 안 카페 수       |
| `elevation_diff_nearest_subway_m` | 가까운 지하철역과의 고도 차   |
| `nearest_park_area_sqm`           | 가까운 공원 면적         |


## 1. 실험 목적

- 기존 `rental_count` 대신 `bike_change(시간별 대여량 변화량)`를 신규 타깃으로 설정한다.
- 기존 `full static weather interaction` 계열에서 필터링된 `full_36` 피처를 기준선으로 삼는다.
- `rep15(대표 15개)`에서 전체 baseline, 군집 효과, 군집별 분리 실험, 누락 피처 재도입 실험을 순차적으로 확인한다.

## 2. 현재 기준선

기준선 모델:

- `LightGBM_RMSE + cluster 포함 + full_36`

전체 `rep15` 기준 성능:

| 모델 | 구간 | RMSE | MAE | R² | sign_accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| LightGBM_RMSE | train_2023 | 0.9082 | 0.5852 | 0.6287 | 0.8988 |
| LightGBM_RMSE | validation | 1.0055 | 0.6099 | 0.5414 | 0.8966 |
| LightGBM_RMSE | test | 0.8992 | 0.5482 | 0.5490 | 0.8908 |
| CatBoost_RMSE | train_2023 | 0.9600 | 0.6009 | 0.5852 | - |
| CatBoost_RMSE | validation | 1.0079 | 0.6099 | 0.5392 | - |
| CatBoost_RMSE | test | 0.9009 | 0.5489 | 0.5473 | 0.8792 |
| LinearRegression | train_2023 | 1.0214 | 0.6305 | 0.5297 | - |
| LinearRegression | validation | 1.1070 | 0.6710 | 0.4442 | - |
| LinearRegression | test | 0.9907 | 0.6066 | 0.4526 | 0.7408 |
| Ridge | train_2023 | 1.0214 | 0.6305 | 0.5297 | - |
| Ridge | validation | 1.1070 | 0.6710 | 0.4442 | - |
| Ridge | test | 0.9907 | 0.6066 | 0.4526 | 0.7408 |


비교 결과:

- `CatBoost_RMSE` test RMSE `0.9009`
- `LinearRegression` / `Ridge` test RMSE `0.9907`

해석:

- `bike_change`에서도 비선형 부스팅 계열이 유리했다.
- 현재 전체 기준선은 `LightGBM_RMSE`로 고정하는 것이 맞다.

## 3. cluster 포함 효과

비교안:

- `LightGBM_RMSE_WithCluster`
- `LightGBM_RMSE_NoCluster`

결과:

| 비교안 | 구간 | RMSE | MAE | R² | sign_accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| WithCluster | train_2023 | 0.9082 | 0.5852 | 0.6287 | 0.8988 |
| WithCluster | validation | 1.0055 | 0.6099 | 0.5414 | 0.8966 |
| WithCluster | test | 0.8992 | 0.5482 | 0.5490 | 0.8908 |
| NoCluster | train_2023 | 0.9079 | 0.5853 | 0.6290 | 0.8991 |
| NoCluster | validation | 1.0048 | 0.6098 | 0.5420 | 0.8956 |
| NoCluster | test | 0.9001 | 0.5485 | 0.5482 | 0.8895 |


해석:

- `cluster(군집 라벨)`는 아주 소폭이지만 유효한 보조 피처다.
- 따라서 현재 기준선에서는 `cluster 포함`을 유지한다.

## 4. 군집별 baseline 난이도


| 군집 | 군집명 | 구간 | RMSE | MAE | R² | 해석 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| cluster03 | 생활권 혼합형 | train_2023 | 0.6623 | 0.4663 | 0.6637 | 가장 쉬운 군집 |
| cluster03 | 생활권 혼합형 | validation | 0.7911 | 0.5488 | 0.4689 | 가장 쉬운 군집 |
| cluster03 | 생활권 혼합형 | test | 0.6522 | 0.4515 | 0.4704 | 가장 쉬운 군집 |
| cluster04 | 외곽 주거형 | train_2023 | 0.6299 | 0.4006 | 0.6983 | 비교적 안정적 |
| cluster04 | 외곽 주거형 | validation | 0.7868 | 0.4862 | 0.5136 | 비교적 안정적 |
| cluster04 | 외곽 주거형 | test | 0.8631 | 0.5979 | 0.5509 | 비교적 안정적 |
| cluster02 | 주거 도착형 | train_2023 | 0.5977 | 0.3962 | 0.7047 | 비교적 안정적 |
| cluster02 | 주거 도착형 | validation | 0.8377 | 0.5147 | 0.4882 | 비교적 안정적 |
| cluster02 | 주거 도착형 | test | 0.8634 | 0.5729 | 0.5313 | 비교적 안정적 |
| cluster00 | 업무/상업 혼합형 | train_2023 | 0.7417 | 0.5147 | 0.6869 | 중간 난이도 |
| cluster00 | 업무/상업 혼합형 | validation | 0.8900 | 0.6006 | 0.4594 | 중간 난이도 |
| cluster00 | 업무/상업 혼합형 | test | 1.0772 | 0.6106 | 0.2911 | 중간 난이도 |
| cluster01 | 아침 도착 업무 집중형 | train_2023 | 1.0833 | 0.7259 | 0.7875 | 가장 어려운 군집 |
| cluster01 | 아침 도착 업무 집중형 | validation | 1.5540 | 0.9177 | 0.5789 | 가장 어려운 군집 |
| cluster01 | 아침 도착 업무 집중형 | test | 1.5691 | 0.9525 | 0.6255 | 가장 어려운 군집 |


해석:

- `bike_change`에서도 군집별 난이도 차이는 분명하다.
- 하지만 난이도 차이가 바로 `축소 피처 조합`의 성공을 뜻하지는 않았다.

## 5. 군집별 2차 실험 결론

### cluster01 아침 도착 업무 집중형


| 비교안 | 구간 | RMSE | MAE | R² |
| --- | --- | ---: | ---: | ---: |
| full_36 | train_2023 | 1.0775 | 0.7216 | 0.7898 |
| full_36 | validation | 1.5596 | 0.9205 | 0.5759 |
| full_36 | test | 1.5716 | 0.9531 | 0.6243 |
| subset_a_commute_transit | train_2023 | 1.8872 | 1.1460 | 0.3550 |
| subset_a_commute_transit | validation | 2.0347 | 1.1914 | 0.2781 |
| subset_a_commute_transit | test | 2.1227 | 1.2667 | 0.3146 |
| subset_b_commute_transit_short_trend | train_2023 | 1.5896 | 1.0179 | 0.5424 |
| subset_b_commute_transit_short_trend | validation | 1.9208 | 1.1421 | 0.3567 |
| subset_b_commute_transit_short_trend | test | 1.9789 | 1.1927 | 0.4043 |
| subset_c_current_compact | train_2023 | 1.5349 | 0.9849 | 0.5734 |
| subset_c_current_compact | validation | 1.9117 | 1.1366 | 0.3628 |
| subset_c_current_compact | test | 1.9536 | 1.1767 | 0.4194 |


결론:

- 축소 조합이 크게 무너졌다.
- `full_36` 유지가 맞다.

### cluster02 주거 도착형


| 비교안 | 구간 | RMSE | MAE | R² |
| --- | --- | ---: | ---: | ---: |
| full_36 | train_2023 | 0.5965 | 0.3952 | 0.7058 |
| full_36 | validation | 0.8415 | 0.5157 | 0.4836 |
| full_36 | test | 0.8665 | 0.5754 | 0.5279 |
| subset_d_current_compact | train_2023 | 0.8544 | 0.5361 | 0.3965 |
| subset_d_current_compact | validation | 1.0868 | 0.6639 | 0.1387 |
| subset_d_current_compact | test | 1.1463 | 0.7309 | 0.1738 |
| subset_b_living_pattern_weather | train_2023 | 0.9382 | 0.5561 | 0.2724 |
| subset_b_living_pattern_weather | validation | 1.1307 | 0.6624 | 0.0677 |
| subset_b_living_pattern_weather | test | 1.1890 | 0.7380 | 0.1111 |
| subset_c_living_pattern_location | train_2023 | 0.9785 | 0.5807 | 0.2085 |
| subset_c_living_pattern_location | validation | 1.1287 | 0.6635 | 0.0710 |
| subset_c_living_pattern_location | test | 1.1945 | 0.7462 | 0.1029 |
| subset_a_living_pattern_core | train_2023 | 0.9834 | 0.5828 | 0.2005 |
| subset_a_living_pattern_core | validation | 1.1266 | 0.6622 | 0.0744 |
| subset_a_living_pattern_core | test | 1.1948 | 0.7463 | 0.1025 |


결론:

- 축소 조합이 전부 실패했다.
- `full_36` 유지가 맞다.

### cluster03 생활권 혼합형


| 비교안 | 구간 | RMSE | MAE | R² |
| --- | --- | ---: | ---: | ---: |
| full_36 | train_2023 | 0.6601 | 0.4648 | 0.6659 |
| full_36 | validation | 0.7977 | 0.5533 | 0.4601 |
| full_36 | test | 0.6542 | 0.4554 | 0.4671 |
| subset_d_current_compact | train_2023 | 0.6854 | 0.4800 | 0.6399 |
| subset_d_current_compact | validation | 0.8052 | 0.5595 | 0.4499 |
| subset_d_current_compact | test | 0.6717 | 0.4786 | 0.4382 |
| subset_b_mixed_lifestyle_weather | train_2023 | 0.6763 | 0.4748 | 0.6493 |
| subset_b_mixed_lifestyle_weather | validation | 0.8040 | 0.5594 | 0.4515 |
| subset_b_mixed_lifestyle_weather | test | 0.6733 | 0.4789 | 0.4356 |
| subset_c_mixed_lifestyle_location | train_2023 | 0.7123 | 0.5005 | 0.6110 |
| subset_c_mixed_lifestyle_location | validation | 0.8109 | 0.5594 | 0.4420 |
| subset_c_mixed_lifestyle_location | test | 0.6733 | 0.4764 | 0.4355 |
| subset_a_mixed_lifestyle_core | train_2023 | 0.6975 | 0.4928 | 0.6270 |
| subset_a_mixed_lifestyle_core | validation | 0.8082 | 0.5583 | 0.4458 |
| subset_a_mixed_lifestyle_core | test | 0.6745 | 0.4792 | 0.4335 |


결론:

- 가장 쉬운 군집에서도 축소 조합이 baseline을 넘지 못했다.
- `full_36` 유지가 맞다.

### cluster04 외곽 주거형


| 비교안 | 구간 | RMSE | MAE | R² |
| --- | --- | ---: | ---: | ---: |
| full_36 | train_2023 | 0.6284 | 0.3998 | 0.6997 |
| full_36 | validation | 0.7887 | 0.4877 | 0.5112 |
| full_36 | test | 0.8638 | 0.5986 | 0.5502 |
| subset_d_current_compact | train_2023 | 0.9150 | 0.5612 | 0.3634 |
| subset_d_current_compact | validation | 1.0495 | 0.6324 | 0.1345 |
| subset_d_current_compact | test | 1.1644 | 0.7757 | 0.1826 |
| subset_b_suburban_residential_weather | train_2023 | 0.9999 | 0.5914 | 0.2398 |
| subset_b_suburban_residential_weather | validation | 1.1027 | 0.6452 | 0.0445 |
| subset_b_suburban_residential_weather | test | 1.2272 | 0.7966 | 0.0921 |
| subset_a_suburban_residential_core | train_2023 | 1.0421 | 0.6157 | 0.1743 |
| subset_a_suburban_residential_core | validation | 1.1017 | 0.6446 | 0.0462 |
| subset_a_suburban_residential_core | test | 1.2312 | 0.8034 | 0.0862 |
| subset_c_living_pattern_suburban location | train_2023 | 1.0360 | 0.6109 | 0.1838 |
| subset_c_living_pattern_suburban location | validation | 1.1043 | 0.6444 | 0.0417 |
| subset_c_living_pattern_suburban location | test | 1.2328 | 0.8046 | 0.0838 |


결론:

- 축소 조합이 전부 무너졌다.
- `full_36` 유지가 맞다.

### cluster00 업무/상업 혼합형


| 비교안 | 구간 | RMSE | MAE | R² |
| --- | --- | ---: | ---: | ---: |
| baseline LightGBM_RMSE | train_2023 | 0.7384 | 0.5124 | 0.6896 |
| baseline LightGBM_RMSE | validation | 0.8935 | 0.6021 | 0.4553 |
| baseline LightGBM_RMSE | test | 1.0961 | 0.6196 | 0.2660 |
| full_36 | train_2023 | 0.7344 | 0.5101 | 0.6929 |
| full_36 | validation | 0.8966 | 0.6043 | 0.4515 |
| full_36 | test | 1.0852 | 0.6181 | 0.2806 |
| subset_c_business_location | train_2023 | 0.8029 | 0.5518 | 0.6330 |
| subset_c_business_location | validation | 0.9071 | 0.6135 | 0.4385 |
| subset_c_business_location | test | 1.1161 | 0.6249 | 0.2390 |
| subset_a_business_transit_core | train_2023 | 0.7888 | 0.5446 | 0.6458 |
| subset_a_business_transit_core | validation | 0.9066 | 0.6143 | 0.4392 |
| subset_a_business_transit_core | test | 1.1225 | 0.6223 | 0.2303 |
| subset_b_business_transit_weather | train_2023 | 0.7565 | 0.5205 | 0.6743 |
| subset_b_business_transit_weather | validation | 0.9070 | 0.6096 | 0.4386 |
| subset_b_business_transit_weather | test | 1.1373 | 0.6605 | 0.2098 |
| subset_d_current_compact | train_2023 | 0.7655 | 0.5268 | 0.6664 |
| subset_d_current_compact | validation | 0.9064 | 0.6114 | 0.4394 |
| subset_d_current_compact | test | 1.1579 | 0.6544 | 0.1810 |


결론:

- 전용 재학습은 소폭 개선됐다.
- 그러나 핵심은 `축소 조합`이 아니라 `full_36 유지`였다.

## 6. hmw 중요 피처 축 재도입 실험

비교안:

- `base_full_36`
- `base_plus_cluster_onehot`
- `base_plus_weather_interaction`
- `base_plus_bike_change_signal`
- `base_plus_context_extras`
- `all_augmented`

결과:


| 비교안 | 구간 | RMSE | MAE | R² | 해석 |
| --- | --- | ---: | ---: | ---: | --- |
| `base_full_36` | train_2023 | 0.8838 | 0.5740 | 0.6484 | 현재 최선 |
| `base_full_36` | validation | 1.0064 | 0.6097 | 0.5405 | 현재 최선 |
| `base_full_36` | test | 0.8986 | 0.5478 | 0.5496 | 현재 최선 |
| `base_plus_context_extras` | train_2023 | 0.8846 | 0.5742 | 0.6478 | 거의 동일하지만 미세하게 열세 |
| `base_plus_context_extras` | validation | 1.0076 | 0.6102 | 0.5395 | 거의 동일하지만 미세하게 열세 |
| `base_plus_context_extras` | test | 0.8987 | 0.5472 | 0.5495 | 거의 동일하지만 미세하게 열세 |
| `base_plus_cluster_onehot` | train_2023 | 0.8830 | 0.5742 | 0.6490 | one-hot 이득 없음 |
| `base_plus_cluster_onehot` | validation | 1.0048 | 0.6095 | 0.5421 | one-hot 이득 없음 |
| `base_plus_cluster_onehot` | test | 0.8991 | 0.5476 | 0.5491 | one-hot 이득 없음 |
| `base_plus_weather_interaction` | train_2023 | 0.8827 | 0.5741 | 0.6493 | 명시적 상호작용 이득 없음 |
| `base_plus_weather_interaction` | validation | 1.0055 | 0.6096 | 0.5414 | 명시적 상호작용 이득 없음 |
| `base_plus_weather_interaction` | test | 0.8993 | 0.5479 | 0.5490 | 명시적 상호작용 이득 없음 |
| `all_augmented` | train_2023 | 0.8831 | 0.5769 | 0.6528 | 과보강으로 악화 |
| `all_augmented` | validation | 1.0071 | 0.6105 | 0.5399 | 과보강으로 악화 |
| `all_augmented` | test | 0.9026 | 0.5507 | 0.5506 | 과보강으로 악화 |
| `base_plus_bike_change_signal` | train_2023 | 0.8834 | 0.5765 | 0.6525 | 가장 악화 |
| `base_plus_bike_change_signal` | validation | 1.0052 | 0.6095 | 0.5416 | 가장 악화 |
| `base_plus_bike_change_signal` | test | 0.9052 | 0.5522 | 0.5480 | 가장 악화 |


재도입한 축:

- `cluster_0 ~ cluster_4` one-hot
- `temp_x_commute`, `rain_x_commute`, `rain_x_night`
- `bike_change_lag_1`, `bike_change_lag_24`, `bike_change_lag_168`
- `bike_change_rollmean_3`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollstd_168`
- `heavy_rain_flag`, `is_lunch_hour`, `is_holiday_eve`, `is_after_holiday`

결론:

- `hmw` 쪽에서 중요해 보였던 누락 축을 다시 넣어도 이번 `rep15 bike_change` 기준선은 넘지 못했다.
- 현재 1차 실험에서는 `full_36`이 가장 안정적이다.

## 7. 현재 최종 해석

- `bike_change rep15` 1차 실험의 운영 기준선은 `LightGBM_RMSE + cluster 포함 + full_36`이다.
- 군집별 분리 실험은 난이도 차이를 보여줬지만, `축소 피처 조합`을 권장안으로 만들지는 못했다.
- 누락 피처 재도입도 baseline을 넘지 못했으므로, 지금은 `full_36`을 유지한 채 다음 단계로 넘어가는 것이 맞다.

## 8. 다음 단계

- 현재 1차 결론을 기준으로 `summary_aggregation` 경로에 집계 문서를 추가한다.
- 필요하면 `161개 확장` 전에 `bike_change`의 정의 자체를 더 엄밀하게 바꾸는지 검토한다.
- 실제 자전거 재고/API와 연결하려면, 장기적으로는 `return_count` 또는 `실시간 보유대수` 계열 입력 확보가 필요하다.

## 9. 최종 권장 수치 요약

### 전체 rep15 기준선


| 권장안 | 구간 | RMSE | MAE | R² | sign_accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `LightGBM_RMSE + cluster 포함 + full_36` | train_2023 | 0.9082 | 0.5852 | 0.6287 | 0.8988 |
| `LightGBM_RMSE + cluster 포함 + full_36` | validation | 1.0055 | 0.6099 | 0.5414 | 0.8966 |
| `LightGBM_RMSE + cluster 포함 + full_36` | test | 0.8992 | 0.5482 | 0.5490 | 0.8908 |


### 군집별 최종 권장안


| 군집 | 최종 권장안 | 구간 | RMSE | MAE | R² | sign_accuracy |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| cluster00 | `LightGBM_RMSE + full_36` | train_2023 | 0.7344 | 0.5101 | 0.6929 | 0.9076 |
| cluster00 | `LightGBM_RMSE + full_36` | validation | 0.8966 | 0.6043 | 0.4515 | 0.8837 |
| cluster00 | `LightGBM_RMSE + full_36` | test | 1.0852 | 0.6181 | 0.2806 | 0.9091 |
| cluster01 | `LightGBM_RMSE + full_36` | train_2023 | 1.0775 | 0.7216 | 0.7898 | 0.8672 |
| cluster01 | `LightGBM_RMSE + full_36` | validation | 1.5596 | 0.9205 | 0.5759 | 0.8460 |
| cluster01 | `LightGBM_RMSE + full_36` | test | 1.5716 | 0.9531 | 0.6243 | 0.8639 |
| cluster02 | `LightGBM_RMSE + full_36` | train_2023 | 0.5965 | 0.3952 | 0.7058 | 0.9276 |
| cluster02 | `LightGBM_RMSE + full_36` | validation | 0.8415 | 0.5157 | 0.4836 | 0.9021 |
| cluster02 | `LightGBM_RMSE + full_36` | test | 0.8665 | 0.5754 | 0.5279 | 0.9010 |
| cluster03 | `LightGBM_RMSE + full_36` | train_2023 | 0.6601 | 0.4648 | 0.6659 | 0.9026 |
| cluster03 | `LightGBM_RMSE + full_36` | validation | 0.7977 | 0.5533 | 0.4601 | 0.8878 |
| cluster03 | `LightGBM_RMSE + full_36` | test | 0.6542 | 0.4554 | 0.4671 | 0.9156 |
| cluster04 | `LightGBM_RMSE + full_36` | train_2023 | 0.6284 | 0.3998 | 0.6997 | 0.9065 |
| cluster04 | `LightGBM_RMSE + full_36` | validation | 0.7887 | 0.4877 | 0.5112 | 0.8901 |
| cluster04 | `LightGBM_RMSE + full_36` | test | 0.8638 | 0.5986 | 0.5502 | 0.8872 |
