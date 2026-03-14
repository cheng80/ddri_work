# 03 Prediction

이 폴더는 프로젝트의 `station-day` 단위 baseline 예측 작업 경로다.

현재 주력 정본인 `station-hour` 실험 폴더는 아래 두 경로다.

- [05_prediction_long](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long)
- [06_prediction_long_full](/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full)

따라서 `03_prediction`은 최종 주력 실험 폴더라기보다, 그 이전 레이어의 `일 단위 baseline`, 데이터셋 설계 설명, 운영 보조 지표 검토를 보관하는 참조 경로로 읽는 것이 맞다.

## 목적

- 공통 대여소 기준 `station-day` baseline 데이터셋 생성
- `2023 train / 2024 validation / 2025 test` 기준 baseline 회귀 비교
- 운영 보조 지표와 데이터 결합 구조 설명

## 먼저 볼 파일

- 데이터셋 생성 스크립트: [ddri_station_day_dataset_builder.py](/Users/cheng80/Desktop/ddri_work/works/03_prediction/04_scripts/ddri_station_day_dataset_builder.py)
- 베이스라인 모델 노트북: [02_ddri_station_day_baseline_modeling.ipynb](/Users/cheng80/Desktop/ddri_work/works/03_prediction/04_scripts/02_ddri_station_day_baseline_modeling.ipynb)
- 학습 데이터셋: [ddri_station_day_train_baseline_dataset.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/02_data/ddri_station_day_train_baseline_dataset.csv)
- 테스트 데이터셋: [ddri_station_day_test_baseline_dataset.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/02_data/ddri_station_day_test_baseline_dataset.csv)
- 모델 성능 비교표: [ddri_station_day_baseline_model_metrics.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/02_data/ddri_station_day_baseline_model_metrics.csv)
- 중요도 차트: [ddri_station_day_lightgbm_feature_importance.png](/Users/cheng80/Desktop/ddri_work/works/03_prediction/03_images/ddri_station_day_lightgbm_feature_importance.png)

## 세부 구분

- `01_dataset_design`
- `02_data`
- `03_images`
- `04_scripts`
- `support_scripts`
- `support_data`
- `support_images`

설계 문서, 데이터, 이미지, 스크립트는 각 번호 폴더 기준으로 열람하면 된다.

## 보관 경로

- 데이터셋 설명 노트북: [01_ddri_station_day_dataset_explainer.ipynb](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_scripts/01_ddri_station_day_dataset_explainer.ipynb)
- 운영 지표 차트 스크립트: [ddri_flow_metrics_chart_builder.py](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_scripts/ddri_flow_metrics_chart_builder.py)
- 지원용 생성 CSV:
  - [ddri_station_day_target_train_2023_2024.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_data/ddri_station_day_target_train_2023_2024.csv)
  - [ddri_station_day_target_test_2025.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_data/ddri_station_day_target_test_2025.csv)
  - [ddri_weather_daily_2023_2024.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_data/ddri_weather_daily_2023_2024.csv)
  - [ddri_weather_daily_2025.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_data/ddri_weather_daily_2025.csv)
  - [ddri_station_day_flow_metrics_summary.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_data/ddri_station_day_flow_metrics_summary.csv)
  - [ddri_station_day_test_exception_cases.csv](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_data/ddri_station_day_test_exception_cases.csv)
- 설명용 차트 이미지:
  - [ddri_flow_metrics_summary.png](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_images/ddri_flow_metrics_summary.png)
  - [ddri_same_station_return_ratio_boxplot.png](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_images/ddri_same_station_return_ratio_boxplot.png)
  - [ddri_prediction_feature_correlation_heatmap.png](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_images/ddri_prediction_feature_correlation_heatmap.png)
  - [ddri_holiday_weekend_rental_comparison.png](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_images/ddri_holiday_weekend_rental_comparison.png)
  - [ddri_monthly_avg_rental_trend.png](/Users/cheng80/Desktop/ddri_work/works/03_prediction/support_images/ddri_monthly_avg_rental_trend.png)

위 파일들은 baseline 정본 실행 경로는 아니지만, 설명, 재생성, 예외 추적을 위해 현재 작업이 직접 참조할 수 있는 보조 경로다.

## 현재 해석

- 이 폴더의 핵심 산출물은 `station-day` baseline CSV와 성능표다
- 최종 서비스 직전 핵심 읽기 경로는 아니지만, baseline 근거와 비교 출발점으로는 유지 가치가 있다
- 차후 구조 정리 때도 `station-hour` 정본과 섞지 않고 `baseline/참조 경로`로 분리해서 다뤄야 한다

## 현재 baseline 모델링 기준

- 검증 전략: `Train=2023`, `Validation=2024`, `Test=2025`
- 기준 노트북: `02_ddri_station_day_baseline_modeling.ipynb`
