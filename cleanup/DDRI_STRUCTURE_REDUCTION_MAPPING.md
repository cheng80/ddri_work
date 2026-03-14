# DDRI Structure Reduction Mapping

작성일: 2026-03-14  
기준 문서: `TODO.md`  
관련 문서: `cleanup/DDRI_STRUCTURE_CLEANUP_CANDIDATES.md`

## 1. 목적

`축소` 대상으로 분류한 문서와 산출물을 어떤 `정본`으로 흡수할지 정리한 실행용 매핑표다.

이 문서는 실제 삭제나 이동 전에 아래를 고정하기 위한 것이다.

- 어떤 문서를 정본으로 삼을지
- 중간 문서에서 무엇만 남길지
- 어떤 문서는 링크만 남기고 본문은 줄일지

## 2. 정본 세트 초안

현재 구조 정리 기준의 핵심 정본 세트는 아래처럼 잡는다.

중요:

- `works/00_overview/`는 단순 보조 폴더가 아니라 `과밀 해소 우선 대상`이다
- 최종적으로는 `정본 5~6개 + 구조 정리 문서 2개 + 보관 문서` 정도까지 줄이는 것을 목표로 한다

### 상위 기준 문서

- `works/00_overview/01_ddri_master_plan.md`
- `works/00_overview/03_ddri_prediction_target_definition.md`
- `works/00_overview/04_ddri_prediction_dataset_design.md`
- `works/00_overview/07_ddri_notebook_and_evidence_chart_policy.md`
- `works/00_overview/10_ddri_model_score_summary.md`
- `cleanup/DDRI_STRUCTURE_CLEANUP_CANDIDATES.md`
- `cleanup/DDRI_STRUCTURE_REDUCTION_MAPPING.md`

### 예측/서비스 정본

- `works/05_prediction_long/03_ddri_station_hour_model_comparison.ipynb`
- `works/05_prediction_long/04_ddri_station_hour_evidence_charts.ipynb`
- `works/05_prediction_long/cheng80/07_ddri_cluster_final_recommendation.md`
- `works/05_prediction_long/cheng80/rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md`
- `works/06_prediction_long_full/02_ddri_station_hour_full_model_comparison.ipynb`
- `cheng80/01_ddri_api_verification.ipynb`
- `cheng80/02_ddri_api_operational_rules.md`

## 3. 축소 대상 매핑

### A. `works/00_overview/`

| 축소 대상 | 흡수 대상 정본 | 남길 최소 내용 | 처리 방향 |
|---|---|---|---|
| `02_ddri_project_report_log.md` | `01_ddri_master_plan.md` | 날짜별 의사결정 중 현재 구조, 실험 경로, 서비스 연결 판단만 남김 | 상세 로그는 보관, 정본에는 결정사항만 반영 |
| `05_ddri_workspace_structure_guide.md` | `works/README.md`, `works/00_overview/README.md`, `cleanup/DDRI_STRUCTURE_CLEANUP_CANDIDATES.md` | 새 폴더 읽기 순서, 핵심 경로, archive 원칙 | 기존 장문 설명은 축약 |
| `06_ddareungi_project_inventory_2026-03-11.md` | `01_ddri_master_plan.md`, `works/README.md` | 실제 계속 쓰는 데이터/문서 경로만 표로 유지 | 전체 나열식 인벤토리는 보관 후보 |
| `08_ddri_service_output_logic_draft.md` | `cheng80/02_ddri_api_operational_rules.md`, `01_ddri_master_plan.md` | `predicted_remaining_bikes`, `risk_score`, 예외 스테이션 규칙, 입력 스키마 초안 | 서비스 후처리 정본으로 재편 필요 |
| `works/00_overview/README.md` | 자체 재작성 | 읽기 순서와 정본 링크만 남김 | 문서 목록형 README로 재작성 |

`02_ddri_project_report_log.md` 세부 처리 기준:

- `유지 후 흡수` 대상
  - `Decision 0XY` 실시간 API 기준 및 161개 매핑 규칙
  - `Decision 0XX` 군집별 최종 권장안 해석
  - `Decision 017` 통합 군집화 결과 정리 방식
  - `Decision 018` 통합 군집화 메인 `k=5`
  - `Decision 020` `08_integrated` 구조 재정리
  - `Decision 022` `station-day` baseline 비교 기준
  - `Decision 023` 대표 15개 `station-hour` 모델 비교 기준
  - `Decision 024` 전체 161개 `station-hour` 실험 분리
  - `Decision 026` 전체 161개 기본 모델은 `LightGBM_RMSE_Full`
  - `Decision 027` 대표 15개 단계의 역할은 탐색/설명 단계
  - `Decision 031` `works/05_prediction_long` 원본과 산출물 분리
  - `Decision 032` `works/06_prediction_long_full`는 `output/` 중심 관리
  - `Decision 033` 용어 표기 `한글(영문)` 통일
  - `Decision 034` 모델 점수 요약 문서 분리
  - `Decision 035`, `036` 팀 공통 프로토콜/템플릿 고정
  - `Decision 037` 2024 날씨 정정 및 재생성
  - `Decision 038`~`043` `cheng80` 대리 실험 트랙과 2차/3차 실험 누적 판단

