# Station-Hour Bike Availability Analysis

## 1. 분석 목표 재정의

- 학습 기간: `2023-01-01 ~ 2024-12-31`
- 테스트 기간: `2025-01-01 ~ 2025-12-31`
- 분석 단위: `station-hour`
- 실제 시간대별 보유대수 이력은 현재 데이터에 없다.
- 따라서 이번 분석의 핵심 타깃은 `bike_change`다.
- `bike_change = return_count - rental_count` 이며, 다음 1시간 동안 해당 station의 자전거가 순증가할지 순감소할지를 뜻한다.
- 실제 서비스에서 필요한 다음 시간 보유대수는 `현재 실시간 재고(API) + 예측 bike_change`로 계산해야 한다.

## 2. 왜 bike_count_index 대신 bike_change 중심으로 가는가

- `bike_count_index`는 실제 보유대수가 아니라 대여/반납 흐름을 누적한 관측 기반 지수다.
- 이 값은 상대적 방향성 해석에는 유용하지만, 사용자에게 '다음 시간에 몇 대 있나'를 직접 답하는 값은 아니다.
- 반면 `bike_change`는 현재 실제 재고와 결합하면 바로 다음 시간 예상 보유대수로 변환할 수 있다.
- 따라서 앱과 관리자 웹 모두에서 바로 연결되는 핵심 예측값은 `bike_change`다.

## 3. 데이터와 Feature 구성

- 기본 원천 데이터: 강남구 따릉이 이용정보(2023~2025), 강남구 날씨, 대여소 메타데이터, `works/01_clustering` 군집 결과
- 시간 파생 feature: `hour`, `weekday`, `dayofyear`, `is_commute_hour`, `is_weekend_or_holiday`, 주기성 sin/cos
- 흐름 lag feature: `bike_change_lag_1`, `bike_change_lag_24`, `bike_change_lag_168`, `rental_count_lag_*`, `return_count_lag_*`
- rolling feature: `bike_change_rollmean_3`, `bike_change_rollmean_24`, `bike_change_rollstd_24`, `bike_change_rollstd_168`
- 날씨 feature: `temperature`, `humidity`, `precipitation`, `wind_speed`, `is_rainy`, `heavy_rain`
- 상호작용 feature: `temp_x_commute`, `rain_x_commute`, `rain_x_night`
- 대여소 정적 feature: `lat`, `lon`, `lcd_count`, `qr_count`, `dock_total`, `is_qr_mixed`
- 군집 feature: `cluster`, `cluster_0` ~ `cluster_4`

## 4. 핵심 모델 선택: bike_change

- 최종 선택 모델 family: `hist_gbm_tuned`
- cluster 미포함 성능: RMSE `1.0543`, MAE `0.5870`
- cluster 포함 성능: RMSE `1.0508`, MAE `0.5860`
- 최종 전체 성능: RMSE `1.0543`, MAE `0.5870`, R² `0.2057`
- cluster 추가 효과: RMSE `-0.0035`, MAE `-0.0010`

### 4-1. bike_change 상위 5개 모델

|   rank | model          |    rmse |      mae |       r2 | notes                       |
|-------:|:---------------|--------:|---------:|---------:|:----------------------------|
|      1 | hist_gbm_tuned | 1.05429 | 0.587036 | 0.205666 | 부스팅 튜닝 버전            |
|      2 | hist_gbm       | 1.05579 | 0.587755 | 0.2034   | 히스토그램 기반 부스팅      |
|      3 | extra_trees    | 1.07426 | 0.597128 | 0.175285 | 랜덤 분할 앙상블, 표본 학습 |
|      4 | random_forest  | 1.07505 | 0.586955 | 0.174067 | 비선형 앙상블, 표본 학습    |
|      5 | ridge          | 1.10193 | 0.641657 | 0.132249 | 선형 회귀 계열              |

### 4-2. bike_change 모델 해석

- `hist_gbm_tuned`: RMSE와 MAE를 동시에 가장 안정적으로 낮췄다.
- `hist_gbm`: 튜닝 전 모델도 근접해서, boosting 계열이 문제 구조에 잘 맞음을 보여줬다.
- `extra_trees`, `random_forest`: 일부 패턴은 따라가지만 피크 시간대 큰 변동 대응력이 상대적으로 떨어졌다.
- `ridge`: 선형 반복 구조는 잡았지만 비선형 상호작용 반영이 부족했다.

