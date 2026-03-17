# DDRI Flutter 웹 기획 – 다음 단계

작성일: 2026-03-16  
목적: `02_web_service_final`과 `works/00_overview` 기준으로 Flutter 웹 기획을 이어가기 위한 현황·갭·다음 액션 정리

**범위:** 기획 단계까지만 작성. 웹 프로젝트(`/Users/cheng80/Desktop/ddri_web`)는 생성 완료. 기획 뼈대 확정 후 기획 문서·웹 프로젝트 함께 이전 예정.

---

## 1. 현황 요약

### 1.1 프로젝트 루트 (works/00_overview)

| Phase | 상태 | 비고 |
|-------|------|------|
| Phase 1. 데이터 자산 확정 | 완료 | raw_data, full_data 기준 |
| Phase 2. 군집화 | 완료 | 08_integrated/final |
| Phase 3. 예측 데이터셋 설계 | 완료 | station-day, station-hour |
| Phase 4. ML 베이스라인 | 미완료 | RMSE 0.8624, 오류 분석·후처리 로직 미완 |
| Phase 5. 웹/서비스 설계 | 미완료 | 기획 문서 수준 |
| Phase 6. 최종 보고서 | 미완료 | 군집화 발표만 |

### 1.2 웹서비스 기획 (02_web_service_final)

| 문서 | 상태 | 내용 |
|------|------|------|
| 01_flutter_preparation | 완료 | Flutter 구조, API 계약, 투트랙 원칙 |
| 02_project_plan | 완료 | 페이지 범위, MVP, 기능 우선순위 |
| 03_screen_spec | 완료 | 사용자/관리자/통계 화면 설계 |
| 04_database_design | 완료 | 6개 테이블 정의 |
| 05_erd | 완료 | Mermaid ERD |

### 1.3 마스터 플랜 2026-03-16 정리

- `05_prediction_long`, `06_prediction_long_full` 폐기 대상
- 예측 정본 재구축 단계
- 유효 입력: `3조 공유폴더/raw_data`, `full_data`만 사용

---

## 2. Flutter 웹 기획 갭

| 항목 | 현재 | 부족 |
|------|------|------|
| API 명세 | JSON 예시만 | OpenAPI/Swagger 스펙 |
| 예측 타깃 | rental_count | bike_change vs rental_count 정리 필요 |
| 실시간 API | OA-15493 bikeList | 호출 주기·캐시 정책 |
| 예외 스테이션 | 3개(2314, 2323, 3628) | API 응답 규칙 |
| 와이어프레임 | 텍스트 설계 | 시각적 와이어프레임 |
| Flutter 프로젝트 | 없음 | 초기 생성·라우팅 세팅 |

---

## 3. 다음 액션 (우선순위)

### 3.1 즉시 진행 가능

1. **API 응답 스키마 고정**
   - 01_flutter_preparation의 JSON 예시를 OpenAPI 3.0 초안으로 정리
   - `/user/station/{id}`, `/admin/stations`, `/stats/summary` 엔드포인트 정의

2. **Flutter 프로젝트 골격 생성**
   - `flutter create ddri_web --platforms web`
   - 라우트: `/user`, `/admin`, `/stats`
   - lib/app, lib/core, lib/features 구조

3. **목업 데이터 JSON 작성**
   - 일반 사용자·관리자·통계 응답 fixture 3종
   - Flutter에서 목업 API 클라이언트 연결

### 3.2 분석 트랙과 협의 필요

4. **예측 타깃 정리**
   - rental_count vs bike_change 서비스 연결 방식
   - `predicted_remaining_bikes = current_stock - predicted_rental` vs `current_stock + bike_change`

5. **예외 스테이션 처리 규칙**
   - `operational_status`: operational | realtime_unavailable | inactive
   - API 응답에 포함 방식

### 3.3 후순위

6. **와이어프레임**
   - Figma/Excalidraw 등으로 사용자/관리자/통계 화면 스케치

7. **실시간 API 래퍼**
   - bikeList 수집 배치 또는 FastAPI 엔드포인트

---

## 4. 권장 진행 순서

```
1. API 스키마 문서화 (06 또는 별도 api_spec.md)
2. Flutter 프로젝트 생성 + 라우팅
3. 목업 JSON + MockApiClient
4. 사용자 페이지 UI (목업 기반)
5. 관리자 페이지 UI (목업 기반)
6. 통계 페이지 UI (목업 기반)
7. 백엔드 API 연동 (실제 예측·실시간 연결)
```

---

## 5. 참조 문서·경로

| 용도 | 경로 |
|------|------|
| 프로젝트 루트 | `works/00_overview/01_ddri_master_plan.md` |
| 예측 타깃 | `works/00_overview/03_ddri_prediction_target_definition.md` |
| API 규칙 | `cheng80/02_ddri_api_operational_rules.md` |
| API 테스트 결과 | `cheng80/api_output/` |
| API 키 (이전 예정) | `cheng80/api_keys.env` → FastAPI 환경변수 |
| Flutter 준비 | `01_ddri_flutter_web_service_preparation.md` |
| 프로젝트·이전 계획 | `07_ddri_web_project_context_and_migration.md` |