- `정본에 이미 반영되었고 원문 보관만 하면 되는 대상`
  - `Decision 009`, `010`
  - `Decision 014`, `015`
  - 위 항목들은 각각 `03_ddri_prediction_target_definition.md`, `04_ddri_prediction_dataset_design.md`, `01_ddri_master_plan.md` 쪽에 이미 흡수되어 있다

- `구버전 또는 보관 전용 대상`
  - `Decision 001`~`008-2`
  - 초기 1차 군집화 baseline과 `k=2` 판단 중심이라 현재 최종 정본 흐름에서는 전면 노출 대상이 아니다
  - 추적 필요 시 `works/01_clustering/archive_1st/`와 함께 보관한다
  - `Decision 012`
  - `2025` 날씨 부재로 테스트셋 생성을 보류했던 과거 상태라 `Decision 013`, `037` 이후 기준으로는 종료된 이슈다
  - `Decision 019`, `021`
  - 환경 보강/POI 비채택 과정 추적용 가치가 있으므로 보관은 하되 정본 본문 흡수 우선순위는 낮다
  - `Decision 029`, `030`
  - 이미 수행된 폴더 정리 이력이라 현재는 로그 보관 성격이 강하다

`02_ddri_project_report_log.md` 축소 실행 순서:

1. 현재 유효한 결정만 `01_ddri_master_plan.md`에 1차 요약 반영
2. `report_log` 상단에는 `현재 유효한 핵심 결정 링크`만 남기고 원문 결정 로그는 뒤로 보낸다
3. 최종적으로는 `cleanup` 또는 별도 `archive docs` 경로로 이동 여부를 다시 판단한다

`works/00_overview/` 최종 목표 형태:

- `01_ddri_master_plan.md`
- `03_ddri_prediction_target_definition.md`
- `04_ddri_prediction_dataset_design.md`
- `07_ddri_notebook_and_evidence_chart_policy.md`
- `10_ddri_model_score_summary.md`
- `cheng80/02_ddri_api_operational_rules.md` 또는 서비스 후처리 정본 링크
- `cleanup/DDRI_STRUCTURE_CLEANUP_CANDIDATES.md`
- `cleanup/DDRI_STRUCTURE_REDUCTION_MAPPING.md`

`overview`에서 전면 노출을 줄일 후보:

- `02_ddri_project_report_log.md`
- `05_ddri_workspace_structure_guide.md`
- `06_ddareungi_project_inventory_2026-03-11.md`
- `08_ddri_service_output_logic_draft.md`
- `09_ddri_cluster_specific_modeling_strategy.md`

위 5개 중 `09`는 완전 제거 대상은 아니지만, 장기적으로는 `master_plan`이나 대표 예측 정본 노트북과의 역할 중복 여부를 다시 점검해야 한다.

### B. `works/05_prediction_long/cheng80/` 루트 요약 문서

| 축소 대상 | 흡수 대상 정본 | 남길 최소 내용 | 처리 방향 |
|---|---|---|---|
| `01_ddri_cluster_result_collection.md` | `07_ddri_cluster_final_recommendation.md` | 1차 baseline 기준 군집별 초기 성능표 | 요약 표만 남기고 세부 과정 제거 |
| `02_ddri_second_round_experiment_criteria.md` | `07_ddri_cluster_final_recommendation.md` | 2차 실험 판단 기준 3~5개 bullet | 권장안 문서의 판단 기준 섹션으로 흡수 |
| `03_ddri_cluster_feature_candidate_recommendations.md` | `07_ddri_cluster_final_recommendation.md`, `12_ddri_rep15_top5_feature_linkage_summary.md` | 군집별 추천 피처 묶음 | 후보 전체 설명 대신 최종 채택 피처만 유지 |
| `04_ddri_second_round_result_summary.md` | `07_ddri_cluster_final_recommendation.md` | 2차 실험 개선폭 요약 | 1차 대비 개선표만 남김 |
| `05_ddri_cluster01_third_round_summary.md` | `07_ddri_cluster_final_recommendation.md` | `cluster01` 3차 개선 근거 | 최종 권장안의 `cluster01` 상세 근거로 흡수 |
| `06_ddri_cluster_experiment_overall_summary.md` | `07_ddri_cluster_final_recommendation.md`, `10_ddri_model_score_summary.md` | 군집별 적용 수준 해석 | 전반 결론은 두 정본에 분산 흡수 |
| `works/05_prediction_long/cheng80/README.md` | 자체 재작성 | `최종 권장안`, `오류 분석`, `archive 실험` 3개 링크만 유지 | 길게 설명하지 않음 |

### C. `works/05_prediction_long/cheng80/rep15_error_analysis/`