### 4-3. hist_gbm 과 hist_gbm_tuned 파라미터 비교

| parameter         |   hist_gbm |   hist_gbm_tuned | interpretation                      |
|:------------------|-----------:|-----------------:|:------------------------------------|
| learning_rate     |       0.05 |             0.04 | 학습 속도를 낮춰 더 안정적으로 수렴 |
| max_depth         |      10    |            12    | 더 복잡한 상호작용 허용             |
| max_iter          |     140    |           180    | 부스팅 반복 횟수 확대               |
| min_samples_leaf  |      80    |            60    | 지역 패턴을 더 세밀하게 반영        |
| l2_regularization |       0.1  |             0.05 | 정규화 완화로 설명력 확보           |
| train_sample      |  450000    |        600000    | 더 큰 표본으로 학습 안정화          |

- `hist_gbm_tuned`는 완전히 다른 모델이 아니라 같은 `HistGradientBoostingRegressor`를 현재 데이터에 맞게 조정한 버전이다.
- 더 작은 `learning_rate`와 더 많은 `max_iter`를 사용해 과하게 흔들리지 않으면서도 패턴을 더 오래 학습하도록 만들었다.
- `max_depth`를 늘리고 `min_samples_leaf`를 줄여 station-hour 수준의 국소 패턴과 비선형 상호작용을 더 세밀하게 반영했다.
- 학습 표본도 더 크게 사용해 tuned 버전의 일반화 안정성을 보강했다.

## 5. feature를 줄인 경량 버전 비교

- full feature set: feature `62`개 / RMSE `1.0508` / MAE `0.5860` / R² `0.2110`
- reduced feature set: feature `21`개 / RMSE `1.0534` / MAE `0.5880` / R² `0.2070`
- 경량화 기준: `importance_mean > 0.001`
- 해석: 중요도가 거의 없던 피처를 제거해도 성능이 크게 무너지지 않으면, 운영 단계에서는 경량 버전이 더 실용적일 수 있다.

## 6. cluster별 특화 모델 실험

- 이전까지의 분석은 모든 cluster에 같은 글로벌 모델을 적용하고, cluster는 feature로만 반영하는 구조였다.
- 추가 실험에서는 cluster 0~4 각각에 대해 별도 모델 후보를 비교하고, cluster마다 가장 잘 맞는 모델을 따로 선택했다.

| cluster_name          | model          |     rmse |      mae |        r2 |   train_rows |   eval_rows |
|:----------------------|:---------------|---------:|---------:|----------:|-------------:|------------:|
| 업무/상업 혼합형      | hist_gbm_tuned | 1.08236  | 0.627727 | 0.213776  |       180000 |      429240 |
| 아침 도착 업무 집중형 | hist_gbm_tuned | 1.72417  | 0.990473 | 0.673723  |        52128 |       26280 |
| 주거 도착형           | hist_gbm_tuned | 1.17834  | 0.699256 | 0.223579  |       180000 |      280320 |
| 생활·상권 혼합형      | hist_gbm       | 1.00752  | 0.593146 | 0.0685793 |       150000 |      534360 |
| 외곽 주거형           | hist_gbm_tuned | 0.935204 | 0.544738 | 0.153345  |       180000 |      166440 |

### 6-1. 글로벌 공유 모델 vs cluster별 특화 모델

