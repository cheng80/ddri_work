# DDRI Overview Reduction Checklist

작성일: 2026-03-15  
목적: `works/00_overview/` 정리 작업을 `체크리스트 기반`으로 진행하기 위한 작업 문서다.

이 문서는 아래 용도로 사용한다.

- `overview` 문서별 현재 상태 점검
- 정본 / 축소 / 보관 / archive 후보 판정
- 작업 중간에 기준 추가, 삭제, 수정
- 실제 반영 여부 체크

## 1. 공통 판정 기준

각 문서는 아래 항목을 기준으로 점검한다.

- [ ] 현재 정본 역할이 분명한가
- [ ] 다른 정본 문서와 역할이 겹치지 않는가
- [ ] 지금도 자주 다시 열어야 하는가
- [ ] 핵심 노트북 실행이나 최종 판단과 직접 연결되는가
- [ ] 길이/밀도가 과도하지 않은가
- [ ] archive 또는 보관 문서로 내려도 되는가
- [ ] README에서 전면 노출이 필요한가

판정 규칙:

- 위 항목 대부분이 `예`면 `보존`
- 역할은 있으나 길거나 중복이면 `축소`
- 추적은 필요하지만 핵심 읽기 경로는 아니면 `보관`

## 2. `overview` 목표 상태

- 정본 `5~6개` 수준으로 압축
- 구조 정리 점검 문서는 `cleanup/`에서 별도 관리
- `README`는 문서 목록이 아니라 읽기 순서 안내문으로 유지
- 큰 로그 문서는 핵심 결정만 상위 정본에 흡수하고 원문은 보관

## 3. 문서별 체크

### `01_ddri_master_plan.md`

- [x] 현재 정본 역할이 분명한가
- [x] 핵심 노트북 실행/최종 판단과 직접 연결되는가
- [x] 현재 유효한 결정 일부를 이미 흡수했는가
- [ ] 길이 과밀 여부를 다시 점검했는가

현재 판단:

- `보존`
- 필요 시 후속 축약 가능

### `02_ddri_project_report_log.md`

- [ ] 현재 정본 역할이 분명한가
- [ ] 다른 정본 문서와 역할이 겹치지 않는가
- [ ] 지금도 전면에서 읽어야 하는가
- [x] 길이/밀도가 과도한가
- [x] 핵심 결정이 `01_ddri_master_plan.md`에 일부 흡수되었는가
- [x] 원문을 보관 문서로 내려도 되는가

현재 판단:

- `축소 + 보관` 후보
- 다음 우선 점검 대상

점검 메모:

- 현재 유효한 핵심 결정은 이미 아래 정본 문서들로 상당 부분 흡수 가능하다
  - `01_ddri_master_plan.md`
  - `10_ddri_model_score_summary.md`
  - `cheng80/02_ddri_api_operational_rules.md`
  - `works/05_prediction_long/cheng80/07_ddri_cluster_final_recommendation.md`
- 특히 아래 결정들은 `현재도 유효한 핵심 결정`으로 본다
  - `Decision 0XY` 실시간 API 기준 및 161개 매핑 규칙
  - `Decision 0XX` 군집별 최종 권장안 해석
  - `Decision 017`, `018`, `020` 통합 군집화 정리 방식
  - `Decision 022`, `023`, `024`, `026`, `027` 예측 baseline 및 대표/전체 실험 해석
  - `Decision 031`, `032`, `033`, `034`, `035`, `036`, `037`
  - `Decision 038`~`043`
- 반대로 초기 1차 군집화 세부 로그, 종료된 과거 이슈, 이미 수행 완료된 정리 이력은 전면 노출 가치가 낮다

현재 결론:

- `report_log`는 더 이상 `overview` 전면 정본 문서가 아니다
- 다음 단계에서 할 일은 `원문 유지 여부`보다 `보관 문서로 내렸을 때 README와 상위 문서에서 충분히 대체 가능한가`를 최종 확인하는 것이다

반영 상태:

- [x] `works/00_overview/archive_docs/`로 이동 완료

### `03_ddri_prediction_target_definition.md`

- [x] 현재 정본 역할이 분명한가
- [x] 예측 타깃 정의 정본으로 유지 가치가 있는가
- [ ] 다른 정본과 중복이 과도한지 재점검했는가

현재 판단:

- `보존`

### `04_ddri_prediction_dataset_design.md`

- [x] 현재 정본 역할이 분명한가
- [x] 최종 입력 구조 설명에 필요 한가
- [x] archive_data_collection 경로 반영이 되었는가
- [ ] 길이 축약 필요성을 재점검했는가

현재 판단:

- `보존`

### `05_ddri_workspace_structure_guide.md`

- [x] 현재 구조 안내문으로 축약되었는가
- [ ] README와 역할이 과하게 겹치지 않는가
- [ ] 최종 구조 확정 후 추가 축약이 필요한가

현재 판단:

- `archive`

### `06_ddareungi_project_inventory_2026-03-11.md`

- [x] 보관형 인벤토리 문서로 역할이 재정의되었는가
- [ ] `overview` 전면 노출에서 계속 제외해도 되는가
- [ ] archive성 문서로 별도 이동할지 판단했는가

현재 판단:

- `archive`

### `07_ddri_notebook_and_evidence_chart_policy.md`

- [x] 현재 정본 역할이 분명한가
- [x] 정책 문서 정본으로 유지 가치가 있는가

현재 판단:

- `보존`

### `08_ddri_service_output_logic_draft.md`

- [x] API 세부 규칙과 역할이 분리되었는가
- [ ] 서비스 후처리 정본으로 승격할지 여부를 판단했는가
- [ ] `cheng80/02_ddri_api_operational_rules.md`와 함께 읽는 구조가 충분히 명확한가

현재 판단:

- `archive`
- 핵심 서비스 후처리 항목은 `01_ddri_master_plan.md`에 최소 고정안으로 반영

### `09_ddri_cluster_specific_modeling_strategy.md`

- [ ] 현재 정본 역할이 분명한가
- [ ] `01_ddri_master_plan.md`와 역할이 겹치지 않는가
- [ ] `05_prediction_long`, `06_prediction_long_full` README와 중복이 없는가
- [x] 전면 보존이 필요한가

현재 판단:

- `archive`
- 현재 핵심 내용은 `01_ddri_master_plan.md`와 `07_ddri_cluster_final_recommendation.md` 쪽에서 이미 읽을 수 있다

### `10_ddri_model_score_summary.md`

- [x] 현재 정본 역할이 분명한가
- [x] 점수 요약 정본으로 유지 가치가 있는가

현재 판단:

- `보존`

### `README.md`

- [x] 핵심 정본 중심 읽기 순서 안내로 줄였는가
- [ ] 최종 구조 확정 후 다시 한 번 줄일 필요가 있는가

현재 판단:

- `유지`
- 최종 구조 확정 후 1회 추가 정리 가능

## 4. 다음 작업 순서

1. `02_ddri_project_report_log.md` 체크 항목 실제 점검
2. 점검 결과를 바탕으로 `보관` 또는 `archive_docs` 이동 시점 판단
3. `09_ddri_cluster_specific_modeling_strategy.md` 점검
4. 마지막으로 `overview` 최종 정본 목록 고정

## 5. 작업 메모

- 체크리스트는 작업 중간에 자유롭게 항목을 추가/삭제/수정한다
- 새로운 문제가 보이면 이 문서에 먼저 기준을 적고 나서 실제 파일을 수정한다
