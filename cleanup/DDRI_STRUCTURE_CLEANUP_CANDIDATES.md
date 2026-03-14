# DDRI Structure Cleanup Candidates

작성일: 2026-03-14  
기준 문서: `TODO.md`  
기준 브랜치: `cheng80`  
구조 정리 기준점: `cbada81`

## 1. 목적

`works/`와 `cheng80/` 안에 누적된 문서, 노트북, 산출물을 `앱 제작 직전 핵심 근거 자료` 중심으로 다시 묶기 위한 1차 분류표다.

이번 문서는 실제 삭제 실행 문서가 아니라, 다음 단계 정리 작업을 위한 판단 기준 문서다.
정리 작업 기간 동안만 루트 `cleanup/` 폴더에서 관리한다.

## 2. 분류 기준

### 보존

- 현재 정본이거나 최종 판단에 직접 쓰는 자료
- 앱 제작 직전에도 바로 다시 열어야 하는 자료

### 축소

- 내용은 필요하지만 문서 수가 많거나 중복 설명이 있는 자료
- 상위 정본 문서나 핵심 노트북으로 흡수 가능한 자료

### 보관

- 재현성, 추적성, 과거 비교를 위해 남길 가치는 있으나 핵심 열람선에서는 빼야 하는 자료
- 별도 `archive/` 또는 하위 보관 영역으로 이동 후보

### 삭제 후보

- 재생성 가능성이 높고, 중복이며, 최종 판단에 직접 필요하지 않은 자료
- 단, 삭제 전에는 재생성 가능 여부를 다시 확인한다

## 3. 1차 판단 요약

현재 구조 기준으로는 아래 방향이 적절하다.

- `works/00_overview/`는 별도 과밀 구간으로 취급해야 하며, `마스터 플랜 + 데이터/타깃 설계 + 서비스/API 규칙 + 점수 요약` 중심으로 압축
- `works/01_clustering/`은 현재 `08_integrated/final` 정본, `pipeline` 재생성 경로, `intermediate/archive_1st` 보관 경로 구분까지 반영된 상태다
- `works/03_prediction/`은 최종 주력 `station-hour` 정본이 아니라 `station-day` baseline/참조 경로라는 점을 고정했고, 현재는 `02_data/04_scripts` 정본과 `support_*` 보조 경로 분리까지 반영된 상태다
- `works/04_presentation/`은 발표 정본(`md + css`)과 보조 자산(`support_assets`, `support_scripts`) 분리까지 반영된 상태다
- `works/05_prediction_long/`는 대표 15개 핵심 실험 노트북과 최종 권장안만 전면에 남기고, 군집별 중간 회차 문서는 축소 또는 보관
- `works/06_prediction_long_full/`는 현재 이미 비교적 얇아서 보존 중심으로 유지
- `cheng80/` 루트는 API 검증 정본 위주로 유지하고, 대량 검증 CSV는 lookup 중심만 보존
- `works/archive_data_collection/02_data_collection/`는 최종 실행 입력 경로가 아니라 재수집/보관 경로로 유지

`cleanup/DDRI_FINAL_NOTEBOOK_INPUT_MANIFEST.md` 기준 현재 추가 판단:

- 최종 노트북 실행 입력은 이미 아래 공유폴더 정본 CSV에 수렴해 있다
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/raw_data`
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/full_data`
- 구조 정리 기준의 `1차 정본 데이터`는 아래 두 경로다
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개`
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션`
- 이 두 정본으로 실험한 작업 폴더는 아래 두 경로다
  - `/Users/cheng80/Desktop/ddri_work/works/05_prediction_long`
  - `/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full`
- 따라서 `works/05_prediction_long`과 `works/06_prediction_long_full`은 단순 작업 폴더가 아니라, 각각 `15개 대표 스테이션 정본`, `161개 전체 스테이션 정본`에 대응하는 실험 정본 경로로 봐야 한다
- 따라서 구조 정리 판단은 `수집 원천 폴더가 남아 있어야 하는가`보다 `최종 노트북이 읽는 정본 CSV가 고정돼 있는가`를 기준으로 해야 한다
- 이 기준에서는 `works/archive_data_collection/02_data_collection/`은 메인 읽기 경로가 아니라 archive로 두는 해석이 맞다

`works/00_overview/` 과밀 근거:

- 문서 수가 이미 `12개`이며 상위 기준 폴더 치고는 많다
- `02_ddri_project_report_log.md`는 약 `2581줄`로 사실상 로그 저장소 역할을 하고 있다
- `03`, `04`, `08`, `09`, `10`은 모두 예측/서비스 해석 문서인데 일부 역할이 겹친다
- `README.md`가 현재는 문서 안내보다 전체 목록 나열에 가깝다