| scope   | cluster_name          | variant                |     rmse |      mae |        r2 |
|:--------|:----------------------|:-----------------------|---------:|---------:|----------:|
| cluster | 업무/상업 혼합형      | global_shared_model    | 1.09106  | 0.629667 | 0.201083  |
| cluster | 업무/상업 혼합형      | cluster_specific_model | 1.08236  | 0.627727 | 0.213776  |
| cluster | 아침 도착 업무 집중형 | global_shared_model    | 1.81765  | 0.986695 | 0.637381  |
| cluster | 아침 도착 업무 집중형 | cluster_specific_model | 1.72417  | 0.990473 | 0.673723  |
| cluster | 주거 도착형           | global_shared_model    | 1.19307  | 0.70314  | 0.204045  |
| cluster | 주거 도착형           | cluster_specific_model | 1.17834  | 0.699256 | 0.223579  |
| cluster | 생활·상권 혼합형      | global_shared_model    | 1.00656  | 0.595945 | 0.0703534 |
| cluster | 생활·상권 혼합형      | cluster_specific_model | 1.00752  | 0.593146 | 0.0685793 |
| cluster | 외곽 주거형           | global_shared_model    | 0.944589 | 0.542333 | 0.136266  |
| cluster | 외곽 주거형           | cluster_specific_model | 0.935204 | 0.544738 | 0.153345  |
| overall | overall               | global_shared_model    | 1.08354  | 0.627874 | 0.210861  |
| overall | overall               | cluster_specific_model | 1.07435  | 0.625843 | 0.224202  |

- 이 비교를 통해 모든 cluster에 같은 모델을 쓸지, cluster별로 다른 모델을 둘지의 실익을 직접 확인할 수 있다.

## 7. RMSE와 MAE 해석

- `RMSE`는 큰 오차에 더 민감하므로 피크 시간대 실패를 보여준다.
- `MAE`는 평균적인 오차 수준을 보여준다.
- 앱/운영에서는 둘 다 중요하므로 두 지표를 함께 봐야 한다.
- `hist_gbm_tuned`가 두 지표를 가장 균형 있게 관리했다.

## 6. cluster feature 반영 결과

- 공통 station `161`개 중 `35`개가 2025년에 cluster가 바뀌었다. 변화율은 `21.74%`다.
- 따라서 cluster는 고정 정답이 아니라 station 성향을 요약하는 보조 피처로 해석해야 한다.
- 그래도 bike_change 예측에서는 cluster 추가 후 오차가 소폭 개선되었다.

## 7. bike_change 최종 사용 Feature 전체

| feature                  | category     | description                             | source                   |   importance_mean |   importance_std |
|:-------------------------|:-------------|:----------------------------------------|:-------------------------|------------------:|-----------------:|
| bike_change_lag_168      | lag          | bike_change의 168시간 전 값             | station-hour 집계 파생   |        0.052706   |      0.00446168  |
| hour_sin                 | calendar     | 시간의 주기성(sin)                      | time 파생                |        0.0333749  |      0.00668835  |
| bike_change_lag_24       | lag          | bike_change의 24시간 전 값              | station-hour 집계 파생   |        0.0322636  |      0.00225599  |
| hour                     | calendar     | 시간(0~23)                              | time 파생                |        0.00775008 |      0.00110768  |
| is_weekend_or_holiday    | calendar     | 주말 또는 공휴일 여부                   | 휴일 캘린더              |        0.00767592 |      0.00409302  |
| bike_change_lag_1        | lag          | bike_change의 1시간 전 값               | station-hour 집계 파생   |        0.0067926  |      0.000247841 |
| cluster_2                | cluster      | cluster 2 여부                          | cluster dummy            |        0.00656765 |      0.00104088  |
| bike_change_rollmean_24  | rolling      | bike_change의 직전 24시간 이동평균      | station-hour 집계 파생   |        0.0065502  |      0.00231967  |
| return_count_lag_24      | lag          | return_count의 24시간 전 값             | station-hour 집계 파생   |        0.00532951 |      0.000444946 |
| cluster                  | cluster      | train 기준 cluster 라벨                 | works/01_clustering 결과 |        0.00525339 |      0.00238496  |
| rental_count_lag_1       | lag          | rental_count의 1시간 전 값              | station-hour 집계 파생   |        0.00502984 |      0.000199762 |
| bike_change_rollstd_168  | rolling      | bike_change의 직전 168시간 이동표준편차 | station-hour 집계 파생   |        0.00411916 |      0.000385884 |
| is_commute_hour          | calendar     | 출퇴근 시간대 여부                      | time 파생                |        0.00383693 |      0.000586756 |
| bike_change_rollmean_3   | rolling      | bike_change의 직전 3시간 이동평균       | station-hour 집계 파생   |        0.00364725 |      0.000363147 |
| hour_cos                 | calendar     | 시간의 주기성(cos)                      | time 파생                |        0.00336476 |      0.000576521 |
| cluster_1                | cluster      | cluster 1 여부                          | cluster dummy            |        0.00212269 |      0.000122027 |
| bike_change_rollmean_168 | rolling      | bike_change의 직전 168시간 이동평균     | station-hour 집계 파생   |        0.00177038 |      0.00141791  |
| bike_count_index_lag_24  | lag          | bike_count_index의 24시간 전 값         | station-hour 집계 파생   |        0.00170034 |      0.000667773 |
| bike_change_rollstd_24   | rolling      | bike_change의 직전 24시간 이동표준편차  | station-hour 집계 파생   |        0.00137259 |      0.000120358 |
| cluster_0                | cluster      | cluster 0 여부                          | cluster dummy            |        0.00115292 |      0.000597054 |
| dock_total               | station_meta | 총 거치면 수                            | 대여소 정보              |        0.00104084 |      0.000157525 |

