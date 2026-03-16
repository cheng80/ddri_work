# cheng80 군집 0~4 분석 요약

작성일: 2026-03-16  
대상: `works/05_prediction_long/cheng80/` (cluster00~04 모델링·2차·3차·축소 피처)  
용도: cheng80 군집별 실험 결과 요약

---

## 1. cheng80 폴더 구조

```
works/05_prediction_long/cheng80/
├── cluster00/     # 업무/상업 혼합형
│   ├── 01_cluster_modeling.ipynb
│   └── 02_cluster_modeling_second_round.ipynb
├── cluster01/     # 아침 도착 업무 집중형
│   ├── 01_cluster_modeling.ipynb
│   ├── 02_cluster_modeling_second_round.ipynb
│   ├── 03_cluster_modeling_third_round.ipynb
│   ├── 04_ddri_cluster01_subset_experiment_design.md
│   └── 05_cluster_modeling_subset_experiment.ipynb
├── cluster02/     # 주거 도착형
│   ├── 01_cluster_modeling.ipynb
│   ├── 02_cluster_modeling_second_round.ipynb
│   ├── 03_ddri_cluster02_subset_recheck_design.md
│   └── 04_cluster_modeling_subset_recheck.ipynb
├── cluster03/     # 생활권 혼합형
│   ├── 01_cluster_modeling.ipynb
│   └── 02_cluster_modeling_second_round.ipynb
├── cluster04/     # 외곽 주거형
│   ├── 01_cluster_modeling.ipynb
│   └── 02_cluster_modeling_second_round.ipynb
├── summary_aggregation/   # 결과 집계
├── rep15_error_analysis/ # 대표 15개 오류 분석
├── 07_ddri_cluster_final_recommendation.md
└── archive_docs/
```

---

## 2. 분석 대상·데이터

### 2.1 군집별 대표 대여소 (5군집 × 3개 = 15개)


| cluster   | 군집명          | 대표 대여소 (station_id)                               |
| --------- | ------------ | ------------------------------------------------- |
| cluster00 | 업무/상업 혼합형    | 4908 SB타워 앞, 2328 르네상스 호텔 사거리, 4902 구역삼세무서 교차로    |
| cluster01 | 아침 도착 업무 집중형 | 2377 수서역 5번출구, 2323 주식회사 오뚜기 정문 앞, 2348 포스코사거리    |
| cluster02 | 주거 도착형       | 2312 청담역 13번 출구, 2354 청담역 2번출구, 4917 일원에코파크 주차장   |
| cluster03 | 생활권 혼합형      | 2321 학여울역 사거리, 2320 도곡역 대치지구대 방향, 3616 역삼중학교 앞    |
| cluster04 | 외곽 주거형       | 3643 더시그넘하우스 앞, 2359 국립국악중·고교 정문 맞은편, 2392 구룡산 입구 |


### 2.2 데이터·분할

- **1차**: `3조 공유폴더/.../raw_data/` (기본 15컬럼)
- **2차**: `3조 공유폴더/.../second_round_data/` (정적·교통·환경·POI 추가)
- **분할**: train=2023, valid=2024, test=2025 (2023+2024 재학습 후 2025 평가)
- **타깃**: `rental_count` (시간당 대여건수)

---

## 3. 1차·2차 Test(2025) 점수 비교


| cluster   | 군집명          | 1차 RMSE | 1차 MAE | 1차 R²  | 2차 RMSE | 2차 MAE | 2차 R²  | RMSE Δ  |
| --------- | ------------ | ------- | ------ | ------ | ------- | ------ | ------ | ------- |
| cluster00 | 업무/상업 혼합형    | 0.8113  | 0.5439 | 0.3212 | 0.8085  | 0.5403 | 0.3259 | -0.0028 |
| cluster01 | 아침 도착 업무 집중형 | 1.3462  | 0.8042 | 0.6398 | 1.3324  | 0.7868 | 0.6471 | -0.0138 |
| cluster02 | 주거 도착형       | 0.8088  | 0.5059 | 0.4987 | 0.8059  | 0.5053 | 0.5022 | -0.0029 |
| cluster03 | 생활권 혼합형      | 0.6901  | 0.4928 | 0.1802 | 0.6882  | 0.4882 | 0.1848 | -0.0019 |
| cluster04 | 외곽 주거형       | 0.7160  | 0.4425 | 0.3785 | 0.7145  | 0.4427 | 0.3811 | -0.0015 |


- 전 군집 2차에서 RMSE 소폭 개선
- **cluster01** 개선폭 가장 큼 (-0.0138)

