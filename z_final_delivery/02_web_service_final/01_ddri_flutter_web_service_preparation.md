# DDRI Flutter 웹서비스 개발 준비 문서

작성일: 2026-03-16  
목적: 현재 분석/ML 프로젝트 오버뷰를 서비스 관점으로 재정리하고, Flutter 기반 웹서비스 개발을 바로 시작할 수 있도록 준비 기준을 고정한다.

## 1. 프로젝트 오버뷰

현재 DDRI 프로젝트는 강남구 따릉이 대여소 데이터를 바탕으로 아래 두 문제를 함께 해결하는 것을 목표로 한다.

- 운영자용:
  - 대여소별 시간대 수요를 예측하고 재배치 우선순위를 판단
- 일반 사용자용:
  - 특정 시각 특정 대여소의 예상 잔여 자전거 수와 대여 가능 여부를 안내

현재 분석/ML 단계의 직접 예측값은 `predicted_rental_count`다.  
서비스는 이 값을 실시간 재고와 결합해 아래 출력으로 바꿔 보여준다.

- 운영자 화면:
  - `predicted_demand`
  - `current_bike_stock`
  - `stock_gap`
  - `risk_score`
  - `reallocation_priority`
- 일반 사용자 화면:
  - `predicted_remaining_bikes`
  - `bike_availability_flag`
  - `availability_level`

즉, 서비스의 핵심은 `수요 예측 모델` 자체보다 `예측값을 사용자 행동에 맞는 판단 정보로 바꾸는 후처리 계층`에 있다.

## 2. 현재 확정된 분석 자산

서비스 준비 기준으로 지금 바로 활용 가능한 자산은 아래와 같다.

- 공통 서비스 대상 대여소:
  - `161개` 공통 스테이션
- 기본 시간 단위 운영 모델:
  - `LightGBM_RMSE_Full`
  - 2025 test RMSE `0.8624`
- 군집별 고도화 후보:
  - `cluster01`: `subset_a_commute_transit + LightGBM_Poisson`
  - `cluster02`: `current_compact_best + LightGBM_Poisson`
- 실시간 재고 기준 API:
  - `OA-15493 bikeList`
- 대여소 매핑 기준:
  - `tbCycleStationInfo`
- 서비스용 lookup:
  - `cheng80/api_output/ddri_full161_station_api_mapping_table.csv`
  - `cheng80/api_output/ddri_station_id_api_lookup.csv`

현재 해석상 서비스 1차 버전은 군집별 완전 분기보다 아래 방식이 가장 현실적이다.

- 공통 예측 baseline 1개를 기본 운영 모델로 사용
- `cluster01`, `cluster02`는 추후 서버 측 모델 라우팅으로 확장
- Flutter 앱은 모델 내부 로직을 직접 갖지 않고 예측 결과를 소비하는 클라이언트로 유지

## 3. Flutter 서비스로 옮길 때의 핵심 판단

Flutter로 화면을 만들더라도 예측과 실시간 수집은 앱 내부에서 직접 처리하지 않는 편이 맞다.

이유:

- ML 모델이 Python/노트북 기반 산출물과 연결되어 있음
- 서울시 실시간 API 키를 클라이언트에 직접 넣으면 관리가 어렵고 노출 위험이 큼
- 실시간 재고, 예측 결과, 예외 스테이션 규칙을 서버에서 먼저 정리해야 Flutter 상태 관리가 단순해짐

따라서 권장 구조는 아래와 같다.

1. `Prediction API`
   - 특정 `station_id + target_datetime` 입력
   - `predicted_rental_count` 또는 후처리된 `predicted_remaining_bikes` 반환
2. `Realtime Stock API`
   - `bikeList` 수집 후 대상 161개 스테이션만 필터링
   - 예외 스테이션 상태 포함 반환
3. `Service Aggregation API`
   - 예측값 + 실시간 재고 + 운영 규칙을 결합
   - Flutter는 이 최종 응답을 그대로 렌더링
4. `Flutter Web`
   - 조회, 필터, 지도/리스트, 상태 배지, 운영 대시보드 담당