## 4. 폴더별 분류

### A. `works/00_overview/`

현재 판단:

- 이 폴더는 `정본 5~6개 + 구조 정리 문서 2개 + 보관 문서` 수준까지 줄여야 한다
- 특히 `02`, `05`, `06`, `08`은 별도 과밀 해소 대상이다
- `README.md`는 문서 카탈로그가 아니라 `읽기 순서 안내문`으로 다시 써야 한다

보존:

- `01_ddri_master_plan.md`
- `03_ddri_prediction_target_definition.md`
- `04_ddri_prediction_dataset_design.md`
- `07_ddri_notebook_and_evidence_chart_policy.md`
- `10_ddri_model_score_summary.md`

축소:

- `02_ddri_project_report_log.md`
  - 작업 로그 전체를 유지하기보다 `마스터 플랜`에서 필요한 의사결정만 링크 또는 요약으로 흡수
- `05_ddri_workspace_structure_guide.md`
  - 정리 완료 후 새 구조 기준으로 대폭 축약 필요
- `06_ddareungi_project_inventory_2026-03-11.md`
  - 인벤토리 전체 나열 대신 핵심 경로 표만 남기는 방식으로 축소 가능
- `08_ddri_service_output_logic_draft.md`
  - 서비스 출력 로직은 API 규칙 및 핵심 예측 노트북과 합쳐 정본 1개로 묶는 편이 적절
- `README.md`
  - 문서 수가 줄어든 뒤 새 읽기 순서 기준으로 재작성 필요

보관:

- `02_ddri_project_report_log.md`
  - 축소 이후의 최종 위치는 `overview` 핵심선 밖의 보관 문서가 적절
- `06_ddareungi_project_inventory_2026-03-11.md`
  - 원문 전체는 추적용 보관본으로 둘 가치가 있다

삭제 후보:

- 현재 단계에서는 없음
  - 이 폴더 문서는 대부분 의사결정 흔적이라 삭제보다 축소가 우선

### B. `works/05_prediction_long/`

보존:

- `03_ddri_station_hour_model_comparison.ipynb`
- `04_ddri_station_hour_evidence_charts.ipynb`
- `05_ddri_team_cluster_modeling_protocol.md`
- `06_ddri_cluster_modeling_template.ipynb`
- `output/data/ddri_station_hour_model_metrics.csv`
- `output/data/ddri_station_hour_station_error_summary.csv`
- `output/data/ddri_station_hour_station_group_error_summary.csv`
- `output/data/ddri_station_hour_lightgbm_feature_importance.csv`
- `README.md`

축소:

- `01_ddri_prediction_long_dataset_builder.ipynb`
  - 핵심 노트북 수를 줄일 때는 데이터셋 생성 절차를 별도 핵심 노트북 안의 입력 설명 섹션으로 흡수하거나 보조 노트북으로만 남기는 방향 검토
- `output/images/` 전체
  - 최종 보고용 대표 차트만 남기고 나머지는 재생성 경로로 돌리는 편이 적절

보관:

- `cheng80/` 하위 전체
  - 현재는 대표 15개 심화 실험 근거가 들어 있으므로 즉시 삭제 대상은 아니지만, 최종 열람선에서는 루트 핵심 경로 밖으로 빼는 편이 맞음

### C. `works/05_prediction_long/cheng80/`

보존:

- `07_ddri_cluster_final_recommendation.md`
- `rep15_error_analysis/08_ddri_rep15_station_error_priority_summary.md`
- `rep15_error_analysis/11_ddri_rep15_top5_station_hourly_error_summary.md`
- `rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md`
- `rep15_error_analysis/output/data/ddri_cluster_subset_priority_table.csv`
- `rep15_error_analysis/output/data/ddri_rep15_station_error_priority_table.csv`
- `rep15_error_analysis/output/data/ddri_rep15_top5_feature_linkage_table.csv`
- `summary_aggregation/output/data/ddri_cluster_second_round_comparison_summary.csv`
- `summary_aggregation/output/data/cluster01_third_round_progression_summary.csv`

축소:

- `README.md`
  - 최종 정리 후에는 `최종 권장안`, `오류 분석`, `보관 실험` 세 축만 소개하도록 축소
- `01_ddri_cluster_result_collection.md`
- `02_ddri_second_round_experiment_criteria.md`
- `03_ddri_cluster_feature_candidate_recommendations.md`
- `04_ddri_second_round_result_summary.md`
- `05_ddri_cluster01_third_round_summary.md`
- `06_ddri_cluster_experiment_overall_summary.md`
  - 위 6개는 현재 흐름을 설명하는 중간 요약 문서다. 핵심 결론은 `07_ddri_cluster_final_recommendation.md`와 오류 분석 정본으로 흡수 가능

