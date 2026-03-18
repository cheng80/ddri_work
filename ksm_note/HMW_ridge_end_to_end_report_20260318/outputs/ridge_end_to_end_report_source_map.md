# Ridge End-to-End Report Source Map

작성일: 2026-03-18

## 1. 최종 보고서 파일

- 대상 보고서: `ksm_note/HMW_ridge_end_to_end_report_20260318/outputs/ridge_end_to_end_report.md`
- 직접 생성 스크립트: `ksm_note/HMW_ridge_end_to_end_report_20260318/build_ridge_end_to_end_report.py`

이 스크립트는 Markdown 보고서를 직접 조합해서 저장한다.
문서 본문 대부분은 스크립트 내부의 한국어 문장 템플릿에서 생성되고,
표 일부는 CSV를 읽어 `to_markdown()`으로 삽입되며,
이미지 일부는 이 스크립트가 새로 그리고,
이미지 일부는 다른 분석 스크립트 산출물을 참조한다.

## 2. 직접 입력 소스

`build_ridge_end_to_end_report.py`의 `load_inputs()` 기준 직접 입력은 아래와 같다.

### 2-1. 핵심 데이터셋

- `ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
- `ksm_note/data/ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`

현재 워크트리에는 `ksm_note/data/` 디렉터리가 없고, 동일 파일명 데이터는 아래 위치에서 확인됐다.

- `3조 공유폴더/ksm_note_large_files_20260318/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
- `3조 공유폴더/ksm_note_large_files_20260318/data/ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`
- `3조 공유폴더/ksm_note_large_files_20260318/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3.csv`

즉 현재 보고서 재생성 시에는 `ksm_note/data` 대신 위 공유폴더 데이터를 연결하거나 복사해야 할 가능성이 높다.

### 2-2. 선형 회귀 계수/성능 소스

- 입력 파일:
  - `ksm_note/HMW_linear_regression_coefficients_20260318/outputs/linear_regression_scores.csv`
  - `ksm_note/HMW_linear_regression_coefficients_20260318/outputs/linear_regression_coefficients.csv`
- 생성 스크립트:
  - `ksm_note/HMW_linear_regression_coefficients_20260318/run_linear_regression_coefficients.py`
- 이 스크립트의 입력:
  - train: `ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
  - test: `ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`

### 2-3. 월 유사도 / sample_weight 소스

- 입력 파일:
  - `ksm_note/feature_weight/outputs/overall_month_weight_suggestions.csv`
  - `ksm_note/feature_weight/outputs/feature_adjacent_month_similarity.csv`
  - `ksm_note/feature_weight/outputs/feature_hourly_profiles_by_year_month.csv`
- 생성 스크립트:
  - `ksm_note/feature_weight/run_feature_monthly_similarity_weights.py`
- 이 스크립트의 입력:
  - `ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3.csv`

즉 `sample_weight` 관련 근거는 `with_sample_weight` 파일이 아니라,
먼저 `v3` train 데이터에서 월 유사도 분석을 수행한 뒤,
그 결과를 기반으로 `overall_month_weight_suggestions.csv`를 만들고,
그 가중치가 다시 `with_sample_weight` 데이터셋에 반영된 흐름으로 보는 것이 자연스럽다.

### 2-4. 누수 / 분할 점검 소스

- 입력 파일:
  - `ksm_note/lightgbm_reason/outputs/target_like_feature_audit.csv`
  - `ksm_note/lightgbm_reason/outputs/future_information_audit.csv`
  - `ksm_note/lightgbm_reason/outputs/split_date_ranges.csv`
  - `ksm_note/lightgbm_reason/outputs/split_key_overlap_audit.csv`
- 추가 이미지 참조:
  - `ksm_note/lightgbm_reason/outputs/target_like_feature_correlation.png`
  - `ksm_note/lightgbm_reason/outputs/repeated_pattern_similarity_counts.png`
- 생성 스크립트:
  - `ksm_note/lightgbm_reason/run_leakage_split_similarity_audit.py`
- 이 스크립트의 입력:
  - train: `ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
  - test: `ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`

### 2-5. LightGBM 비교 소스

- 입력 파일:
  - `ksm_note/lightgbm_reason_1/outputs/lightgbm_without_history_comparison.csv`
- 참조 보고서:
  - `ksm_note/lightgbm_reason_1/outputs/lightgbm_without_history_report.md`
- 생성 스크립트:
  - `ksm_note/lightgbm_reason_1/run_lightgbm_without_bikechange_history.py`
- 이 스크립트의 입력:
  - train: `ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
  - test: `ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`

### 2-6. 클러스터별 Ridge 소스

- 입력 파일:
  - `ksm_note/HMW_cluster_ridge_regression_20260318/outputs/cluster_ridge_scores.csv`
- 추가 이미지 참조:
  - `ksm_note/HMW_cluster_ridge_regression_20260318/outputs/cluster_r2_by_split.png`
  - `ksm_note/HMW_cluster_ridge_regression_20260318/outputs/cluster_rmse_by_split.png`
- 생성 스크립트:
  - `ksm_note/HMW_cluster_ridge_regression_20260318/run_cluster_ridge_regression.py`
- 이 스크립트의 입력:
  - train: `ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
  - test: `ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`

### 2-7. 공선성 / 상관계수 소스

- 입력 파일:
  - `ksm_note/feature_hitmap/outputs/high_correlation_pairs_over_0_7.csv`
- 생성 노트북:
  - `ksm_note/feature_hitmap/feature_correlation_analysis.ipynb`
