# Station-Hour Regression Report

## 1. 분석 개요

- 학습 기간: 2023-01-01 ~ 2024-12-31
- 테스트 기간: 2025-01-01 ~ 2025-12-31
- 비교 대상 타깃: `bike_change`(시간별 변화량), `bike_count_index`(관측 기반 재고지수)
- 주의: `bike_count_index`는 절대 재고가 아니라 대여/반납 로그 누적 지수다.

## 2. 검토 과정

- 1차: `HistGradientBoostingRegressor`로 `basic` vs `enhanced` feature set 비교
- 2차: 선택된 feature set으로 `Dummy`, `Ridge`, `RandomForest`, `ExtraTrees`, `HistGradientBoosting` 계열 비교
- 3차: 타깃별 최고 ML 모델을 다시 학습하고 2025 전체 성능 및 permutation importance 점검

## 3. 최종 요약

- 변화량 예측 최고 ML 모델: `hist_gbm_tuned`
- 재고지수 예측 최고 ML 모델: `ridge`
- 정규화 RMSE 기준 더 쉬운 타깃: `bike_count_index`

## 4. 최종 성능

### bike_change

- 모델: `hist_gbm_tuned`
- feature set: `enhanced`
- RMSE: `1.0543`
- MAE: `0.5870`
- R²: `0.2057`
- normalized RMSE: `0.8913`
- normalized MAE: `0.4963`

### bike_count_index

- 모델: `ridge`
- feature set: `basic`
- RMSE: `1.6539`
- MAE: `1.0867`
- R²: `1.0000`
- normalized RMSE: `0.0005`
- normalized MAE: `0.0003`

## 5. 중요 피처 상위 10개

### bike_change

- `bike_change_lag_168`: 0.057777
- `bike_change_lag_24`: 0.035289
- `hour_sin`: 0.028665
- `is_weekend_or_holiday`: 0.008634
- `bike_change_rollmean_24`: 0.007008
- `hour`: 0.006307
- `return_count_lag_24`: 0.005528
- `is_commute_hour`: 0.005392
- `bike_change_rollstd_168`: 0.004863
- `bike_change_rollmean_3`: 0.004686

### bike_count_index

- `bike_count_index_lag_1`: 2363.140922
- `bike_index_rollmean_3`: 1073.451672
- `bike_count_index_lag_2`: 720.198722
- `bike_index_rollmean_24`: 204.297380
- `bike_index_rollmean_168`: 9.003119
- `bike_count_index_lag_168`: 7.270158
- `bike_count_index_lag_24`: 0.917543
- `bike_change_lag_1`: 0.078830
- `month`: 0.072450
- `dayofyear`: 0.071960

## 6. 추가로 고려할 피처

- 실시간 또는 시간대별 실제 자전거 재배치 로그
- station별 물리 거치대 수의 월별 변동 이력
- 공휴일/연휴/행사 일정의 정형화된 캘린더 파일
- 강수 형태, 체감온도, 적설량 같은 확장 날씨 변수
- 인접 station의 순유입/순유출과 같은 공간적 상호작용 피처