---

## 4. 군집별 최종 권장안 (07_ddri_cluster_final_recommendation 기준)


| cluster   | 군집명          | 권장 모델                | 최종 Test RMSE | 권장 수준                   |
| --------- | ------------ | -------------------- | ------------ | ----------------------- |
| cluster00 | 업무/상업 혼합형    | LightGBM_RMSE        | 0.8085       | 공통 baseline + 선택적 피처 보강 |
| cluster01 | 아침 도착 업무 집중형 | **LightGBM_Poisson** | **1.3108**   | 군집별 커스텀 우선 적용           |
| cluster02 | 주거 도착형       | **LightGBM_Poisson** | **0.7990**   | compact + objective 전환  |
| cluster03 | 생활권 혼합형      | LightGBM_RMSE        | 0.6882       | 추가 검토 대상 (R² 낮음)        |
| cluster04 | 외곽 주거형       | LightGBM_RMSE        | 0.7145       | 공통 baseline 우선          |


---

## 5. 군집별 상세

### 5.1 cluster00 – 업무/상업 혼합형

- **1차**: RMSE 0.8113, MAE 0.5439
- **2차**: RMSE 0.8085, MAE 0.5403
- **해석**: 출퇴근·상권 피처 보강 시 소폭 개선
- **권장 피처**: is_commute_hour, subway_distance_m, bus_stop_count_300m, restaurant_count_300m, cafe_count_300m, rolling_mean_6h

### 5.2 cluster01 – 아침 도착 업무 집중형

- **1차**: RMSE 1.3462
- **2차**: RMSE 1.3324
- **3차**: RMSE 1.3189 (LightGBM_Poisson 전환)
- **축소 피처**: RMSE **1.3108** (subset_a_commute_transit)
- **해석**: 가장 어렵지만, Poisson·축소 피처에서 개선 큼
- **권장 피처**: is_commute_hour, commute_morning_flag, commute_evening_flag, subway_distance_m, bus_stop_count_300m

### 5.3 cluster02 – 주거 도착형

- **1차**: RMSE 0.8088
- **2차**: RMSE 0.8059
- **축소 재검증**: RMSE **0.7990** (subset_d + LightGBM_Poisson)
- **해석**: 피처 축소보다 **objective 전환**이 더 유효
- **권장 피처**: is_night_hour, is_weekend, is_holiday_eve, heavy_rain_flag, station_elevation_m, bus_stop_count_300m

### 5.4 cluster03 – 생활권 혼합형

- **1차**: RMSE 0.6901
- **2차**: RMSE 0.6882
- **해석**: RMSE는 낮으나 **R² 낮음** → 구조 보완 후보
- **권장 피처**: restaurant_count_300m, cafe_count_300m, convenience_store_count_300m, is_lunch_hour, rolling_mean_6h

### 5.5 cluster04 – 외곽 주거형

- **1차**: RMSE 0.7160
- **2차**: RMSE 0.7145
- **해석**: 개선 방향은 맞으나 폭 매우 작음
- **권장 피처**: station_elevation_m, elevation_diff_nearest_subway_m, distance_naturepark_m, distance_river_boundary_m, bus_stop_count_300m (선택적)

---

## 6. Validation vs Test 요약


| cluster   | validation_2024 RMSE | test_2025_refit RMSE | gap    |
| --------- | -------------------- | -------------------- | ------ |
| cluster00 | 0.8987               | 0.8113               | -0.087 |
| cluster01 | 1.5660               | 1.3462               | -0.220 |
| cluster02 | 0.8263               | 0.8088               | -0.017 |
| cluster03 | 0.7898               | 0.6901               | -0.100 |
| cluster04 | 0.7852               | 0.7160               | -0.069 |


- cluster01: validation–test 격차 가장 큼 (과대적합 가능성)
- cluster02: 격차 가장 작음 (안정적)

---

## 7. 핵심 정리


| 구분            | 핵심 내용                                                            |
| ------------- | ---------------------------------------------------------------- |
| **공통**        | 전 군집 LightGBM_RMSE 1차 baseline, 2차 round2 피처로 소폭 개선              |
| **cluster01** | Poisson + subset_a_commute_transit으로 RMSE 1.31까지 개선, 군집별 커스텀 1순위 |
| **cluster02** | Poisson + compact 피처로 RMSE 0.80, objective 전환 효과 확인              |
| **cluster03** | RMSE 낮으나 R² 낮음, 추가 검토 대상                                         |
| **cluster04** | 2차 개선폭 매우 작음, 공통 baseline 유지                                     |