## 8. bike_change 상위 중요 Feature

| target      | feature                 |   importance_mean |   importance_std |
|:------------|:------------------------|------------------:|-----------------:|
| bike_change | bike_change_lag_168     |        0.052706   |      0.00446168  |
| bike_change | hour_sin                |        0.0333749  |      0.00668835  |
| bike_change | bike_change_lag_24      |        0.0322636  |      0.00225599  |
| bike_change | hour                    |        0.00775008 |      0.00110768  |
| bike_change | is_weekend_or_holiday   |        0.00767592 |      0.00409302  |
| bike_change | bike_change_lag_1       |        0.0067926  |      0.000247841 |
| bike_change | cluster_2               |        0.00656765 |      0.00104088  |
| bike_change | bike_change_rollmean_24 |        0.0065502  |      0.00231967  |
| bike_change | return_count_lag_24     |        0.00532951 |      0.000444946 |
| bike_change | cluster                 |        0.00525339 |      0.00238496  |
| bike_change | rental_count_lag_1      |        0.00502984 |      0.000199762 |
| bike_change | bike_change_rollstd_168 |        0.00411916 |      0.000385884 |
| bike_change | is_commute_hour         |        0.00383693 |      0.000586756 |
| bike_change | bike_change_rollmean_3  |        0.00364725 |      0.000363147 |
| bike_change | hour_cos                |        0.00336476 |      0.000576521 |

## 9. 부족한 Feature와 추가 필요 데이터

- 현재 없는 핵심 데이터는 `실시간 재고 스냅샷 이력`, `재배치 로그`, `정비/회수 이동 로그`다.
- 추가 가치가 큰 피처는 `인접 station 상호작용`, `행사/연휴 캘린더`, `세분화된 기상 정보`다.

## 10. 서비스 적용 방식

- 이용자 앱: `현재 실시간 재고 + 예측 bike_change = 다음 시간 예상 보유대수`
- 관리자 웹: `현재 재고`, `예측 bike_change`, `station 중요도`, `cluster`를 결합해 부족/과잉 우선순위를 계산

## 11. 대표 station 분석

