# 01 Analysis ML Final

이 경로는 `works/`를 다시 설명하는 폴더가 아니라, 최종적으로 이 폴더만 분리해도 입력, 출력, 핵심 문서, 정본 노트북이 모두 유지되는 `자기완결형 분석/ML 정본 패키지`를 만드는 경로다.

## 용어 정리

- `subset`(축소 피처 조합)
  - 전체 후보 피처 중 일부만 골라 만든 피처 묶음
- `objective`(학습 목표 함수)
  - 모델이 무엇을 더 잘 맞추도록 학습할지 정하는 기준
- `RMSE objective`
  - 일반 회귀형 학습 목표 함수
- `Poisson objective`
  - 수요량, 건수처럼 `0 이상 count 데이터`에 맞춘 학습 목표 함수
- `interaction`(상호작용 피처)
  - 두 조건을 곱하거나 묶어서 함께 반응을 보게 만든 피처
- `baseline`(기준선 모델)
  - 이후 개선 여부를 비교하기 위한 기본 모델

현재 목표는 명확하다.

- 정본 노트북은 `1개`
- 현재 확정된 실험 결론만 반영
- 추가 실험은 계속 `works/`에서 수행
- 여기에는 최종 전달용 요약과 핵심 산출물만 남김
- 최종적으로는 이 폴더 안의 `01_notebook`, `02_input_data`, `03_output_data`, `04_reference_docs`만으로 읽기와 실행이 가능해야 함

## 최종 기준

- 정본 노트북:
  - [01_ddri_analysis_ml_final.ipynb](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/01_notebook/01_ddri_analysis_ml_final.ipynb)
- 입력 데이터:
  - `02_input_data/`
- 출력 데이터:
  - `03_output_data/`
- 보조 근거 문서:
  - `04_reference_docs/`

## 현재 확정 결론

- `15개 대표 스테이션` 실험은 군집별 특성과 유효 피처를 찾는 탐색/해석 경로로 유지한다
- `cluster01` 최우선 권장안은 `subset_a_commute_transit + LightGBM_Poisson`이며, 이는 `출퇴근+교통` 중심의 축소 피처 조합과 `Poisson objective`를 함께 쓴 경우다
- `cluster02` 최우선 권장안은 `current_compact_best + LightGBM_Poisson`이다
- `161개 전체 운영 기준선`은 `static enriched + weather_full interaction(상호작용 피처)`이다
- `161개`에서 군집 라우팅 계열은 반복적으로 test 기준 열세였다
- 따라서 최종 전달 문서에서는 `운영 모델`과 `군집 해석 근거`를 분리해서 적는다

## 폴더 역할

### `01_notebook/`

- 최종 분석/ML 정본 노트북 1개만 두는 경로
- 군집화, 대표 15개, 전체 161개, 오류 해석, 최종 운영안을 여기서 통합

### `02_input_data/`

- 이 정본 노트북에 실제로 필요한 최소 CSV만 복사해 두는 경로
- 최종적으로는 노트북이 외부 `works/` 경로를 직접 읽지 않도록 이 폴더 안 입력만 사용한다

### `03_output_data/`

- 최종 노트북에서 내보내는 요약표, 비교표, 서비스 연결용 출력 테이블
- 최종적으로는 이 폴더 안 결과만으로 서비스 연결과 보고서 반영이 가능해야 한다

### `04_reference_docs/`

- 꼭 필요한 정본 문서만 최소한으로 다시 두는 경로
- 원본 `works/` 문서를 계속 열지 않아도 되도록 핵심 근거를 이 안으로 다시 정리한다

## 현재 패키지 포함 자산

### `02_input_data/`

- [ddri_아침_도착_업무_집중형_subset_experiment_model_metrics.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_아침_도착_업무_집중형_subset_experiment_model_metrics.csv)
- [ddri_주거_도착형_subset_recheck_model_metrics.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_주거_도착형_subset_recheck_model_metrics.csv)
- [ddri_rep15_static_weather_interaction_metrics.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_rep15_static_weather_interaction_metrics.csv)
- [ddri_full_static_enriched_model_comparison_metrics.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_full_static_enriched_model_comparison_metrics.csv)
- [ddri_full_static_weather_interaction_metrics.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_full_static_weather_interaction_metrics.csv)
- [ddri_full_exact_cluster_feature_routing_with_weather_full_metrics.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_full_exact_cluster_feature_routing_with_weather_full_metrics.csv)
- [ddri_final_district_clustering_features_train_2023_2024.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_final_district_clustering_features_train_2023_2024.csv)
- [ddri_second_cluster_summary.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_second_cluster_summary.csv)
- [ddri_second_cluster_representative_stations.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_second_cluster_representative_stations.csv)
- [ddri_second_cluster_hypothesis_crosstab.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_second_cluster_hypothesis_crosstab.csv)

### `04_reference_docs/`

- [01_ddri_master_plan.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/01_ddri_master_plan.md)
- [01_ddri_clustering_basis_summary.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/01_ddri_clustering_basis_summary.md)
- [01_ddri_clustering_basis_evidence.ipynb](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/01_ddri_clustering_basis_evidence.ipynb)
- [07_ddri_cluster_final_recommendation.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/07_ddri_cluster_final_recommendation.md)
- [12_ddri_rep15_top5_feature_linkage_summary.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/12_ddri_rep15_top5_feature_linkage_summary.md)
- [ddri_integrated_second_clustering_report.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/ddri_integrated_second_clustering_report.md)

## 다음 작업

1. 정본 노트북 골격 작성
2. 노트북에 현재 확정 결론과 비교 점수 반영
3. 이후 `works` 실험이 더 마감되면 필요한 CSV만 추가 복사
4. 필요한 핵심 문서만 더 압축해서 `04_reference_docs/`를 닫힌 형태로 정리