즉 Flutter는 프론트엔드, Python 또는 별도 백엔드는 예측/집계 계층으로 분리하는 것이 맞다.

## 4. 권장 MVP 범위

Flutter 웹서비스 1차 범위는 아래 두 화면으로 충분하다.

### A. 일반 사용자 화면

- 대여소 검색
- 날짜/시간 선택
- 현재 자전거 수
- 예측 대여량
- 예상 잔여 자전거 수
- 대여 가능 여부 배지
- 실시간 비노출 대여소 예외 메시지

### B. 운영자 화면

- 대여소 목록 표
- 현재 재고
- 예측 수요
- 재고 차이값
- 위험 점수
- 재배치 우선순위 정렬
- 군집 필터
- 예외 스테이션 분리 보기

이 범위를 넘어서 지도, 즐겨찾기, 푸시, 다중 시간 비교까지 한 번에 넣으면 분석 결과 검증보다 UI 작업량이 더 커질 가능성이 높다.

## 5. Flutter 앱 구조 권장안

Flutter 프로젝트는 웹 기준으로 시작하되 모바일 확장 가능 구조로 만드는 편이 낫다.

권장 레이어:

- `lib/app/`
  - 앱 진입, 라우팅, 테마
- `lib/core/`
  - 환경변수, 공통 상수, 날짜 포맷, 에러 처리
- `lib/data/`
  - API client, DTO, repository
- `lib/domain/`
  - entity, usecase, 서비스 계산 모델
- `lib/features/user_station_forecast/`
  - 일반 사용자 조회 화면
- `lib/features/operator_dashboard/`
  - 운영자 대시보드
- `lib/features/station_search/`
  - 대여소 검색/필터
- `lib/shared/`
  - 공통 위젯, 배지, 카드, 표, 로딩/에러 뷰

상태 관리는 `Riverpod` 같은 명시적 구조가 적합하다.

이유:

- 일반 사용자 화면과 운영자 화면이 같은 대여소 데이터를 공유함
- 실시간 조회, 시간 선택, 필터 상태가 분리되어야 함
- API 실패와 예외 스테이션 처리를 UI에 안정적으로 반영하기 쉬움

## 6. 서버 응답 규격 초안

Flutter 개발을 시작하려면 먼저 화면보다 응답 계약을 고정하는 편이 낫다.

### 일반 사용자 조회 응답 예시

```json
{
  "station_id": 2328,
  "station_name": "르네상스 호텔 사거리 역삼지하보도 7번출구 앞",
  "target_datetime": "2026-03-16T18:00:00+09:00",
  "current_bike_stock": 7,
  "predicted_rental_count": 5.2,
  "predicted_remaining_bikes": 1.8,
  "bike_availability_flag": true,
  "availability_level": "low",
  "operational_status": "operational"
}
```

### 운영자 목록 응답 예시

```json
{
  "base_datetime": "2026-03-16T18:00:00+09:00",
  "items": [
    {
      "station_id": 2328,
      "cluster": "cluster00",
      "current_bike_stock": 7,
      "predicted_demand": 5.2,
      "stock_gap": 1.8,
      "risk_score": 0.72,
      "reallocation_priority": 3,
      "operational_status": "operational"
    }
  ]
}
```

이 계약이 먼저 있어야 Flutter에서 목업 API로도 화면 개발을 병행할 수 있다.

## 7. 투트랙 개발 원칙

산출물이 아직 계속 보강될 예정이므로, 웹서비스 개발은 단일 순차 방식보다 `투트랙`으로 운영하는 편이 맞다.

### 트랙 A. 분석/모델 산출물 확정 트랙

- 예측 모델 성능 보강
- 군집별 커스텀 모델 적용 여부 확정
- 후처리 식 정교화
- 서비스 입력용 테이블 정리
- 실시간 API 예외 규칙 고정

이 트랙의 산출물은 최종적으로 서버 응답 계약에 반영된다.

### 트랙 B. Flutter 서비스 개발 트랙

- 화면 구조 설계
- 공통 디자인 시스템
- 라우팅과 상태관리 세팅
- 목업 데이터 기반 UI 개발
- API 연동 인터페이스 선구현

