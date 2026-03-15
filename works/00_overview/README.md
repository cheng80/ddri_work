# 00 Overview

이 폴더는 프로젝트 전체 기준 문서를 모으는 위치다.

현재는 문서가 과밀해져 있어, 모든 문서를 같은 비중으로 읽으면 오히려 흐름이 흐려진다.

## 용어 정리

- `target`(예측 목표값)
  - 모델이 직접 맞추려는 값
- `grain`(데이터 단위)
  - 한 행이 무엇을 의미하는지 정하는 기준
  - 예: `station-day`는 대여소-하루 1행, `station-hour`는 대여소-시간 1행
- `feature`(입력 변수)
  - 모델이 예측에 참고하는 입력 컬럼
- `baseline`(기준선 모델)
  - 이후 개선 여부를 비교하기 위한 기본 모델
- `lag`(과거 시점 값)
  - 직전 1시간, 24시간 전, 1주 전처럼 과거 같은 대상의 값을 가져온 피처
- `rolling`(이동 통계)
  - 최근 6시간, 24시간처럼 일정 구간의 평균이나 표준편차를 계산한 피처

우선은 아래 `핵심 정본`만 따라가면 된다.

1. `01_ddri_master_plan.md`
2. `03_ddri_prediction_target_definition.md`
3. `04_ddri_prediction_dataset_design.md`
4. `07_ddri_notebook_and_evidence_chart_policy.md`
5. `10_ddri_model_score_summary.md`

직접 열람 링크:

- [01_ddri_master_plan.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/01_ddri_master_plan.md)
- [03_ddri_prediction_target_definition.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/03_ddri_prediction_target_definition.md)
- [04_ddri_prediction_dataset_design.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/04_ddri_prediction_dataset_design.md)
- [07_ddri_notebook_and_evidence_chart_policy.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/07_ddri_notebook_and_evidence_chart_policy.md)
- [10_ddri_model_score_summary.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/10_ddri_model_score_summary.md)

## 읽기 순서

1. 전체 상태와 단계: `01_ddri_master_plan.md`
2. 예측 타깃과 데이터 단위: `03_ddri_prediction_target_definition.md`
3. 데이터 결합 구조: `04_ddri_prediction_dataset_design.md`
4. 노트북/차트 운영 기준: `07_ddri_notebook_and_evidence_chart_policy.md`
5. 현재 점수 요약: `10_ddri_model_score_summary.md`

## 정리 작업 문서

현재 구조 정리 기간 동안의 점검 문서는 루트 `cleanup/` 폴더에서 별도로 관리한다.

- [DDRI_STRUCTURE_CLEANUP_CANDIDATES.md](/Users/cheng80/Desktop/ddri_work/cleanup/DDRI_STRUCTURE_CLEANUP_CANDIDATES.md)
- [DDRI_STRUCTURE_REDUCTION_MAPPING.md](/Users/cheng80/Desktop/ddri_work/cleanup/DDRI_STRUCTURE_REDUCTION_MAPPING.md)

## 축소 또는 보관 예정 문서

- [archive_docs/02_ddri_project_report_log.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/02_ddri_project_report_log.md)
- [archive_docs/05_ddri_workspace_structure_guide.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/05_ddri_workspace_structure_guide.md)
- [archive_docs/06_ddareungi_project_inventory_2026-03-11.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/06_ddareungi_project_inventory_2026-03-11.md)
- [archive_docs/08_ddri_service_output_logic_draft.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/08_ddri_service_output_logic_draft.md)
- [archive_docs/09_ddri_cluster_specific_modeling_strategy.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/archive_docs/09_ddri_cluster_specific_modeling_strategy.md)

위 문서들은 당장 삭제 대상은 아니지만, `overview` 핵심 읽기 경로에서는 단계적으로 뒤로 뺄 예정이다.
