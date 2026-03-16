# ksm_note 폴더 분석 요약

작성일: 2026-03-16  
대상: `ksm_note/` 폴더 (외곽 주거형 Top3 모델링·2단계·소프트보팅·재배치)  
용도: ksm_note 분석 내용 요약

---

## 1. ksm_note 폴더 구조

```
ksm_note/
├── TWO_STAGE_2359_3643/     # 2단계 모델 (2359, 3643)
│   ├── run_two_stage_top2.py
│   ├── README.md, 01_결과요약.md
│   └── station_*_validation_*, station_*_test_*, station_*_predictions_2025.csv
├── SOFT_VOTING_2359_3643/   # 소프트보팅 앙상블 (2359, 3643)
│   ├── run_soft_voting_top2.py
│   ├── README.md, 01_결과요약.md
│   └── station_*_soft_weight_*, station_*_predictions_2025.csv
└── FINAL_DELIVERABLE/       # 최종 발표/제출용
    ├── md/                  # 01~05 보고서 md
    ├── pdf/
    └── speech/md/           # 발표 스피치 원고
```

---

## 2. 분석 대상·데이터

### 2.1 대상 군집·대여소

- **군집**: 외곽 주거형 (cluster04)
- **대표 대여소 3개**:
  - `2359` 국립국악중,고교 정문 맞은편
  - `2392` 구룡산 입구 (구룡산 서울둘레길 입구)
  - `3643` 더시그넘하우스 앞

### 2.2 데이터·분할

- **입력**: `ksm_note/Data/ddri_prediction_long_*_second_round_feature_collection.csv`
- **분할**: train=2023, valid=2024, test=2025 (2023+2024 재학습 후 2025 평가)
- **예측 대상**: 시간당 대여건수 (0, 1, 2, 3, 4, …)

---

## 3. 최종 운영안 (FINAL_DELIVERABLE)

### 3.1 모델·피처

| 항목 | 내용 |
|------|------|
| 모델 | LightGBM_RMSE |
| 피처 | baseline + is_weekend (1개 추가) |
| 전처리 | hour/weekday/month 원핫 인코딩 |

### 3.2 전체(Top3 통합) 성능

| split | RMSE | MAE | R² | exact_match_rate | n_samples |
|-------|------|-----|-----|------------------|-----------|
| train_2023 | 0.5425 | 0.3444 | 0.7120 | 75.38% | 26,280 |
| validation_2024 | 0.8098 | 0.5128 | 0.2938 | 64.86% | 26,352 |
| test_2025_refit | 0.7282 | 0.4540 | 0.3571 | **67.96%** | 26,280 |

### 3.3 대여소별 Test(2025) 성능

| station_id | station_name | RMSE | MAE | R² | exact_match_rate |
|------------|--------------|------|-----|-----|------------------|
| 2359 | 국립국악중,고교 정문 맞은편 | 0.9229 | 0.6494 | 0.330 | 52.84% |
| 2392 | 구룡산 입구 | 0.2863 | 0.1459 | -0.044 | **92.71%** |
| 3643 | 더시그넘하우스 앞 | 0.8106 | 0.5666 | 0.249 | 58.32% |

- **2392**: 수요가 매우 희소해 exact_match가 높음
- **2359, 3643**: 변동성이 커서 예측 난이도 높음

---

## 4. 2단계 모델 (TWO_STAGE_2359_3643)

### 4.1 구조

- **1단계**: 0대 vs 1대 이상 분류
- **2단계**: 1대 이상일 때 건수 회귀
- **튜닝**: valid에서 `threshold_nonzero`, `scale_positive`, `bias_positive` 탐색

### 4.2 Test(2025) 결과 (단일 LightGBM vs 2단계)

| station_id | baseline exact | two_stage exact | delta exact | baseline RMSE | two_stage RMSE | delta RMSE |
|------------|---------------|-----------------|-------------|---------------|----------------|------------|
| 2359 | 0.5209 | **0.5747** | +0.0538 | 0.9348 | 1.2092 | +0.2744 |
| 3643 | 0.5798 | **0.6712** | +0.0914 | 0.8535 | 0.9632 | +0.1096 |

- **Exact(정수 반올림 일치율)**는 두 대여소 모두 개선
- 3643은 0.67로 목표 0.7에 근접
- RMSE/±1 정확도는 일부 하락 → 정확일치 최적화에 따른 트레이드오프

### 4.3 최적 튜닝 파라미터

- 2359: `threshold=0.84`, `scale=0.74`, `bias=-0.35`
- 3643: `threshold=0.82`, `scale=0.70`, `bias=-0.40`

---

## 5. 소프트보팅 앙상블 (SOFT_VOTING_2359_3643)

### 5.1 구성

