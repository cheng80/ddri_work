# Session Handoff

## 프로젝트 목표

- 대상 타깃은 `bike_change`
- 목적은 `현재 시점 t`까지의 정보로 `다음 시점 t+1`의 `bike_change`를 예측하는 것
- 현재 사용자 기준 해석:
  - 예: `6시까지의 정보`로 `7시 bike_change` 예측
  - 따라서 `7시에 실제로 관측되는 값`이 feature에 들어가면 안 됨

## 현재까지의 핵심 결론

- 초기에는 `bike_change_deseasonalized`, `bike_change_seasonal_expected`, `return_count_deseasonalized` 같은 feature가 높은 성능을 만들었지만, 이들은 현재/예측 대상 시점 정보를 직접 반영할 가능성이 커서 누수 위험이 있음
- 엄격 비누수 기준에서는 성능이 많이 낮아졌고, 사용자 요구에 따라 다시 feature 기준을 완화하며 여러 번 재실험함
- 가장 최근 실험에서는:
  - `bike_change_deseasonalized`만 제외
  - 시계열 feature는 제외
  - 나머지 feature는 상관계수 `0.9` 이상 중복만 제거
  - 결과:
    - train R2 `0.5092`
    - valid R2 `0.4116`
    - test R2 `0.3944`
- 하지만 이 결과도 `6시 -> 7시 예측` 문제 정의에 완전히 맞는 구조는 아님
  - 이유: row 시각 `t`의 일부 feature가 실제 `t` 시점 관측값일 수 있음
  - 사용자 최종 요구는 `t 시점 정보로 t+1 예측`이므로, 데이터셋을 한 번 더 재구성해야 함

## 현재 사용자 최종 요구사항

- `2023=train`, `2024=valid`, `2025=test`
- 하지만 feature는 반드시 `t 시점까지 알 수 있는 정보`만 사용
- 즉 `6시 정보 -> 7시 예측` 구조가 맞아야 함
- `bike_change`를 직접 쓰는 feature는 제외
- 시계열 정보는 사용하지 않는 순수 feature 실험도 원했지만, 마지막으로는 문제 정의를 명확히 하면서 `t -> t+1` 구조가 맞아야 한다고 합의됨

## 현재 남아 있는 주요 파일

### 스크립트

- [`run_hierarchical_compact_regression.py`](/c:/Users/TJ/ddri_work/hmw/run_hierarchical_compact_regression.py)
- [`build_deseasonalized_splits.py`](/c:/Users/TJ/ddri_work/hmw/build_deseasonalized_splits.py)
- [`build_hierarchical_compact_splits.py`](/c:/Users/TJ/ddri_work/hmw/build_hierarchical_compact_splits.py)
- [`build_compact_bike_change_splits.py`](/c:/Users/TJ/ddri_work/hmw/build_compact_bike_change_splits.py)
- [`run_station_hour_regression.py`](/c:/Users/TJ/ddri_work/hmw/run_station_hour_regression.py)

### 현재 데이터

- 원천 전처리 단계
  - [`station_hour_bike_change_deseason_train_2023.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_deseason_train_2023.parquet)
  - [`station_hour_bike_change_deseason_valid_2024.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_deseason_valid_2024.parquet)
  - [`station_hour_bike_change_deseason_test_2025.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_deseason_test_2025.parquet)
- reduced 단계
  - [`station_hour_bike_change_deseason_reduced_train_2023.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_deseason_reduced_train_2023.parquet)
  - [`station_hour_bike_change_deseason_reduced_valid_2024.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_deseason_reduced_valid_2024.parquet)
  - [`station_hour_bike_change_deseason_reduced_test_2025.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_deseason_reduced_test_2025.parquet)
- hierarchical compact 단계
  - [`station_hour_bike_change_hierarchical_compact_train_2023.csv.gz`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_hierarchical_compact_train_2023.csv.gz)
  - [`station_hour_bike_change_hierarchical_compact_sampled_train_2023.csv.gz`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_hierarchical_compact_sampled_train_2023.csv.gz)
  - [`station_hour_bike_change_hierarchical_compact_valid_2024.csv.gz`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_hierarchical_compact_valid_2024.csv.gz)
  - [`station_hour_bike_change_hierarchical_compact_test_2025.csv.gz`](/c:/Users/TJ/ddri_work/hmw/Data/station_hour_bike_change_hierarchical_compact_test_2025.csv.gz)