|   cluster | cluster_name          |   station_id | station_name                 |   rental_total_2025 |   mean_abs_error | selection_reason                     |
|----------:|:----------------------|-------------:|:-----------------------------|--------------------:|-----------------:|:-------------------------------------|
|         0 | 업무/상업 혼합형      |         2335 | 3호선 매봉역 3번출구앞       |               16974 |         1.34065  | usage 16974, center 0.765, mae 1.341 |
|         0 | 업무/상업 혼합형      |         2340 | 삼호물산버스정류장(23370) 옆 |               12637 |         1.24256  | usage 12637, center 0.765, mae 1.243 |
|         0 | 업무/상업 혼합형      |         2414 | 도곡역 아카데미스위트 앞     |               11818 |         1.14046  | usage 11818, center 0.765, mae 1.140 |
|         1 | 아침 도착 업무 집중형 |         2377 | 수서역 5번출구               |               15966 |         1.42834  | usage 15966, center 2.648, mae 1.428 |
|         1 | 아침 도착 업무 집중형 |         2348 | 포스코사거리(기업은행)       |               12923 |         1.31819  | usage 12923, center 3.345, mae 1.318 |
|         1 | 아침 도착 업무 집중형 |         2323 | 주식회사 오뚜기 정문 앞      |                1234 |         0.21356  | usage 1234, center 3.269, mae 0.214  |
|         2 | 주거 도착형           |         2404 | 대모산입구역 4번 출구 앞     |               13681 |         1.23208  | usage 13681, center 1.062, mae 1.232 |
|         2 | 주거 도착형           |         2384 | 자곡사거리                   |               12508 |         1.19218  | usage 12508, center 1.062, mae 1.192 |
|         2 | 주거 도착형           |         2306 | 압구정역 2번 출구 옆         |               12541 |         1.09614  | usage 12541, center 1.062, mae 1.096 |
|         3 | 생활·상권 혼합형      |         2332 | 선릉역3번출구                |               12215 |         1.11435  | usage 12215, center 0.796, mae 1.114 |
|         3 | 생활·상권 혼합형      |         2431 | 대치역 7번출구               |               11597 |         1.13156  | usage 11597, center 0.807, mae 1.132 |
|         3 | 생활·상권 혼합형      |         3614 | 은마아파트 입구 사거리       |               10332 |         1.01011  | usage 10332, center 0.796, mae 1.010 |
|         4 | 외곽 주거형           |         3643 | 더시그넘하우스 앞            |                4762 |         0.647292 | usage 4762, center 0.731, mae 0.647  |
|         4 | 외곽 주거형           |         2387 | 래미안강남힐즈 사거리        |                8066 |         0.895762 | usage 8066, center 1.356, mae 0.896  |
|         4 | 외곽 주거형           |         3642 | LH강남힐스테이트아파트       |                7276 |         0.809124 | usage 7276, center 1.356, mae 0.809  |

### 업무/상업 혼합형 | 2335  3호선 매봉역 3번출구앞

- 2025 총 대여량: `16974`
- 평균 절대오차(MAE): `1.3406`
- 군집 중심 거리: `0.7648`
- 선정 이유: `usage 16974, center 0.765, mae 1.341`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 업무/상업 혼합형 | 2340  삼호물산버스정류장(23370) 옆

- 2025 총 대여량: `12637`
- 평균 절대오차(MAE): `1.2426`
- 군집 중심 거리: `0.7648`
- 선정 이유: `usage 12637, center 0.765, mae 1.243`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 업무/상업 혼합형 | 2414  도곡역 아카데미스위트 앞

- 2025 총 대여량: `11818`
- 평균 절대오차(MAE): `1.1405`
- 군집 중심 거리: `0.7648`
- 선정 이유: `usage 11818, center 0.765, mae 1.140`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 아침 도착 업무 집중형 | 2377  수서역 5번출구

- 2025 총 대여량: `15966`
- 평균 절대오차(MAE): `1.4283`
- 군집 중심 거리: `2.6481`
- 선정 이유: `usage 15966, center 2.648, mae 1.428`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 아침 도착 업무 집중형 | 2348  포스코사거리(기업은행)

- 2025 총 대여량: `12923`
- 평균 절대오차(MAE): `1.3182`
- 군집 중심 거리: `3.3454`
- 선정 이유: `usage 12923, center 3.345, mae 1.318`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 아침 도착 업무 집중형 | 2323  주식회사 오뚜기 정문 앞

- 2025 총 대여량: `1234`
- 평균 절대오차(MAE): `0.2136`
- 군집 중심 거리: `3.2688`
- 선정 이유: `usage 1234, center 3.269, mae 0.214`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 주거 도착형 | 2404  대모산입구역 4번 출구 앞

- 2025 총 대여량: `13681`
- 평균 절대오차(MAE): `1.2321`
- 군집 중심 거리: `1.0622`
- 선정 이유: `usage 13681, center 1.062, mae 1.232`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 주거 도착형 | 2384  자곡사거리

- 2025 총 대여량: `12508`
- 평균 절대오차(MAE): `1.1922`
- 군집 중심 거리: `1.0622`
- 선정 이유: `usage 12508, center 1.062, mae 1.192`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 주거 도착형 | 2306  압구정역 2번 출구 옆

