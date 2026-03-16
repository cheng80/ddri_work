# 00 Overview

이 폴더는 현재 프로젝트 기준 문서를 모으는 위치다.

지금은 예전 예측 실험 경로를 대거 정리한 상태라, 문서를 읽을 때도 "현재 기준"과 "과거 기록"을 분리해서 보는 것이 중요하다.

## 현재 기준

- 원천 입력 데이터는 공유폴더의 `raw_data`, `full_data`를 기준으로 본다.
- 기존 `station-hour` 예측 실험 폴더 `05_prediction_long`, `06_prediction_long_full`은 폐기되었다.
- 기존 `station-day` baseline 경로 `03_prediction`과 데이터 수집 경로 `02_data_collection`은 [archive_legacy](/Users/cheng80/Desktop/ddri_work/works/archive_legacy)로 이동했다.
- 현재 `works/`에서 실질적으로 살아 있는 축은 `01_clustering`, `04_presentation`, 그리고 본 `00_overview`다.

## 핵심 문서

지금 시점에서 먼저 읽을 문서는 아래 4개다.

1. [01_ddri_master_plan.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/01_ddri_master_plan.md)
2. [03_ddri_prediction_target_definition.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/03_ddri_prediction_target_definition.md)
3. [04_ddri_prediction_dataset_design.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/04_ddri_prediction_dataset_design.md)
4. [07_ddri_notebook_and_evidence_chart_policy.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/07_ddri_notebook_and_evidence_chart_policy.md)

`10_ddri_model_score_summary.md`는 과거 실험 점수 요약 성격이 강하므로, 현재 정본 재구축 단계에서는 참고 문서로만 읽는 편이 맞다.

## 읽기 순서

1. 전체 상태와 재정리 방향: [01_ddri_master_plan.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/01_ddri_master_plan.md)
2. 예측 타깃과 데이터 단위 정의: [03_ddri_prediction_target_definition.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/03_ddri_prediction_target_definition.md)
3. 데이터 결합 구조와 정본 범위: [04_ddri_prediction_dataset_design.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/04_ddri_prediction_dataset_design.md)
4. 새 노트북/근거 차트 기록 원칙: [07_ddri_notebook_and_evidence_chart_policy.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/07_ddri_notebook_and_evidence_chart_policy.md)
5. 과거 점수표 확인이 필요할 때만: [10_ddri_model_score_summary.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/10_ddri_model_score_summary.md)

## 용어 정리

- `target`: 모델이 직접 예측하는 값
- `grain`: 한 행의 단위
- `baseline`: 비교 기준 모델
- `lag`: 과거 시점 값
- `rolling`: 이동 평균, 이동 표준편차 같은 구간 통계

## 보관 문서

아래 문서는 현재 기준 문서가 아니라 과거 기록 보관용이다.

- [archive_docs/02_ddri_project_report_log.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/02_ddri_project_report_log.md)
- [archive_docs/05_ddri_workspace_structure_guide.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/05_ddri_workspace_structure_guide.md)
- [archive_docs/06_ddareungi_project_inventory_2026-03-11.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/06_ddareungi_project_inventory_2026-03-11.md)
- [archive_docs/08_ddri_service_output_logic_draft.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/08_ddri_service_output_logic_draft.md)
- [archive_docs/09_ddri_cluster_specific_modeling_strategy.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/09_ddri_cluster_specific_modeling_strategy.md)