- 노트북 내부 입력:
  - `ksm_note/data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v2.csv`

주의:
- 노트북은 `v2` 데이터를 읽고 있다.
- 반면 최종 end-to-end 보고서는 `v3` 데이터 구조를 기준으로 설명한다.
- 따라서 공선성 섹션 일부는 엄밀히 말하면 `v2` 기반 상관분석 산출물을 차용했을 가능성이 있다.

## 3. 보고서 본문이 어디서 왔는가

### 3-1. 스크립트 내부에서 직접 서술되는 부분

다음 섹션의 핵심 문장은 `build_ridge_end_to_end_report.py` 안에 하드코딩되어 있다.

- 제목
- 분석 목적
- 공선성 정리 설명문
- 누수 점검 설명문
- sample_weight 설계 설명문
- Ridge 성능 해석
- LightGBM 해석
- 결론

즉 이 부분은 어떤 외부 Markdown을 합치는 방식이 아니라, 스크립트 텍스트 자체가 원본이다.

### 3-2. 외부 CSV를 표로 주입하는 부분

다음 내용은 외부 산출 CSV를 읽어 표로 삽입된다.

- 선형 회귀 성능표
- 회귀 계수 상위표
- 월별 유사월/가중치 표
- target-like audit 표
- future information audit 표
- split 범위 및 overlap 표
- LightGBM 비교표
- cluster별 Ridge 점수표
- high correlation pair 표

### 3-3. 스크립트가 직접 새로 그리는 이미지

`build_ridge_end_to_end_report.py`가 스스로 만드는 이미지:

- `analysis_process_flow.png`
- `feature_count_summary.png`
- `split_row_counts.png`
- `ridge_scores.png`
- `top_standardized_coefficients.png`
- `overall_month_weights.png`
- `current_feature_correlation_heatmap.png`
- `weekday_profile_compare_rental_count.png`
- `hourly_profile_compare_rental_count.png`

### 3-4. 외부 산출물을 그대로 참조하는 이미지

- `lightgbm_reason/outputs/target_like_feature_correlation.png`
- `lightgbm_reason/outputs/repeated_pattern_similarity_counts.png`
- `HMW_cluster_ridge_regression_20260318/outputs/cluster_r2_by_split.png`
- `HMW_cluster_ridge_regression_20260318/outputs/cluster_rmse_by_split.png`
- `feature_hitmap/outputs/high_correlation_pairs_over_0_7.csv`는 직접 읽고,
  그 시각화 이미지는 최종 스크립트 안에서 다시 그린다.

## 4. 실제 생성 흐름 추정

보고서 생성 흐름은 대략 아래 순서로 정리된다.

1. `v3` train/test canonical 데이터 준비
2. `feature_weight/run_feature_monthly_similarity_weights.py` 실행
3. sample_weight를 train 데이터에 반영한 `...with_sample_weight.csv` 준비
4. `HMW_linear_regression_coefficients_20260318/run_linear_regression_coefficients.py` 실행
5. `lightgbm_reason/run_leakage_split_similarity_audit.py` 실행
6. `lightgbm_reason_1/run_lightgbm_without_bikechange_history.py` 실행
7. `HMW_cluster_ridge_regression_20260318/run_cluster_ridge_regression.py` 실행
8. `feature_hitmap/feature_correlation_analysis.ipynb` 또는 동등한 상관분석 산출물 준비
9. 마지막으로 `HMW_ridge_end_to_end_report_20260318/build_ridge_end_to_end_report.py` 실행

## 5. 새 문서 작성 시 주의점

새 문서를 만들 때는 아래를 먼저 결정해야 한다.

### 선택 1. 설명문 원본

- 현재 end-to-end 보고서의 설명 문구를 그대로 재사용할지
- 아니면 각 하위 보고서의 문구를 다시 조합할지

현재 구조상 가장 강한 원문 소스는 `build_ridge_end_to_end_report.py` 내부 문자열이다.

### 선택 2. 표/그림 값의 기준 버전

- `v2` 기반 공선성 산출물을 유지할지
- `v3` 기준으로 상관분석을 다시 돌릴지

특히 공선성/상관계수 파트는 버전 혼용 가능성이 있으므로, 새 문서에서는 기준 버전을 통일하는 편이 안전하다.

### 선택 3. 실제 데이터 경로

- 스크립트는 `ksm_note/data`를 기대하지만 현재 저장소에는 없다.
- 재생성이 필요하면 `3조 공유폴더/ksm_note_large_files_20260318/data/`를 기준으로 경로를 다시 연결해야 한다.

## 6. 현재 결론

이 보고서는 단일 원본 파일에서 온 것이 아니라 아래 세 층이 합쳐진 결과물이다.

- 1층: `build_ridge_end_to_end_report.py` 내부 설명문 템플릿
- 2층: `ksm_note` 하위 분석 스크립트들이 만든 CSV / MD / PNG 산출물
- 3층: 최상위 canonical train/test CSV 데이터

따라서 새 혼합 문서를 만들려면 최소한 아래를 원본 세트로 잡아야 한다.

- `build_ridge_end_to_end_report.py`
- `HMW_linear_regression_coefficients_20260318/outputs/*`
- `feature_weight/outputs/*`
- `lightgbm_reason/outputs/*`
- `lightgbm_reason_1/outputs/*`
- `HMW_cluster_ridge_regression_20260318/outputs/*`
- `feature_hitmap/outputs/*`
- 공유폴더의 canonical train/test CSV