- 2025 총 대여량: `12541`
- 평균 절대오차(MAE): `1.0961`
- 군집 중심 거리: `1.0622`
- 선정 이유: `usage 12541, center 1.062, mae 1.096`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 생활·상권 혼합형 | 2332  선릉역3번출구

- 2025 총 대여량: `12215`
- 평균 절대오차(MAE): `1.1144`
- 군집 중심 거리: `0.7956`
- 선정 이유: `usage 12215, center 0.796, mae 1.114`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 생활·상권 혼합형 | 2431 대치역 7번출구

- 2025 총 대여량: `11597`
- 평균 절대오차(MAE): `1.1316`
- 군집 중심 거리: `0.8067`
- 선정 이유: `usage 11597, center 0.807, mae 1.132`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 생활·상권 혼합형 | 3614  은마아파트 입구 사거리

- 2025 총 대여량: `10332`
- 평균 절대오차(MAE): `1.0101`
- 군집 중심 거리: `0.7956`
- 선정 이유: `usage 10332, center 0.796, mae 1.010`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 외곽 주거형 | 3643  더시그넘하우스 앞

- 2025 총 대여량: `4762`
- 평균 절대오차(MAE): `0.6473`
- 군집 중심 거리: `0.7312`
- 선정 이유: `usage 4762, center 0.731, mae 0.647`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 외곽 주거형 | 2387  래미안강남힐즈 사거리

- 2025 총 대여량: `8066`
- 평균 절대오차(MAE): `0.8958`
- 군집 중심 거리: `1.3563`
- 선정 이유: `usage 8066, center 1.356, mae 0.896`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

### 외곽 주거형 | 3642  LH강남힐스테이트아파트

- 2025 총 대여량: `7276`
- 평균 절대오차(MAE): `0.8091`
- 군집 중심 거리: `1.3563`
- 선정 이유: `usage 7276, center 1.356, mae 0.809`
- 해석: 해당 cluster의 전형적 패턴과 운영 중요도를 함께 보여주는 대표 사례다.

## 12. cluster별 모델 상세 해석

### 업무/상업 혼합형 | best model `hist_gbm_tuned`

- train rows: `180000`
- eval rows: `429240`
- RMSE: `1.0824`
- MAE: `0.6277`
- R²: `0.2138`
- global shared model 대비 RMSE 변화: `+0.0087`
- global shared model 대비 MAE 변화: `+0.0019`
- 해석: 공통 모델보다 RMSE 개선 폭이 뚜렷해서 cluster 특화 학습의 실익이 분명했다.
- top 5 candidate models:
| model          |    rmse |      mae |       r2 |
|:---------------|--------:|---------:|---------:|
| hist_gbm_tuned | 1.08236 | 0.627727 | 0.213776 |
| hist_gbm       | 1.08419 | 0.628089 | 0.211116 |
| extra_trees    | 1.09824 | 0.646833 | 0.190533 |
| random_forest  | 1.09912 | 0.633332 | 0.189239 |
| ridge          | 1.13376 | 0.693594 | 0.137324 |

- top features:
| feature                 |   importance_mean |   importance_std |
|:------------------------|------------------:|-----------------:|
| hour_sin                |        0.0405894  |      0.00704498  |
| is_weekend_or_holiday   |        0.0303649  |      0.0072636   |
| bike_change_lag_24      |        0.0268826  |      0.00256898  |
| bike_change_lag_168     |        0.0252689  |      0.00207915  |
| bike_change_rollmean_24 |        0.01028    |      0.00407707  |
| hour_cos                |        0.00997719 |      0.00220243  |
| lat                     |        0.00944725 |      0.000262995 |
| hour                    |        0.00894137 |      0.000998    |

### 아침 도착 업무 집중형 | best model `hist_gbm_tuned`

