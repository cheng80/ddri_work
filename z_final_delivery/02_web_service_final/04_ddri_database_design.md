# DDRI 웹서비스 데이터베이스 설계서

작성일: 2026-03-16  
목적: 웹서비스에서 필요한 저장 데이터의 범위와 테이블 구조를 최소 기준으로 정의한다.

## 1. 설계 원칙

- 사용자 계정 저장은 1차 범위에서 제외
- 서비스는 공용 데이터 조회 중심으로 설계
- 예측 결과와 실시간 재고는 분리 저장
- 스테이션 마스터와 운영 상태는 별도 관리
- 통계는 원시 로그보다 집계 결과 저장을 우선

## 2. 저장 대상

### 반드시 저장

- 서비스 대상 스테이션 마스터
- 스테이션 API 매핑 정보
- 실시간 재고 캐시
- 예측 결과
- 통계 집계 결과

### 선택 저장

- 시스템 호출 로그
- 관리자 작업 이력

### 현재 제외

- 회원 정보
- 사용자 즐겨찾기
- 개인 설정

## 3. 테이블 목록

### 1. `stations`

역할:

- 서비스 대상 스테이션 기본 정보 저장

주요 컬럼:

- `id`
- `station_id`
- `api_station_id`
- `station_name`
- `district_name`
- `address`
- `latitude`
- `longitude`
- `cluster_code`
- `operational_status`
- `is_service_target`
- `created_at`
- `updated_at`

### 2. `station_api_mappings`

역할:

- 숫자형 `station_id`와 외부 API의 `ST-xxxx` 계열 ID 매핑 관리

주요 컬럼:

- `id`
- `station_id`
- `resolved_api_station_id`
- `source_api`
- `match_status`
- `exception_reason`
- `verified_at`

### 3. `realtime_station_stock`

역할:

- 실시간 재고 캐시 저장

주요 컬럼:

- `id`
- `station_id`
- `stock_datetime`
- `current_bike_stock`
- `parking_bike_total_count`
- `shared_count`
- `operational_status`
- `raw_payload_hash`
- `created_at`

### 4. `station_demand_forecasts`

역할:

- 시간 단위 예측 결과 저장

주요 컬럼:

- `id`
- `station_id`
- `target_datetime`
- `predicted_rental_count`
- `predicted_return_count`
- `predicted_remaining_bikes`
- `availability_level`
- `model_version`
- `cluster_code`
- `created_at`

### 5. `station_risk_snapshots`

역할:

- 운영자용 재배치 판단 결과 저장

주요 컬럼:

- `id`
- `station_id`
- `base_datetime`
- `current_bike_stock`
- `predicted_demand`
- `stock_gap`
- `risk_score`
- `reallocation_priority`
- `operational_status`
- `created_at`

### 6. `statistics_snapshots`

역할:

- 통계 페이지에서 사용하는 집계 결과 저장

주요 컬럼:

- `id`
- `base_date`
- `base_hour`
- `cluster_code`
- `metric_key`
- `metric_value`
- `dimension_key`
- `dimension_value`
- `created_at`

## 4. 테이블별 관계 요약

- `stations`는 기준 마스터 테이블
- `station_api_mappings`는 `stations.station_id`를 참조
- `realtime_station_stock`는 `stations.station_id`를 참조
- `station_demand_forecasts`는 `stations.station_id`를 참조
- `station_risk_snapshots`는 `stations.station_id`를 참조
- `statistics_snapshots`는 집계성 테이블로 직접 참조보다는 조회용으로 사용

## 5. 저장 전략

### 실시간 재고

- 원본 API 응답 전체 저장보다 필요한 컬럼만 캐시
- 일정 주기로 갱신

### 예측 결과

- 요청 시 실시간 계산 방식 또는 사전 배치 생성 방식 중 선택 가능
- 1차는 특정 시간대 기준 배치 저장이 더 단순

### 통계 집계

- 화면 응답 속도를 위해 사전 집계 테이블 유지 권장

## 6. 1차 기술 선택 권장

- DB:
  - PostgreSQL
- 이유:
  - 관계형 구조에 적합
  - 통계/집계 질의 처리에 안정적
  - 추후 PostGIS 확장 가능

## 7. 현재 결론

이 서비스는 사용자 중심 서비스라기보다 스테이션 중심 데이터 서비스다.  
따라서 1차 DB 설계는 `회원 테이블`보다 `스테이션/재고/예측/통계` 네 축을 먼저 닫는 것이 맞다.