- **Base 모델**: LightGBM, XGBoost, RandomForest
- **가중치**: 합=1, 0.05 간격 그리드 탐색
- **선택 기준**: exact_match → bucket → RMSE

### 5.2 최적 가중치 (Validation 2024)

- 2359: LightGBM 0.80, XGBoost 0.15, RF 0.05
- 3643: LightGBM 0.75, XGBoost 0.25, RF 0.00

### 5.3 Test(2025) 결과 (단일 LightGBM vs 앙상블)

| station_id | baseline exact | ensemble exact | delta exact | baseline RMSE | ensemble RMSE |
|------------|----------------|----------------|-------------|---------------|---------------|
| 2359 | 0.5209 | 0.5212 | +0.0003 | 0.9348 | 0.9318 |
| 3643 | 0.5798 | 0.5788 | -0.0010 | 0.8535 | 0.8530 |

- **해석**: 2359는 소폭 개선, 3643은 단일 LightGBM 유지가 더 안정적

---

## 6. 피처·모델링 가이드

### 6.1 기본 유지 피처

- hour, weekday, month, holiday, temperature, humidity, precipitation, wind_speed
- station_id, cluster, mapped_dong_code
- lag_1h, lag_24h, lag_168h, rolling_mean_24h, rolling_std_24h, rolling_mean_168h, rolling_std_168h

### 6.2 외곽 주거형 우선 추가 피처 (7개)

- is_night_hour, is_weekend
- station_elevation_m, elevation_diff_nearest_subway_m
- distance_naturepark_m, distance_river_boundary_m
- bus_stop_count_300m

### 6.3 Ablation 결과 (1개/2개 추가)

| 조합 | validation RMSE | test RMSE | 비고 |
|------|-----------------|-----------|------|
| baseline | 0.786281 | 0.716329 | - |
| + is_weekend | 0.785635 | 0.714925 | **최종 채택** |
| + distance_naturepark_m + distance_river_boundary_m | 0.785291 | 0.715119 | 2개 조합 최적 |

- 개선 폭은 작아 **경량 커스텀**이 실무적
- 최종 운영안: `baseline + is_weekend`

### 6.4 전역 피처 중요도 상위

1. hour  
2. lag_168h  
3. is_night_hour  
4. lag_24h  
5. rolling_mean_24h  
6. rolling_mean_168h  
7. precipitation  
8. lag_1h  
9. temperature  
10. is_weekend  

→ 정적 상권보다 **시간 패턴 + 반복 패턴 + 야간/주말 + 날씨**가 중요

### 6.5 대여소별 핵심 피처

| station_id | 특성 | 우선 피처 |
|------------|------|-----------|
| 2359 | 주간 반복성 강, 야간/비 감소 큼 | hour, lag_168h, is_night_hour, precipitation |
| 2392 | 수요 매우 희소, 단순 구조 유리 | hour, lag_24h, lag_168h, is_night_hour |
| 3643 | 2359와 유사, rolling 반응 좋음 | hour, lag_168h, lag_24h, rolling_mean_24h, is_night_hour, precipitation |

---

## 7. 재배치 계획 (Rebalance Plan)

### 7.1 목적

- 여유 대여소 → 부족 대여소로 시간대별 이동 권고 생성
- 입력: 2025 예측 결과

### 7.2 기준재고 (baseline_stock)

| station_id | baseline_stock |
|------------|----------------|
| 2359 | 2 |
| 2392 | 1 |
| 3643 | 2 |

### 7.3 대여소별 요약 (2025)

| station_id | predicted_shortage_hours | actual_shortage_hours | total_received | total_sent |
|------------|--------------------------|------------------------|----------------|------------|
| 2359 | 1,093 | 1,697 | 27 | 29 |
| 2392 | 131 | 557 | 7 | 0 |
| 3643 | 632 | 1,168 | 23 | 28 |

- 전체: 57건 이동 권고, 57대 이동
- **미반영**: 실시간 재고, 차량/인력 제약, 거리·비용 최적화

---

## 8. 핵심 정리

| 구분 | 핵심 내용 |
|------|-----------|
| **최종 운영안** | LightGBM_RMSE + baseline + is_weekend. Test exact 67.96%, 2392가 92.71%로 가장 높음. |
| **2단계 모델** | 2359·3643에서 exact 일치율 개선(3643→0.67). RMSE는 상승하는 트레이드오프. |
| **소프트보팅** | 2359·3643에서 개선 미미. 단일 LightGBM 유지가 더 안정적. |
| **피처 전략** | 경량 커스텀. is_weekend 1개 추가가 validation/test 모두 개선. |
| **재배치** | 예측 기반 부족/여유 판단까지 반영. 최적 경로·제약 최적화는 미구현. |