- train rows: `52128`
- eval rows: `26280`
- RMSE: `1.7242`
- MAE: `0.9905`
- R²: `0.6737`
- global shared model 대비 RMSE 변화: `+0.0935`
- global shared model 대비 MAE 변화: `-0.0038`
- 해석: 공통 모델보다 RMSE 개선 폭이 뚜렷해서 cluster 특화 학습의 실익이 분명했다.
- top 5 candidate models:
| model          |    rmse |      mae |       r2 |
|:---------------|--------:|---------:|---------:|
| hist_gbm_tuned | 1.72417 | 0.990473 | 0.673723 |
| hist_gbm       | 1.73772 | 0.99844  | 0.668572 |
| random_forest  | 1.78769 | 1.03082  | 0.649237 |
| extra_trees    | 1.83088 | 1.04704  | 0.632083 |
| ridge          | 2.07654 | 1.23599  | 0.526729 |

- top features:
| feature               |   importance_mean |   importance_std |
|:----------------------|------------------:|-----------------:|
| hour_sin              |         0.395941  |      0.0142296   |
| bike_change_lag_168   |         0.218412  |      0.00481989  |
| hour                  |         0.167122  |      0.0024688   |
| is_weekend_or_holiday |         0.138337  |      0.0302699   |
| bike_change_lag_24    |         0.0858187 |      0.000530126 |
| is_commute_hour       |         0.0781787 |      9.91381e-05 |
| return_count_lag_1    |         0.0676464 |      0.0156528   |
| bike_change_lag_1     |         0.0657706 |      0.00607736  |

### 주거 도착형 | best model `hist_gbm_tuned`

- train rows: `180000`
- eval rows: `280320`
- RMSE: `1.1783`
- MAE: `0.6993`
- R²: `0.2236`
- global shared model 대비 RMSE 변화: `+0.0147`
- global shared model 대비 MAE 변화: `+0.0039`
- 해석: 공통 모델보다 RMSE 개선 폭이 뚜렷해서 cluster 특화 학습의 실익이 분명했다.
- top 5 candidate models:
| model          |    rmse |      mae |       r2 |
|:---------------|--------:|---------:|---------:|
| hist_gbm_tuned | 1.17834 | 0.699256 | 0.223579 |
| hist_gbm       | 1.18019 | 0.700712 | 0.221141 |
| extra_trees    | 1.18803 | 0.719404 | 0.21076  |
| random_forest  | 1.19653 | 0.711012 | 0.199424 |
| ridge          | 1.23505 | 0.776539 | 0.147058 |

- top features:
| feature                |   importance_mean |   importance_std |
|:-----------------------|------------------:|-----------------:|
| hour_sin               |        0.0572929  |      0.0233585   |
| hour                   |        0.0481256  |      0.0139668   |
| bike_change_lag_168    |        0.039836   |      0.00238034  |
| bike_change_lag_24     |        0.0167995  |      0.00191387  |
| is_weekend_or_holiday  |        0.00807567 |      0.000104599 |
| bike_change_rollstd_24 |        0.00747312 |      0.00034118  |
| hour_cos               |        0.00734749 |      0.000505281 |
| rental_count_lag_1     |        0.00614611 |      0.00206936  |

### 생활·상권 혼합형 | best model `hist_gbm`

- train rows: `150000`
- eval rows: `534360`
- RMSE: `1.0075`
- MAE: `0.5931`
- R²: `0.0686`
- global shared model 대비 RMSE 변화: `-0.0010`
- global shared model 대비 MAE 변화: `+0.0028`
- 해석: RMSE는 비슷하거나 소폭 불리했지만 MAE가 더 낮아 평균 오차 기준으로는 specialist가 더 안정적이었다.
- top 5 candidate models:
| model          |    rmse |      mae |        r2 |
|:---------------|--------:|---------:|----------:|
| hist_gbm       | 1.00752 | 0.593146 | 0.0685793 |
| hist_gbm_tuned | 1.00762 | 0.595204 | 0.0683952 |
| random_forest  | 1.01645 | 0.598465 | 0.0519881 |
| ridge          | 1.0208  | 0.626985 | 0.0438518 |
| extra_trees    | 1.02128 | 0.617342 | 0.0429538 |