| 축소 대상 | 흡수 대상 정본 | 남길 최소 내용 | 처리 방향 |
|---|---|---|---|
| `08_ddri_rep15_station_error_priority_summary.md` | `12_ddri_rep15_top5_feature_linkage_summary.md`, `07_ddri_cluster_final_recommendation.md` | 오류 상위 스테이션 순위와 군집 분포 | top5 정본에서 참조표로 흡수 |
| `09_ddri_rep15_top2_station_hourly_error_summary.md` | `12_ddri_rep15_top5_feature_linkage_summary.md` | 필요 시 top2가 top5 판단의 출발점이었다는 한 줄 | 실질적으로는 삭제 후보 |
| `11_ddri_rep15_top5_station_hourly_error_summary.md` | `12_ddri_rep15_top5_feature_linkage_summary.md` | 시간대 패턴 요약 | top5 정본의 부속 섹션으로 묶기 적합 |
| `rep15_error_analysis/README.md` | 자체 재작성 | 정본 2개와 archive 노트북 링크 | 폴더 사용법만 남김 |

### D. `works/06_prediction_long_full/`

| 축소 대상 | 흡수 대상 정본 | 남길 최소 내용 | 처리 방향 |
|---|---|---|---|
| `README.md`의 장문 설명 일부 | `02_ddri_station_hour_full_model_comparison.ipynb`, `10_ddri_model_score_summary.md` | 전체 161개 실험 목적, 우세 모델, 데이터 경로 | README는 짧은 안내문으로 축소 가능 |
| `output/images/` 다수 | 해당 노트북 또는 발표 문서 | 대표 차트 1~2장 | 나머지는 재생성 가능 산출물로 분리 |

### E. `cheng80/api_output/`

| 축소 대상 | 흡수 대상 정본 | 남길 최소 내용 | 처리 방향 |
|---|---|---|---|
| `ddri_api_summary_revalidation_checklist.csv` | `02_ddri_api_operational_rules.md` | 재검증 필요 항목 목록 | 문서 말미 TODO 형태로 흡수 |
| `ddri_api_key_compatibility_check.csv` | `02_ddri_api_operational_rules.md` | 어떤 키가 어떤 엔드포인트에 응답했는지 요약 | 표 전체 대신 한 단락으로 축약 |
| `ddri_service_realtime_join_preview.csv` | `01_ddri_api_verification.ipynb`, `02_ddri_api_operational_rules.md` | 서비스 join 예시 1개 | 샘플 설명만 남기고 CSV는 보관 |

## 4. 산출물 축소 기준

문서 외에 산출물은 아래 기준으로 줄인다.

### CSV

- 정본 문서가 직접 참조하는 요약표는 유지
- 중간 집계 CSV는 재생성 노트북이 있으면 `archive` 또는 보관 폴더로 이동
- lookup 성격 CSV는 서비스 연결에 직접 쓰이면 유지

### 이미지

- 문서나 발표에 직접 삽입되는 대표 차트만 유지
- 동일 메시지를 반복하는 이미지 묶음은 재생성 경로만 남기고 보관

### 노트북

- 설명 가능한 정본 노트북은 유지
- 재생성/집계/단계별 실험 노트북은 `archive` 또는 목적별 보관 폴더로 이동

## 5. 우선 실행 순서

다음 실제 정리 작업은 아래 순서가 안전하다.

1. `works/05_prediction_long/cheng80` 루트 요약 문서 내용을 `07_ddri_cluster_final_recommendation.md`에 흡수할 항목 표시
2. `rep15_error_analysis`의 top2/top5 문서를 `top5 정본 1개` 중심으로 재편
3. `08_ddri_service_output_logic_draft.md`와 `02_ddri_api_operational_rules.md`의 역할 경계를 정리
4. `works/README.md`, `works/00_overview/README.md`, `works/05_prediction_long/cheng80/README.md`를 새 구조 기준으로 재작성
5. 그 다음에야 실제 `archive` 이동과 삭제 후보 처리 진행

`works/00_overview/` 전용 우선순위:

1. `README.md`에서 과밀 목록 나열을 제거하고 `핵심 5~6문서`만 남긴다
2. `02_ddri_project_report_log.md`는 핵심 결정만 `01_ddri_master_plan.md`로 환원하고 원문은 보관 문서로 돌린다
3. `05`, `06`, `08`은 각각 `구조 안내`, `인벤토리`, `서비스 후처리` 역할만 남기도록 축소한다

## 6. 현재 판단

현재 구조 정리의 핵심은 `파일 수를 줄이는 것`보다 `정본 문서의 역할을 명확히 하는 것`이다.

즉 지금 바로 필요한 것은 아래 두 가지다.

- 대표 15개 실험 결론은 `07_ddri_cluster_final_recommendation.md`로 수렴
- 오류 해석 결론은 `12_ddri_rep15_top5_feature_linkage_summary.md`로 수렴

이 두 축이 정리되면, 나머지 중간 요약 문서 상당수는 보관 또는 삭제 후보로 안정적으로 이동할 수 있다.
