# cheng80 군집별 대리 실험 트랙

목적: 대표 대여소 `15개`, `5개 군집` 기준의 `cheng80` 개인 대리 실험과 그 후속 정리 문서를 관리한다.

## 0. 용어 정리

- `subset`(축소 피처 조합)
  - 전체 후보 피처 중 일부만 골라 만든 피처 묶음
- `summary`(요약 정본)
  - 중간 문서를 줄인 뒤 핵심만 남긴 대표 요약 문서
- `archive`(보관 경로)
  - 현재 전면 정본은 아니지만 기록상 남겨 두는 경로

## 1. 먼저 볼 정본

- `07_ddri_cluster_final_recommendation.md`
  - 군집별 최종 권장 모델과 적용 수준
- `rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md`
  - 상위 오류 스테이션 해석과 축소 피처 조합(subset) 우선순위

즉 현재 이 경로의 핵심 summary(요약 정본)는 아래 두 문서로 읽으면 된다.

## 2. 보조 산출물

### 집계 CSV

- `summary_aggregation/output/data/ddri_cluster_second_round_comparison_summary.csv`
- `summary_aggregation/output/data/cluster01_third_round_progression_summary.csv`

### 오류 분석 CSV

- `rep15_error_analysis/output/data/ddri_cluster_subset_priority_table.csv`
- `rep15_error_analysis/output/data/ddri_rep15_station_error_priority_table.csv`
- `rep15_error_analysis/output/data/ddri_rep15_top5_feature_linkage_table.csv`

## 3. 보관성 실험 경로

### 군집별 실행 노트북

- `cluster00/`
- `cluster01/`
- `cluster02/`
- `cluster03/`
- `cluster04/`

### 집계 재생성 노트북

- `summary_aggregation/`

### 오류 분석 노트북

- `rep15_error_analysis/`

위 경로들은 재현성과 세부 추적을 위해 유지하지만, 현재 핵심 읽기 경로의 정본은 아니다.

## 4. 공통 기준

- 공통 규약:
  - `../05_ddri_team_cluster_modeling_protocol.md`
- 공통 템플릿:
  - `../06_ddri_cluster_modeling_template.ipynb`
- 2차 실험용 데이터:
  - `3조 공유폴더/대표대여소_예측데이터_15개/second_round_data/`

## 5. 현재 경로 해석

- 이 경로는 팀 공용 정본 경로가 아니라 `cheng80` 개인 대리 실험 트랙이다
- 중간 요약 문서는 `archive_docs/(보관 경로)`로 내리고, summary(요약 정본)는 `07`과 `rep15_error_analysis/12`로 수렴시킨다
- 군집별 개별 노트북은 보관성 자료로 남긴다
