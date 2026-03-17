# 02 Web Service Final

이 경로는 분석 결과를 웹/앱 서비스 구조로 연결하는 최종 통합 축이다.

**웹 프로젝트:** `/Users/cheng80/Desktop/ddri_web` (Flutter 생성 완료)  
**범위:** 기획 단계 작성. 뼈대 확정 후 기획 문서·웹 프로젝트 함께 이전 예정.  
**범위 밖:** 이용권, 사용자 정보(회원가입·로그인·프로필 등) — 비로그인 공개 웹.

## 이 축에서 최종적으로 보여야 하는 것

- 서비스 목적
  - 재배치 관리자용 판단 지원
  - 일반 사용자용 시점별 대여 가능성 안내
- 예측 출력이 서비스 출력으로 변환되는 방식
- API 연결 규칙
- 화면/기능 흐름
- ERD, API 명세, Architecture Design 같은 웹 프로젝트 산출물
- 최종 시연과 동영상 제작 기준

## 현재 우선 문서

1. [01_ddri_flutter_web_service_preparation.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/01_ddri_flutter_web_service_preparation.md)
2. [02_ddri_web_service_project_plan.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/02_ddri_web_service_project_plan.md)
3. [03_ddri_web_service_screen_spec.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/03_ddri_web_service_screen_spec.md)
4. [04_ddri_database_design.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/04_ddri_database_design.md)
5. [05_ddri_erd.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/05_ddri_erd.md)
6. [06_ddri_flutter_web_planning_next_steps.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/06_ddri_flutter_web_planning_next_steps.md) – 다음 단계·갭·우선순위
7. [07_ddri_web_project_context_and_migration.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/07_ddri_web_project_context_and_migration.md) – 웹 프로젝트 위치, API 산출물·키, 이전 계획
8. [08_ddri_user_page_spec_detail.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/08_ddri_user_page_spec_detail.md) – 사용자 페이지 상세 (현 위치·주소 검색, kpostal_plus)
9. [09_stitch_design_application_guide.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/09_stitch_design_application_guide.md) – Stitch MCP 디자인 적용 가이드
10. [10_ddri_user_page_map_ux_spec.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/10_ddri_user_page_map_ux_spec.md) – 지도 UX (단일 지도 + 원형 반경 + 마커, 모바일/데스크탑 레이아웃)
11. [11_stitch_mcp_progress_and_references.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/11_stitch_mcp_progress_and_references.md) – Stitch MCP 진행 상황 및 참고 주소

## 현재 근거 정본

- 프로젝트 기준 문서:
  - [01_ddri_master_plan.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/01_ddri_master_plan.md)
- 예측 타깃 정의:
  - [03_ddri_prediction_target_definition.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/03_ddri_prediction_target_definition.md)
- 데이터셋 설계:
  - [04_ddri_prediction_dataset_design.md](/Users/cheng80/Desktop/ddri_work/works/00_overview/04_ddri_prediction_dataset_design.md)
- API 운영 규칙:
  - [02_ddri_api_operational_rules.md](/Users/cheng80/Desktop/ddri_work/cheng80/02_ddri_api_operational_rules.md)
- API 검증 노트북:
  - [01_ddri_api_verification.ipynb](/Users/cheng80/Desktop/ddri_work/cheng80/01_ddri_api_verification.ipynb)
- Open API 테스트 결과:
  - [cheng80/api_output/](/Users/cheng80/Desktop/ddri_work/cheng80/api_output/)
- API 키 (차후 FastAPI 이전 예정):
  - [cheng80/api_keys.env](/Users/cheng80/Desktop/ddri_work/cheng80/api_keys.env)
- 발표 정본:
  - [04_presentation](/Users/cheng80/Desktop/ddri_work/works/04_presentation)
- Flutter 서비스 준비 문서:
  - [01_ddri_flutter_web_service_preparation.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/01_ddri_flutter_web_service_preparation.md)
- 웹서비스 기획서:
  - [02_ddri_web_service_project_plan.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/02_ddri_web_service_project_plan.md)
- 화면 설계서:
  - [03_ddri_web_service_screen_spec.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/03_ddri_web_service_screen_spec.md)
- DB 설계서:
  - [04_ddri_database_design.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/04_ddri_database_design.md)
- ERD 초안:
  - [05_ddri_erd.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/02_web_service_final/05_ddri_erd.md)

## 작성 계획

1. 서비스 사용자와 핵심 시나리오 정리
2. 분석 출력과 서비스 출력 필드 연결
3. API 입력/출력과 예외 규칙 통합
4. ERD, 아키텍처, 화면 흐름 초안 정리
5. 발표/시연/동영상 제작 기준 연결