이 트랙은 실제 모델이 완전히 끝나기 전에도 진행할 수 있다.

핵심 원칙은 아래와 같다.

1. Flutter는 실제 모델 파일이 아니라 `응답 계약`에 의존한다.
2. 분석 트랙은 CSV/노트북 산출물을 직접 UI에 연결하지 않고 서버 스키마로 번역한다.
3. 두 트랙의 접점은 `API spec`, `station lookup`, `예외 처리 규칙` 세 가지로 고정한다.

## 8. 지금 필요한 개발 준비 항목

우선순위 기준으로 정리하면 아래 7개가 필요하다.

1. 서비스 대상 161개 스테이션 기준 테이블 확정
2. 예측 API 입력/출력 스키마 고정
3. 실시간 재고 수집 배치 또는 API 래퍼 작성
4. 예외 스테이션 처리 규칙을 API 응답에 포함
5. 운영자/일반 사용자 화면 와이어프레임 확정
6. Flutter 프로젝트 초기 생성 및 라우팅/상태관리 세팅
7. 목업 데이터와 실데이터 전환 규칙 정리

## 9. 권장 개발 순서

### 1단계. 백엔드 계약 먼저 고정

- FastAPI 등으로 예측/재고/집계 API 초안 작성
- Flutter는 이 계약 기준으로 진행

### 2단계. Flutter 웹 골격 생성

- 라우트:
  - `/`
  - `/station`
  - `/operator`
- 공통 레이아웃
- 검색 바, 시간 선택기, 상태 배지 컴포넌트 구현

### 3단계. 목업 응답 연결

- 실제 모델 서버 전이라도 JSON fixture로 UI 개발 진행
- 응답 스키마 변경 비용을 초기에 줄임

### 4단계. 실시간 API 연결

- 서버에서 `bikeList`를 수집
- Flutter는 최종 가공 결과만 조회

### 5단계. 모델 결과 연결

- 공통 baseline 모델 결과부터 연결
- 이후 군집별 라우팅은 서버에서 점진 확장

## 10. 투트랙 운영 체크포인트

투트랙으로 갈 때는 매주 아래 항목을 같이 맞춰야 한다.

- 분석 트랙이 바꾼 출력 필드가 있는가
- Flutter 트랙이 가정한 응답 구조가 여전히 유효한가
- 예외 스테이션 규칙이 변경되었는가
- 운영자 화면 우선인지 일반 사용자 화면 우선인지 일정 우선순위가 유지되는가

권장 운영 방식:

- 분석 트랙 산출물은 주 단위 버전으로 고정
- Flutter 트랙은 그 버전을 기준으로 목업 또는 staging API를 사용
- 필드 변경은 ad hoc 공유가 아니라 문서와 샘플 JSON으로 같이 갱신

## 11. 현재 기준의 리스크

- 분석 결과는 충분히 진행되었지만 서비스 API 계약은 아직 문서화 초기 단계다
- Flutter만 먼저 시작하면 실제 예측/실시간 응답과 UI 요구가 뒤늦게 충돌할 수 있다
- 예외 스테이션 3개와 실시간 비노출 케이스를 처음부터 반영하지 않으면 운영 화면 정렬 로직이 흔들릴 수 있다
- 군집별 커스텀 모델을 프론트 요구사항으로 먼저 넣으면 일정이 불필요하게 커진다

## 12. 현재 결론

현재 프로젝트는 `분석 완료 후 서비스 미정` 상태가 아니라, 이미 서비스로 옮길 수 있을 만큼 핵심 판단이 모여 있다.  
다만 지금은 산출물이 더 나올 예정이므로, Flutter 개발은 `완성 산출물 대기` 방식보다 `투트랙 병행` 방식으로 진행해야 한다.

그 기준에서 Flutter 개발의 출발점은 `앱 구현` 자체가 아니라 아래 두 가지다.

- `서비스 응답 계약 고정`
- `예측/실시간/API 집계 계층의 서버 분리`

이 기준으로 진행하면 Flutter는 화면과 사용자 흐름에 집중할 수 있고, ML 산출물도 무리 없이 서비스에 연결할 수 있다.