- 기타
  - [`ddri_second_cluster_train_with_labels.csv`](/c:/Users/TJ/ddri_work/hmw/Data/clustering/ddri_second_cluster_train_with_labels.csv)
  - [`gangnam_weather_1year_2023.csv`](/c:/Users/TJ/ddri_work/hmw/Data/gangnam_weather_1year_2023.csv)
  - [`gangnam_weather_1year_2024.csv`](/c:/Users/TJ/ddri_work/hmw/Data/gangnam_weather_1year_2024.csv)
  - [`gangnam_weather_1year_2025.csv`](/c:/Users/TJ/ddri_work/hmw/Data/gangnam_weather_1year_2025.csv)

### 최근 결과 파일

- [`hierarchical_compact_final_metrics.csv`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_final_metrics.csv)
- [`hierarchical_compact_model_benchmark.csv`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_model_benchmark.csv)
- [`hierarchical_compact_cluster_best_models.csv`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_cluster_best_models.csv)
- [`hierarchical_compact_cluster_comparison.csv`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_cluster_comparison.csv)
- [`hierarchical_compact_cluster_feature_importance.csv`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_cluster_feature_importance.csv)
- [`hierarchical_compact_global_feature_importance.csv`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_global_feature_importance.csv)
- [`hierarchical_compact_test_predictions.csv.gz`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_test_predictions.csv.gz)
- [`hierarchical_compact_test_predictions.parquet`](/c:/Users/TJ/ddri_work/hmw/Data/hierarchical_compact_test_predictions.parquet)

### 현재 리포트/시각화

- [`hierarchical_compact_model_report.md`](/c:/Users/TJ/ddri_work/hmw/reports/hierarchical_compact_model_report.md)
- [`hierarchical_compact_model_report.pdf`](/c:/Users/TJ/ddri_work/hmw/reports/hierarchical_compact_model_report.pdf)
- [`hierarchical_compact_assets`](/c:/Users/TJ/ddri_work/hmw/reports/hierarchical_compact_assets)
- [`feature_compaction_assets`](/c:/Users/TJ/ddri_work/hmw/reports/feature_compaction_assets)

## 최근 점수

가장 최근 실행 결과:

- global best model: `lightgbm_balanced`
- feature variant: `compact_safe_with_cluster`

점수:

- train
  - RMSE `0.6766`
  - MAE `0.3975`
  - R2 `0.5092`
- valid
  - RMSE `0.9752`
  - MAE `0.5806`
  - R2 `0.4116`
- test
  - RMSE `0.9251`
  - MAE `0.5593`
  - R2 `0.3944`

주의:

- 이 점수는 사용자가 마지막에 합의한 엄격한 `t -> t+1` 문제 정의와 100% 일치한다고 보기 어려움
- 다음 작업은 반드시 `입력 시각 t`, `target 시각 t+1` 재구성으로 다시 가야 함

## 현재 feature 관련 해석

- 사용자가 이해한 기준:
  - `6시까지의 정보로 7시를 예측`
- 따라서 부적합 가능성이 높은 feature:
  - `return_count_deseasonalized`
  - `bike_change_seasonal_expected`
  - 같은 row 시각 `t`에서 실제 관측되는 `rental_count`, `return_count` 계열
- 시계열 정보를 완전히 빼는 실험도 했지만, 성능이 낮아짐
- 다만 사용자가 마지막으로 확정한 요구는 “시점 정의가 정확해야 한다”는 점이라서, 성능보다 구조 정합성이 우선됨

## 다음 작업 권장 순서

1. `t 시점 row -> t+1 target` 구조의 새 데이터셋 생성
   - 예: `feature_time = 18:00`, `target_time = 19:00`
   - feature는 반드시 `18:00까지 관측 가능한 값`만 포함
2. 허용 feature / 금지 feature 명시 표 작성
   - 허용:
     - 정류소 고정 정보
     - cluster 정보
     - 외부 공간/생활인구/교통 정보
     - `t` 시점까지 확정된 값
     - 필요 시 과거 lag (`t-1`, `t-24`, `t-168`)는 허용 가능 여부를 사용자와 다시 확인
   - 금지:
     - `t+1` 시점 실측값
     - `t+1` 시점 반납/대여수
     - `t+1` 시점 타깃 직접 파생값
3. train/valid/test 재구성
   - `2023=train`, `2024=valid`, `2025=test` 유지
4. 상관계수 `0.9` 초과 feature 제거
5. R2 우선으로 모델 탐색
   - `LightGBM`, `XGBoost`, `HistGBM`, `ExtraTrees`, `RandomForest`
6. 결과 리포트 재생성

## 기타 참고

- `hmw/Data`는 정리 완료
- 100MB 넘는 파일도 대부분 `parquet`/`csv.gz`로 줄여둠
- `build_compact_bike_change_splits.py`, `build_hierarchical_compact_splits.py`는 `parquet`를 우선 읽도록 수정됨

