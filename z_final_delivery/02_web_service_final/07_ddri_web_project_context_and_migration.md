# DDRI 웹 프로젝트 컨텍스트 및 이전 계획

작성일: 2026-03-16  
목적: 웹 프로젝트 위치, 기획 범위, API 산출물·키 이전 계획을 고정한다.

---

## 1. 현재 구조

### 1.1 웹 프로젝트

| 항목 | 경로 | 상태 |
|------|------|------|
| Flutter 웹 프로젝트 | `/Users/cheng80/Desktop/ddri_web` | 생성 완료 |
| 기획 문서 | `ddri_work/z_final_delivery/02_web_service_final/` | 기획 단계 작성 중 |

### 1.2 이전 계획

- 기획 문서 뼈대가 어느 정도 잡히면 **기획 문서 + 웹 프로젝트**를 함께 이전 예정
- 현재는 **기획 단계까지만** 작성
- 웹 프로젝트 코드 본격 개발은 이전 후 진행

---

## 2. API 관련 산출물

### 2.1 Open API 테스트 결과

| 경로 | 내용 |
|------|------|
| `ddri_work/cheng80/api_output/` | Open API 검증 산출물 |

**주요 파일:**

| 파일 | 용도 |
|------|------|
| `ddri_full161_station_api_mapping_table.csv` | 161개 스테이션 매핑 (station_id ↔ ST-xxxx, operational_status) |
| `ddri_station_id_api_lookup.csv` | 경량 lookup (station_id → resolved_api_station_id) |
| `ddri_full161_station_api_validation_official.csv` | 공식 bikeList 매칭 결과 |
| `ddri_api_key_compatibility_check.csv` | API 키 호환성 검증 |
| `ddri_service_realtime_join_preview.csv` | 실시간·예측 결합 미리보기 |

### 2.2 API 키

| 항목 | 경로 | 이전 계획 |
|------|------|-----------|
| API 키 (로컬 전용) | `ddri_work/cheng80/api_keys.env` | 웹 프로젝트 FastAPI 쪽으로 이전 예정 |

**포함 키:**
- `SEOUL_RTD_API_KEY` (OA-21285 실시간 도시데이터)
- `SEOUL_BIKE_API_KEY` (OA-15493 따릉이 실시간 대여정보)

**주의:** Git 커밋 금지. 이전 시 `.env` 또는 서버 환경변수로 관리.

### 2.3 API 운영 규칙

- `cheng80/02_ddri_api_operational_rules.md`
- 기준 API: OA-15493 bikeList, tbCycleStationInfo
- 예외 스테이션 3개: 2314, 2323, 3628 (실시간 비노출)

---

## 3. 기획 단계 범위

현재 작성 범위는 **기획 단계**로 제한한다.

| 포함 | 제외 |
|------|------|
| 서비스 목적·사용자 시나리오 | Flutter 코드 구현 |
| 화면 설계·라우팅 | FastAPI 구현 |
| API 응답 스키마·계약 | DB 구축 |
| DB·ERD 설계 | API 키 이전 |
| 이전 계획·참조 경로 | |

---

## 4. 이전 시 반영할 항목

기획 문서와 웹 프로젝트 이전 시 아래를 함께 옮긴다.

1. **기획 문서** (`02_web_service_final/*.md`)
2. **웹 프로젝트** (`ddri_web/`)
3. **API 산출물** (`cheng80/api_output/*.csv`) – 서버/데이터용
4. **API 키** (`api_keys.env`) – FastAPI 환경변수로 이전, 원본은 보안 유지
5. **API 운영 규칙** (`02_ddri_api_operational_rules.md`)

---

## 5. 참조 경로 요약

| 용도 | 경로 |
|------|------|
| 웹 프로젝트 | `/Users/cheng80/Desktop/ddri_web` |
| 기획 문서 | `ddri_work/z_final_delivery/02_web_service_final/` |
| API 테스트 결과 | `ddri_work/cheng80/api_output/` |
| API 키 | `ddri_work/cheng80/api_keys.env` |
| API 운영 규칙 | `ddri_work/cheng80/02_ddri_api_operational_rules.md` |
| 프로젝트 루트 | `ddri_work/works/00_overview/` |