보관:

- `cluster00/01_cluster_modeling.ipynb`
- `cluster00/02_cluster_modeling_second_round.ipynb`
- `cluster01/01_cluster_modeling.ipynb`
- `cluster01/02_cluster_modeling_second_round.ipynb`
- `cluster01/03_cluster_modeling_third_round.ipynb`
- `cluster02/01_cluster_modeling.ipynb`
- `cluster02/02_cluster_modeling_second_round.ipynb`
- `cluster03/01_cluster_modeling.ipynb`
- `cluster03/02_cluster_modeling_second_round.ipynb`
- `cluster04/01_cluster_modeling.ipynb`
- `cluster04/02_cluster_modeling_second_round.ipynb`
- `summary_aggregation/11_ddri_cluster_result_collection.ipynb`
- `summary_aggregation/12_ddri_cluster_second_round_comparison.ipynb`
- `summary_aggregation/13_ddri_cluster01_third_round_progression.ipynb`
- `rep15_error_analysis/10_ddri_rep15_station_error_analysis.ipynb`
- `rep15_error_analysis/11_ddri_rep15_top5_station_error_analysis.ipynb`
- `rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_and_subset_priority.ipynb`
- `rep15_error_analysis/output/data/`의 중간 분석 CSV 다수
  - 재현성과 세부 추적은 중요하지만, 최종 읽기 경로의 핵심본으로 두기에는 양이 많다

삭제 후보:

- `rep15_error_analysis/09_ddri_rep15_top2_station_hourly_error_summary.md`
  - top5 확장 정리 이후 우선순위가 낮아진 중간 단계 문서
- `rep15_error_analysis/output/data/ddri_rep15_top2_station_error_summary.csv`
- `rep15_error_analysis/output/data/ddri_rep15_top2_station_hourly_error_patterns.csv`
- `rep15_error_analysis/output/data/ddri_rep15_top2_station_peak_error_hours.csv`
  - top5 기준 정본이 확정되면 중복 가능성이 높음

### D. `works/06_prediction_long_full/`

보존:

- `01_ddri_station_hour_full_baseline.ipynb`
- `02_ddri_station_hour_full_model_comparison.ipynb`
- `README.md`
- `output/data/ddri_station_hour_full_model_metrics.csv`
- `output/data/ddri_station_hour_full_model_comparison_metrics.csv`
- `output/data/ddri_station_hour_full_station_error_summary.csv`
- `output/data/ddri_station_hour_full_lightgbm_feature_importance.csv`
- `output/data/ddri_full_top20_error_rep15_overlap.csv`

축소:

- `output/images/`
  - 핵심 비교 이미지 1~2장만 남기고 나머지는 재생성 가능 산출물로 돌리는 방안 검토
- `output/data/ddri_station_hour_full_model_comparison_lightgbm_feature_importance.csv`
  - 일반 importance와 역할이 중복되는지 확인 후 정리 가능

삭제 후보:

- 현재 단계에서는 없음
  - 이 폴더는 이미 핵심 산출물 위주라 우선 삭제보다 유지가 맞다

### E. `works/04_presentation/`

보존:

- 실제 최종 발표에 다시 쓸 문서만 남기는 방향
- 현 시점 기준 잠정 보존 후보:
  - `01_clustering/01_ddri_clustering_presentation_a4_landscape.md`
  - `01_clustering/02_ddri_clustering_speaker_notes_detailed.md`
  - `ddri_presentation_a4_landscape.css`

보관:

- `01_clustering/support_assets/`
  - PDF, 지도 캡처, 지도 PNG 같은 보조 발표 자산
- `support_scripts/`
  - 보조 자산 재생성 스크립트

삭제 후보:

- 최종 발표본 확정 후 중복 PDF 또는 중복 캡처본
- 현재는 보수적으로 보관 우선

### F. `works/archive_data_collection/`

현재 판단:

- 이 경로는 이미 학습용 정본 CSV 생성에 반영된 외부 데이터 수집 보관 영역이다
- 메인 README 흐름에서는 전면 노출하지 않고, 재수집이 필요할 때만 여는 archive 경로로 유지한다

보관:

- `archive_data_collection/02_data_collection/` 전체
  - `01_calendar/`
  - `02_weather/`
  - 수집 노트북, 수집 스크립트, 생성 CSV

삭제 후보:

- 현재 단계에서는 없음
  - 재수집 근거와 원시 생성 절차를 남겨 두는 편이 안전하다

### G. `works/01_clustering/`

보존:

- `08_integrated/final/`
- `08_integrated/pipeline/04_ddri_final_district_clustering_feature_builder.ipynb`
- `08_integrated/pipeline/12_ddri_integrated_clustering_report_builder.ipynb`
- `08_integrated/source_data/ddri_common_station_master.csv`
- `README.md`

보관:

- `08_integrated/intermediate/` 전체
- `08_integrated/final/results/second_clustering_results/support_assets/`
- `archive_1st/` 전체
  - 최종 군집 정본은 아니지만, 군집 근거 추적과 비교에는 필요

삭제 후보:

- 현재 단계에서는 없음

후속 정리 메모:

- `pipeline/` 안 노트북/스크립트 중 무엇이 실제 정본 재생성 기준인지 다시 나눌 필요가 있다
- `intermediate/`는 세부 목적별로 archive성 하위 구분을 더 줄 수 있다
- `archive_1st/`는 유지하되 README 수준에서 전면 노출을 더 낮출 수 있다

### `works/03_prediction/`

현재 판단:

- `station-day` baseline 정본 경로로 유지하되, 현재는 `02_data/04_scripts` 정본과 `support_data/support_images/support_scripts` 보조 경로를 분리한 상태다

후속 정리 메모:

- `02_data/` 안에서 직접 참조하는 정본 CSV는 이미 좁혀졌고, 남은 보조 산출물은 `support_*` 경로 기준으로 읽는다
- 이후에는 `support_*`까지 더 줄일지 여부만 보면 된다

### `works/04_presentation/`

현재 판단:

- 현재는 군집화 발표 정본과 보조 자산 분리가 반영된 상태다

후속 정리 메모:

- 현재 기준 정본은 markdown과 css이며, PDF와 지도 자산은 `support_assets/`로 본다
- 차후 실제 최종 발표본이 새로 만들어지면 그때 다시 정본 교체 여부를 판단한다

### H. `cheng80/` 루트

보존:

- `01_ddri_api_verification.ipynb`
- `02_ddri_api_operational_rules.md`
- `api_output/ddri_full161_station_api_mapping_table.csv`
- `api_output/ddri_station_id_api_lookup.csv`

축소:

- `api_output/ddri_api_summary_revalidation_checklist.csv`
  - 정본 문서에 재검증 체크 항목만 흡수 가능
- `api_output/ddri_api_key_compatibility_check.csv`
  - 1차 점검 흔적 성격이 강해 요약만 남기는 방향 가능

보관:

- `api_output/ddri_full161_station_api_validation_official.csv`
- `api_output/ddri_rep15_station_api_validation_official.csv`
- `api_output/ddri_rep15_station_api_validation.csv`
- `api_output/ddri_unmatched_station_master_crosscheck.csv`
- `api_output/ddri_service_realtime_join_preview.csv`
- `api_output/ddri_bikeseoul_realtime_sample.csv`
- `api_output/ddri_seoul_bike_page_summary.csv`
- `api_output/ddri_seoul_bike_realtime_all_pages.csv`
- `api_output/ddri_seoul_bike_stationid_filter_tests.csv`
  - 검증 근거는 있으나 서비스 직전 참조 빈도는 낮다

삭제 후보:

- 현재 단계에서는 없음
  - API 검증은 재수집 가능해도 외부 상태 변동이 있으므로 섣불리 삭제하지 않는다

## 5. 현 시점 핵심 노트북 후보

현재 2~3개 구조로 압축할 때의 1차 후보는 아래와 같다.

1. `works/05_prediction_long/03_ddri_station_hour_model_comparison.ipynb`
   - 대표 15개 baseline과 모델 선택 근거
2. `works/06_prediction_long_full/02_ddri_station_hour_full_model_comparison.ipynb`
   - 전체 161개 baseline과 서비스 확장 기준선
3. `cheng80/01_ddri_api_verification.ipynb`
   - 실시간 API 매핑, 예외 규칙, 서비스 연결 근거

보조 정본 문서 후보:

- `works/05_prediction_long/cheng80/07_ddri_cluster_final_recommendation.md`
- `works/05_prediction_long/cheng80/rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md`
- `cheng80/02_ddri_api_operational_rules.md`

## 6. 다음 작업

다음 단계에서는 아래를 이어서 수행한다.

1. 위 분류표를 기준으로 `정본 문서 목록`을 확정한다
2. `축소` 대상 문서 중 어떤 내용을 어디 정본으로 흡수할지 매핑한다
3. `보관` 대상 폴더의 실제 이동 경로를 설계한다
4. 최종적으로 `핵심 노트북 2~3개 + 정본 문서 3~5개` 구조로 상위 README를 재작성한다