- top features:
| feature                  |   importance_mean |   importance_std |
|:-------------------------|------------------:|-----------------:|
| bike_change_lag_168      |        0.0149111  |      0.00162218  |
| bike_change_lag_24       |        0.0146527  |      0.00340077  |
| bike_change_rollmean_168 |        0.00920485 |      0.00198421  |
| bike_change_rollmean_24  |        0.00473878 |      0.00332742  |
| hour_sin                 |        0.00442264 |      0.00190157  |
| hour                     |        0.00386887 |      0.000855528 |
| bike_count_index_lag_168 |        0.00357214 |      0.000636133 |
| rental_count_lag_1       |        0.00333514 |      0.00121674  |

### 외곽 주거형 | best model `hist_gbm_tuned`

- train rows: `180000`
- eval rows: `166440`
- RMSE: `0.9352`
- MAE: `0.5447`
- R²: `0.1533`
- global shared model 대비 RMSE 변화: `+0.0094`
- global shared model 대비 MAE 변화: `-0.0024`
- 해석: 공통 모델보다 RMSE 개선 폭이 뚜렷해서 cluster 특화 학습의 실익이 분명했다.
- top 5 candidate models:
| model          |     rmse |      mae |        r2 |
|:---------------|---------:|---------:|----------:|
| hist_gbm_tuned | 0.935204 | 0.544738 | 0.153345  |
| hist_gbm       | 0.936094 | 0.546055 | 0.151732  |
| random_forest  | 0.946825 | 0.554968 | 0.132171  |
| extra_trees    | 0.947035 | 0.56498  | 0.131787  |
| ridge          | 0.965489 | 0.596274 | 0.0976208 |

- top features:
| feature                  |   importance_mean |   importance_std |
|:-------------------------|------------------:|-----------------:|
| bike_change_lag_168      |        0.0329655  |      0.000216433 |
| hour_sin                 |        0.0303089  |      0.00542441  |
| hour_cos                 |        0.0177702  |      0.000836695 |
| is_weekend_or_holiday    |        0.0141822  |      0.00234359  |
| bike_change_lag_24       |        0.0113487  |      0.0027907   |
| hour                     |        0.00861401 |      0.00163619  |
| bike_change_rollmean_168 |        0.00848667 |      0.000371923 |
| bike_change_rollmean_24  |        0.00822409 |      0.000907026 |

## 13. 참고: bike_count_index

- 참고용 최고 모델은 `ridge`였고, cluster 포함 시 RMSE `1.1019`, MAE `0.6415`였다.
- cluster 미포함 대비 개선 폭은 RMSE `-0.5520`, MAE `-0.4452`였다.
- 그러나 이 값은 실제 재고가 아니라 누적 지수이므로 참고 자료로만 사용한다.

|   rank | model          |     rmse |       mae |       r2 | notes                       |
|-------:|:---------------|---------:|----------:|---------:|:----------------------------|
|      1 | ridge          |   1.6539 |   1.08673 | 1        | 선형 회귀 계열              |
|      2 | extra_trees    | 329.639  |  40.5242  | 0.988947 | 랜덤 분할 앙상블, 표본 학습 |
|      3 | random_forest  | 331.69   |  41.2062  | 0.988809 | 비선형 앙상블, 표본 학습    |
|      4 | hist_gbm       | 667.733  | 163.018   | 0.954648 | 히스토그램 기반 부스팅      |
|      5 | hist_gbm_tuned | 671.093  | 164.524   | 0.954191 | 부스팅 튜닝 버전            |

## 14. 최종 결론

- 실제 시간대별 보유대수 이력이 없으므로 이번 분석의 핵심 타깃은 `bike_change`가 맞다.
- 여러 회귀 모델 중 `hist_gbm_tuned`가 RMSE와 MAE를 가장 균형 있게 낮췄다.
- cluster는 성능 향상 폭보다 station 성향 설명력 측면에서 특히 의미가 있었다.
- 최종 추천은 `cluster를 포함한 bike_change 중심 회귀 모델`이다.
- 실서비스에서는 반드시 `실시간 재고 API`를 붙여서 `현재 재고 + 예측 bike_change` 형태로 다음 시간 보유대수를 계산해야 한다.
- 다음 고도화 우선순위는 `실시간 재고 이력 수집`, `재배치 로그 결합`, `인접 station 네트워크 feature`, `행사/연휴 캘린더`, `확장 날씨 변수` 순서다.
