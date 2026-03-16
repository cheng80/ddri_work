# Ddri Master Plan

작성일: 2026-03-11  
최종 점검일: 2026-03-16  
목적: 프로젝트 진행 상태를 실제 산출물 기준으로 점검하고, 분석/ML Report와 앱 기능 설계를 다음 단계로 연결한다.

## 0. 작업 원칙

- [x] 데이터 기준 연도 고정
  - 학습: `2023-01-01 ~ 2024-12-31`
  - 테스트: `2025-01-01 ~ 2025-12-31`
- [x] 파일명/폴더명/산출물 prefix는 기본적으로 `ddri` 사용
- [x] 없는 자료는 임의로 생성하거나 추정값으로 채우지 않음
- [x] 작업 중 필수 자료가 없으면 즉시 사용자에게 요청
- [x] 모든 산출물은 기본적으로 `works/` 아래에 저장
- [x] 대표 노트북은 설명형 마크다운 셀과 코드 주석을 포함한 `실험 문서` 형태 유지
- [x] 앱 구현 전까지의 모든 분석과 ML 작업은 노트북 기반으로 진행
  - 스크립트는 보조 재생성 도구 또는 유틸 성격으로만 사용
  - 분석 해석, 전처리 설명, 모델 실험 로그, 결과 비교는 반드시 노트북에 남김
- [x] 발표/레포트용 차트는 결과 소개보다 `선정 근거 설명용 차트`를 우선 생성
- [x] 정책 문서는 `works/00_overview/07_ddri_notebook_and_evidence_chart_policy.md`를 정본으로 사용
- [x] 군집화 이후 예측 단계는 `대표 대여소 탐색 -> 전체 스테이션 공통 baseline -> 군집별 축소 피처 조합(subset) 최적화` 순서로 해석

## 0.1 용어 정리

- `subset`(축소 피처 조합)
  - 전체 후보 피처 중 일부만 골라 만든 피처 묶음
- `objective`(학습 목표 함수)
  - 모델이 무엇을 더 잘 맞추도록 학습할지 정하는 기준
- `RMSE objective`
  - 일반 회귀형 학습 목표 함수
- `Poisson objective`
  - 수요량, 건수처럼 `0 이상 count 데이터`에 맞춘 학습 목표 함수
- `baseline`(기준선 모델)
  - 추가 보강 없이 먼저 비교하는 기본 모델
- `feature`(입력 변수)
  - 모델이 예측에 사용하는 입력값
- `interaction`(상호작용 피처)
  - 두 조건을 함께 반영하도록 만든 결합 피처
- `routing`(군집 분기 적용)
  - 군집별로 다른 모델이나 피처 조합을 나눠 적용하는 방식

## 1. 현재 문제 정의

현재 앱은 하나의 기능만 해결하는 것이 아니라, 아래 두 사용자 문제를 함께 다룬다.

### A. 운영자용 문제

목표:

- 대여소별 수요를 예측하고
- 특정 시간대 부족 가능성을 파악하고
- 재배치 우선순위와 운영 판단을 지원한다

핵심 질문:

- 어느 스테이션이 언제 부족해질 가능성이 큰가
- 어떤 스테이션/군집/시간대에서 재배치 우선순위가 높은가
- 예측 수요를 기준으로 적정 보유 대수 또는 재배치 필요성을 어떻게 해석할 것인가

### B. 일반 사용자용 문제

목표:

- 사용자가 특정 스테이션과 특정 시각을 입력했을 때
- 그 시점에 자전거가 몇 대 남아 있을지 예측하여 보여준다

핵심 질문:

- 사용자가 원하는 시각에 해당 스테이션에서 자전거를 빌릴 수 있는가
- 특정 시간대에 잔여 자전거가 부족하거나 충분한가

### 현재 프로젝트 해석

분석/ML 단계의 직접 예측값은 우선 `대여량`이다.

즉,

- 1차 ML 출력: `rental_count(예측 대여량)`
- 운영자 기능: 수요 예측을 재배치 판단 지표로 변환
- 일반 사용자 기능: 수요 예측과 재고/보유 추정 로직을 결합해 `예상 잔여 자전거 수` 또는 `대여 가능 여부`로 변환

따라서 현재 문제 정의는 아래처럼 고정한다.

- 분석/ML 1차 목표: 대여소별 수요 예측
- 서비스 1차 목표: 운영자 재배치 지원 + 일반 사용자 잔여 자전거 예측

## 2. 전체 단계 현황

- [x] Phase 1. 데이터 자산 확정
- [x] Phase 2. 군집화 통합 산출물
- [x] Phase 3. 예측용 데이터셋 설계
- [ ] Phase 4. ML 베이스라인 구축
- [ ] Phase 5. 웹/서비스 설계 문서화
- [ ] Phase 6. 최종 보고서 및 영상 산출물 정리

## 3. 현재 상태 요약

현재 기준으로 프로젝트는 아래처럼 재정리되었다.

1. 통합 군집화 최종 결과 정리 완료
2. 발표용 군집화 문서 및 PDF 정리 완료
3. 대표 대여소 `raw_data`와 전체 스테이션 `full_data` 원천 CSV는 유지
4. 과거 `station-day`, `station-hour`, `bike_change` 예측 실험 경로는 현재 정본 기준에서 제외
5. `03_prediction`, `02_data_collection`은 `works/archive_legacy/`로 이동
6. 기존 `05_prediction_long`, `06_prediction_long_full`은 폐기 대상으로 판단
7. 현재 예측 파트는 과거 점수 계승이 아니라 정본 재구축 단계로 전환
8. ML 오류 분석과 서비스 후처리 로직 정교화는 아직 미완료
9. 실시간 서비스 연결용 외부 API 후보 확보

### 3.1 2026-03-16 정리 로그

- 기존 예측 실험 검토 결과, 잘못된 타깃 또는 흔들린 정본 정의를 전제로 한 실험 데이터는 더 이상 유지 가치가 없다고 판단했다.
- 특히 과거 `station-hour` 계열 실험 결과와 `bike_change` 파생 실험 결과는 현재 기준 정본으로 승계하지 않는다.
- 과거 `station-day` baseline과 데이터 수집 보조 경로는 삭제 대신 `archive_legacy`로 이동했다.
- 현재 이후 작업의 유효 입력은 아래 두 경로만 본다.
  - `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/`
  - `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/`

핵심 결과 위치:

- 통합 군집화 최종 결과:
  - `works/01_clustering/08_integrated/final/results/second_clustering_results/`
- 통합 군집화 최종 피처:
  - `works/01_clustering/08_integrated/final/features/`
- 과거 station-day 예측 데이터 보관:
  - `works/archive_legacy/03_prediction/`
- 대표 대여소 원천 데이터:
  - `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/`
- 전체 스테이션 원천 데이터:
  - `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/`
- 발표 자료:
  - `works/04_presentation/`
- 실시간 서비스 입력 후보:
  - 서울시 실시간 도시데이터
  - 서울시 공공자전거 따릉이 실시간 대여정보

## 3.2 현재 고정 판단

`works/00_overview/archive_docs/02_ddri_project_report_log.md`에 누적된 결정 중, 현재 기준 문서에 직접 반영해야 하는 판단만 아래처럼 고정한다.

- 실시간 재고 기준 API는 `OA-15493 bikeList(공식 실시간 자전거 보유 정보 API)`로 사용한다.
- 서비스 대상 `161개` 스테이션은 `station_id(숫자 대여소 ID) ↔ ST-xxxx(문자 대여소 ID) ↔ 운영 상태` 매핑 테이블을 별도 lookup으로 고정한다.
- 통합 군집화 정본 구조는 `works/01_clustering/08_integrated/{final,intermediate,pipeline,source_data}` 기준으로 유지한다.
- 과거 예측 실험 데이터와 점수표는 현재 기준 모델 정본으로 사용하지 않는다.
- 잘못된 타깃 또는 흔들린 정본 정의를 전제로 한 실험 데이터는 유지하지 않는다.
- 문서와 차트의 용어 표기는 기본적으로 `한글(영문)` 형식으로 통일한다.

관련 정본:

- `cheng80/02_ddri_api_operational_rules.md`
- `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/`
- `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/`

## 3.3 서비스 후처리 최소 고정안

서비스 출력 로직은 상세 초안 문서를 따로 길게 유지하기보다, 현재 기준 아래 수준으로만 고정한다.

- 운영자용 핵심 지표:
  - `predicted_demand(예측 수요량)`
  - `current_bike_stock(현재 자전거 보유 대수)`
  - `stock_gap(재고 차이값) = current_bike_stock(현재 자전거 보유 대수) - predicted_demand(예측 수요량)`
  - `risk_score(위험 점수)`
  - `reallocation_priority(재배치 우선순위)`
- 일반 사용자용 핵심 지표:
  - `predicted_remaining_bikes(예상 잔여 자전거 수)`
  - `bike_availability_flag(대여 가능 여부 표시값)`
  - `availability_level(대여 가능 수준)`
- 가장 단순한 1차 계산식:
  - `predicted_remaining_bikes(예상 잔여 자전거 수) = current_bike_stock(현재 자전거 보유 대수) - predicted_rental_count(예측 대여량)`
- 더 현실적인 다음 단계:
  - `predicted_remaining_bikes(예상 잔여 자전거 수) = current_bike_stock(현재 자전거 보유 대수) + predicted_return_count(예측 반납량) - predicted_rental_count(예측 대여량)`
- 실시간 재고 입력과 예외 스테이션 규칙은 `cheng80/02_ddri_api_operational_rules.md` 기준으로 연결한다

## 4. Phase 1. 데이터 자산 확정

목표: 실제 사용 가능한 데이터와 사용 불가능한 데이터를 구분하고, 이후 단계의 입력 기준을 고정한다.

### 체크리스트

- [x] 원천 데이터 폴더 구조 확인
- [x] 핵심 데이터 스키마 샘플 확인
- [x] 학습/테스트 연도 분리 기준 확정
- [x] `works/` 아래 실행용 폴더 구조 생성
- [x] 데이터 인벤토리 문서 유지 방식 결정
- [x] 군집화 1차 작업에 사용할 입력 파일 목록 정리
- [x] 연도별 대여소 기준 정보 사용 전략 확정

### 완료 기준 점검

- [x] 실제 사용할 입력 파일 목록이 문서로 고정됨
- [x] 학습/테스트 기준이 문서로 고정됨
- [x] 폴더 구조가 생성되어 있음

## 5. Phase 2. 군집화 통합 산출물

목표: 강남구 대여소 이용 패턴, 반납 시간대, 순유입, 교통 접근성, 생활인구, 환경 보강 실험을 포함한 통합 군집화 결과를 완성한다.

### 체크리스트

- [x] 기준선 모델(baseline) 이용 패턴 군집화 수행
- [x] 반납 시간대 기반 지구판단 피처 생성
- [x] 순유입/교통 접근성 결합 입력 확정
- [x] 생활인구 결합 완료
- [x] Open-Meteo 표고 피처 생성
- [x] 도시자연공원구역/하천경계 거리 기반 환경 보강 실험 수행
- [x] 통합 군집화 K 탐색 및 최종 K 선택
- [x] 통합 군집화 차트/지도/정적 이미지 생성
- [x] 발표 문서와 스피치 노트 반영
- [x] 작업물 구조를 `08_integrated/final/intermediate/pipeline` 기준으로 재정리
- [x] POI 보강 실험 산출물 추가 생성

### 완료 기준 점검

- [x] 최종 통합 피처와 군집 결과가 `works/01_clustering/08_integrated/final/` 아래 저장됨
- [x] 최종 통합 군집화 리포트와 차트가 생성됨
- [x] 환경 보강 실험 결과가 중간 산출물로 정리됨
- [x] 발표 문서와 스피치 노트가 최신 결과 기준으로 갱신됨

## 6. Phase 3. 예측용 데이터셋 설계

목표: 군집 결과를 포함한 예측용 학습 테이블 구조를 정의하고, 운영자/일반 사용자 기능으로 확장 가능한 형태의 데이터셋을 만든다.

### 체크리스트

- [x] 예측 target 정의 확정
- [x] 예측 기준 테이블 grain 확정
- [x] 내부 데이터와 외부 데이터 결합 키 설계
- [x] 날씨 결합 기준 설계
- [x] 공휴일 결합 기준 설계
- [x] 환경 피처(feature) 결합 전략 설계
- [x] 군집 라벨(label)을 예측 피처(feature)로 포함할지 결정
- [x] 학습용 최종 스키마 문서화
- [x] station-day 베이스라인 데이터셋 생성
- [x] 대표 대여소 15개 기준 station-hour long-format 데이터셋 생성
- [x] 전체 공통 스테이션 161개 기준 station-hour long-format 데이터셋 생성
- [x] 대표 대여소 선정 기준과 그룹 정의 문서화
- [x] 대표 대여소 실험 경로와 전체 스테이션 실험 경로 분리

### 완료 기준 점검

- [x] 예측 단위와 타깃이 문서로 고정됨
- [x] 결합 규칙이 문서로 정리됨
- [x] 최종 학습 테이블 스키마 초안이 존재함
- [x] 실제 사용 가능한 CSV 산출물이 생성됨

### 현재 결과 위치

- station-day 베이스라인:
  - `works/03_prediction/02_data/ddri_station_day_train_baseline_dataset.csv`
  - `works/03_prediction/02_data/ddri_station_day_test_baseline_dataset.csv`
- 대표 대여소 station-hour long-format:
  - `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_train_2023_2024.csv`
  - `3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_test_2025.csv`
- 전체 공통 스테이션 station-hour long-format:
  - `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_train_2023_2024.csv`
  - `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_test_2025.csv`
- 전체 공통 스테이션 station-hour 실험 관리:
  - `works/06_prediction_long_full/README.md`

## 7. Phase 4. ML 베이스라인 구축

목표: 기본 성능을 확인할 수 있는 예측 모델 파이프라인을 만든다.

### 체크리스트

- [x] 베이스라인 데이터셋 생성
- [x] train/validation/test 분리 전략 확정
- [x] 기준선 모델(baseline) 1개 이상 학습
- [x] 트리 기반 모델 1개 이상 학습
- [x] 평가 지표 계산
- [x] 피처 중요도(feature importance) 또는 해석 자료 생성
- [x] 2025 테스트 평가 결과 정리
- [x] 전체 161개 스테이션 `station-hour` 기준선 모델(baseline) 1차 학습
- [ ] 오류 사례 분석
  - 여기서 `오류 상위 스테이션`은 스테이션별 `MAE` 또는 `RMSE`가 큰 순서대로 정렬했을 때 상위에 오는, 즉 모델이 특히 잘 못 맞추는 스테이션을 뜻함
- [ ] 운영자용 재배치 판단 지표 초안 정의
- [ ] 일반 사용자용 `예상 잔여 자전거 수` 계산 로직 초안 정의
- [x] 실시간 따릉이 API 입력 스키마 1차 확인
- [x] 실시간 API 매핑 테이블 및 예외 처리 규칙 1차 정리
- [ ] 실시간 재고와 예측 수요 결합 방식 정의

### 완료 기준 점검

- [x] 최소 2개 모델 결과 비교표 존재
- [x] 2025 테스트셋 결과가 정리됨
- [x] 베이스라인 대비 개선 여부가 보임

### 현재 판단

- `LinearRegression`과 `LightGBM` 2개 모델의 기준선 모델(baseline) 비교 완료
- 연 단위 time-based validation(`Train=2023`, `Validation=2024`)과 2025 테스트셋 평가 완료
- `LightGBM`이 현재 기준선 모델(baseline) 우세 모델로 확인됨
- 대표 대여소 `station-hour` 실험에서는 `LightGBM_RMSE(RMSE 기준 LightGBM)`가 2025 테스트 기준 우세 모델로 확인됨
- 대표 대여소 `station-hour` 실험의 설명 근거 차트와 그룹/스테이션 오류 요약표를 추가 생성함
- 전체 161개 스테이션 `station-hour` 기준선 모델(baseline)에서는 `LightGBM_RMSE_Full(전체 스테이션 RMSE 기준 LightGBM)`이 validation RMSE `0.9735`, test RMSE `0.8624`를 기록함
- 전체 161개 스테이션 `station-hour` 학습 목표 함수(objective) 비교에서도 `LightGBM_RMSE_Full(전체 스테이션 RMSE 기준 LightGBM)`이 `LightGBM_Poisson_Full(전체 스테이션 Poisson 기준 LightGBM)`보다 우세함
- 전체 161개 스테이션 `station-hour`는 대표 대여소 실험과 분리된 별도 경로에서 관리하기로 확정
- 대표 대여소 단계는 군집별 최적화 전의 탐색/설명 단계이며, 다음 ML 고도화는 군집별 축소 피처 조합(subset) 실험으로 넘어가야 함
- 팀원 분업 실험을 위해 대표 대여소 15개 `5개 군집 x 3개 대여소` 기준 공통 전처리·validation·test·평가 규칙 문서를 별도로 고정함
- 팀원 분업 실험을 바로 시작할 수 있도록 `works/05_prediction_long`에 공통 노트북 템플릿을 추가함
- `2024-01-01` 날씨 누락 원천 파일을 `Open-Meteo Archive API`로 다시 받아 정정했고, 대표 대여소 학습 CSV와 전체 스테이션 `full_data` 학습 CSV를 재생성해 해당 날짜 날씨 결측을 제거함
- `works/06_prediction_long_full` 실험 노트북도 새 원본 기준으로 재실행해 데이터-실험 기준을 일치시킴
- 팀원 참여가 지연될 경우를 대비해 `works/05_prediction_long/cheng80/` 아래 군집별 대리 실험 폴더 5개와 사전 설정 노트북을 준비함
- `cheng80` 루트에는 결과 취합 CSV 템플릿, 결과 비교 문서, 2차 실험 판단 기준 문서를 추가해 후속 분석 준비를 완료함
- `cheng80` 대리 실험 기준 5개 군집 모두 `LightGBM_RMSE(RMSE 기준 LightGBM)`가 validation 우세 모델로 확인되었고, 현재 가장 어려운 군집은 `cluster01(아침 도착 업무 집중형)`으로 해석됨
- 팀 공용 사용을 위해 `3조 공유폴더/대표대여소_예측데이터_15개/second_round_data/` 경로에 기본 long 데이터 + 정적 교통/환경/POI + 공통 후보 파생 피처를 합친 2차 실험용 통합 피처모음 CSV를 train/test로 생성함
- `cheng80` 2차 실험 기준 5개 군집 모두 test RMSE가 소폭 개선되었고, 개선폭은 `cluster01`이 가장 컸다
- `cluster01` 3차 심화 실험에서는 `LightGBM_Poisson(Poisson 기준 LightGBM)`이 test RMSE `1.3189`로 1차/2차보다 더 개선되어, 군집별 심화 최적화 사례로 사용할 수 있게 됨
- 이어진 `cluster01` 축소 피처 조합(subset) 실험에서는 `subset_a_commute_transit(출근-교통 중심 조합) + LightGBM_Poisson(Poisson 기준 LightGBM)`이 test RMSE `1.3108`로 3차보다 더 개선되어, `출근 피크 + 교통 접근성` 중심 compact custom subset 후보가 확보됨
- 이어진 `cluster02` 축소 피처 조합(subset) 재검증에서는 축소 피처 조합(subset)보다 `subset_d_current_compact_best(현재 최적 축소 조합) + LightGBM_Poisson(Poisson 기준 LightGBM)`이 test RMSE `0.7990`으로 더 좋아져, `생활 리듬 + 주거형 입지` 축을 유지한 학습 목표 함수(objective) 전환 후보가 확보됨
- 대표 대여소 15개 raw/2차 데이터는 GitHub 대용량 제한을 피하기 위해 `3조 공유폴더/대표대여소_예측데이터_15개/` 아래로 이동하고, 노트북/문서 참조 경로를 모두 해당 공유폴더 기준으로 정리함
- `cheng80/01_ddri_api_verification.ipynb` 기준으로 공식 실시간 API 검증 범위를 `OA-15493 bikeList`로 단순화했고, 비공식 `bikeseoul` 검증은 제외함
- `OA-15493 bikeList`는 현재 `1~1000`, `1001~2000`, `2001~3000` 범위까지 응답이 확인되었고, `3001~`부터는 데이터가 없었다
- 명세서상 `stationId` 선택 파라미터가 있으나, 현재 검증한 호출 형식에서는 실제 필터로 동작하지 않았다
- 따라서 현재 실시간 수집 전략은 `서울 전체 bikeList 페이지 조회 -> 강남/대상 station_id 로컬 필터링`으로 고정한다
- 전체 161개 서비스 대상 스테이션 기준 공식 실시간 `bikeList` 매칭은 `158/161`이었고, 누락 스테이션은 `2314`, `2323`, `3628`이었다
- 위 3개는 `tbCycleStationInfo`, `bikeStationMaster`, 강남구 연도별 대여소 정보에는 존재하지만 `bikeList`에는 없어 `실시간 비노출 / 비활성 후보`로 해석한다
- 추가 호출 절감을 위해 `cheng80/api_output/ddri_full161_station_api_mapping_table.csv`와 `cheng80/api_output/ddri_station_id_api_lookup.csv`를 생성해 `numeric station_id ↔ ST-xxxx` 매핑과 운영 상태를 고정했다
- 전체 161개 스테이션 오류표와 대표 15개 목록을 대조한 결과, 전체 상위 오류 Top20 중 대표 15개에 포함되는 스테이션은 `2377`, `2348` 2개뿐이었다
- 반면 대표 15개 내부 오류 순위는 이미 별도로 정리되어 있으므로, 다음 오류 분석은 `대표 15개 우선 -> 겹치는 고오류 스테이션 확인 -> 전체 161개 확장` 순서로 진행하는 것이 합리적이다
- 대표 15개 상위 오류 5개(`2377`, `2348`, `4917`, `2328`, `2359`)의 시간대 패턴을 추가로 정리한 결과, `2377`·`2348`는 `16~19시` 저녁 피크, `4917`은 `05~08시` 아침 시간대, `2328`은 `08시·11시·16~18시`, `2359`는 `08시·16~18시·20시`가 핵심 확인 구간으로 나타났다
- 상위 오류 5개를 군집별 보강 피처 후보와 연결한 결과, 다음 축소 피처 조합(subset) 실험 우선순위는 `cluster01 -> cluster02 -> cluster00 -> cluster04` 순으로 정리되었고 `cluster03`은 이번 대표 오류 기준에서는 후순위로 둔다
- 전체 161개 확장 오류 분석에서는 Top20 중 `rep15`와 겹치는 스테이션이 여전히 `2377`, `2348` 2개뿐이었고, Top20의 `19/20`이 평균적으로 `over_predict` 방향이었다
- 전체 Top20 개수 기준으로는 `cluster00` 7개, `cluster02` 6개, `cluster03` 5개 순이었고, 군집 크기 대비 집중도는 `cluster02`가 상대적으로 더 높게 나타났다(`concentration_ratio 1.56`)
- 전체 Top5 시간대 패턴 재생성 결과 `2335`, `2377`, `2348`은 `17~19시` 저녁 피크 오차가 두드러졌고, `2404`, `2405`는 `08시` 아침 시간대 오차가 크게 나타났다
- 따라서 전체 161개 후속 해석은 `cluster00/cluster01`의 저녁 피크 구간과 `cluster02`의 아침 이동 구간을 우선 확인하는 방향으로 좁힐 수 있다
- `161개` 전체에 `cluster`별 partial routing(부분 군집 분기 적용)을 적용한 결과 validation RMSE는 `0.9687`로 단일 full model(전체 단일 모델, `0.9728`)보다 소폭 좋아졌지만, test RMSE는 `0.8673`으로 단일 full model(전체 단일 모델, `0.8620`)보다 나빠졌다
- 즉 현재 `full_data`만으로는 군집별 권장안을 부분 반영한 routing(군집 분기 적용)이 일반화 단계에서 아직 우세하지 않았고, 정적 입지 피처 없이 학습 목표 함수(objective)와 일부 시간 파생 피처만으로는 운영 기본안을 대체하기 어렵다고 본다
- 이후 `161개` 정적 피처를 `poi + environment` 원천에서 `161/161` 완전 매칭으로 복원했고, `static enriched single model(정적 피처 보강 단일 모델)`은 test RMSE `0.8620`으로 원본 full baseline(전체 단일 기준선 모델, `0.8624`)보다 소폭 개선됐다
- 반면 `static enriched routing model(정적 피처 보강 군집 분기 모델)`은 validation RMSE `0.9690`으로 좋아졌지만 test RMSE `0.8681`로 여전히 열세였으므로, 현재 단계에서는 `군집 라우팅(routing)`보다 `정적 피처를 붙인 단일 full model(전체 단일 모델)`이 더 현실적인 운영 기본안에 가깝다
- 같은 `static enriched single model(정적 피처 보강 단일 모델)` 위에 `rain_x_commute(비-출퇴근 결합 피처)`, `rain_x_night(비-야간 결합 피처)`, `precipitation_x_commute(강수량-출퇴근 결합 피처)` 같은 weather interaction(날씨 상호작용 피처)을 추가한 결과, validation RMSE `0.9701`, test RMSE `0.8604`로 다시 소폭 개선됐다
- 따라서 현재 `161개` 기준 가장 유력한 운영 기본안은 `static enriched single model + weather interaction(정적 피처 보강 단일 모델 + 날씨 상호작용 피처)` 조합이며, 다음 후속 실험은 이 기준선 위의 세부 weighting(가중치) 또는 interaction(상호작용 피처) 조정으로 두는 것이 합리적이다
- 이어서 `weather_full(전체 날씨 상호작용 조합)` 기준 `sample weighting(표본 가중치)`을 비교한 결과, `weather_full_weight_simple(단순 가중치)` test RMSE `0.8609`, `weather_full_weight_monthly(월별 가중치)` test RMSE `0.8605`로 모두 무가중치 `weather_full_no_weight(가중치 없음, 0.8604)`를 넘지 못했다
- 따라서 현재 단계에서는 `sample weighting(표본 가중치)`보다 `weather interaction(날씨 상호작용 피처)` 자체가 더 유효했고, 운영 기준선은 계속 `static enriched + weather_full interaction(정적 피처 보강 + 전체 날씨 상호작용 조합)`으로 유지한다
- 마지막으로 `15개` 군집별 최종 권장 피처에 `weather_full interaction(전체 날씨 상호작용 조합)`까지 그대로 얹은 `exact routed + weather_full(정확 군집 분기 + 전체 날씨 상호작용 조합)`을 `161개` 전체에 적용했지만, validation RMSE는 `0.9682`로 다소 좋아진 반면 test RMSE는 `0.8673`으로 다시 `static enriched + weather_full interaction(0.8604)`보다 나빠졌다
- 따라서 `161개` 운영 모델에서는 군집별 routing(군집 분기 적용)보다 `단일 full model + 정적 피처 + weather_full interaction(전체 단일 모델 + 정적 피처 + 전체 날씨 상호작용 조합)` 조합을 유지하는 편이 더 안정적이며, `15개` 군집별 권장안은 운영 모델 자체보다 해석과 피처 발굴 근거로 두는 것이 맞다
- 다만 서비스 출력 로직 자체는 아직 확정되지 않았으므로, API 검증/매핑 정리까지 완료하고 `예상 잔여 자전거 수` 후처리 정의는 다음 단계로 미룬다
- 따라서 Phase 4는 `베이스라인 1차 완료, 후속 고도화 및 오류 분석 미완료` 상태로 본다

## 8. Phase 5. 웹/서비스 설계 문서화

목표: 분석 결과를 웹에서 보여주기 위한 구조를 문서화한다.

### 체크리스트

- [ ] 사용자 시나리오 정의
- [ ] API 입력/출력 스키마 초안 작성
- [ ] ERD 또는 데이터 구조도 작성
- [ ] 아키텍처 다이어그램 작성
- [ ] Flutter 웹 화면 구성 초안 작성
- [ ] 지도 표시 항목 정의
- [ ] 예측 결과 갱신 방식 정의
- [ ] 운영자 화면과 일반 사용자 화면 역할 분리 정의
- [ ] 일반 사용자 입력 정의
  - `station_id(or station_name)`, `date`, `hour`
- [ ] 일반 사용자 출력 정의
  - `예상 잔여 자전거 수` 또는 `대여 가능 여부`
- [ ] 실시간 API 호출 주기와 캐시 정책 정의

### 현재 판단

- 기획 문서 레벨 설명은 있으나, 구현 기준의 웹 설계 문서는 아직 부족하다

## 9. Phase 6. 최종 보고서 및 영상 산출물 정리

목표: 발표 가능한 형태로 모든 결과를 정리한다.

### 체크리스트

- [ ] 분석 보고서 초안 작성
- [x] 군집화 결과 요약 슬라이드 작성
- [ ] ML 결과 요약 슬라이드 작성
- [ ] 웹 설계 요약 슬라이드 작성
- [ ] 시연 시나리오 작성
- [ ] 동영상 구성안 작성
- [ ] 최종 파일 목록 점검

### 현재 판단

- 군집화 발표 자료는 상당 부분 정리됨
- 현재 `works/04_presentation`에는 군집화 발표 자료만 유지함
- 기존 임시 프로젝트 발표 자료는 제거했으며, 예측/웹/최종 제출물 관점의 종합 발표 자료는 이후 최종 결과 기준으로 새로 작성해야 함

## 10. 바로 다음 실행 순서

현재는 `z_final_delivery` 본작업보다 `works` 안의 잔여 실험과 정리 마감을 먼저 끝내는 것이 맞다.

다음 작업은 아래 순서로 진행하는 것이 합리적이다.

1. `works` 구조 정리를 현재 수준에서 일단 마감하고, README/정본/보조 경계를 더 흔들지 않는다
2. `cluster00`, `cluster02`에 상위 오류가 몰리는지 추가 확인한다
3. `CatBoost(범주형 처리에 강한 부스팅 모델)`는 축소 실험 또는 경량 파라미터 조건으로 별도 검토한다
4. 수요 예측값을 `재배치 판단 지표`와 `예상 잔여 자전거 수`로 변환하는 후처리 규칙 초안을 작성한다
5. 운영자 화면 / 일반 사용자 화면을 분리한 API·화면 단위 정의로 넘어간다
6. 예측 파트 결과를 발표 문서에 반영한다
7. 위 결과가 안정되면 그때 `z_final_delivery`로 필요한 데이터와 근거만 옮긴다

## 11. 현재 점검 결론

마스터 플랜 기준 현재 상태는 아래와 같다.

- Phase 1 완료
- Phase 2 완료
- Phase 3 완료
- Phase 4 미완료
- Phase 5 미완료
- Phase 6 미완료

즉, 현재 프로젝트는 `군집화 완료 + 예측 데이터셋 준비 완료 + 실시간 API 1차 검증/매핑 정리 완료` 단계까지 왔고, 이제 핵심 남은 일은 아래 두 갈래다.

- 분석/ML: 오류 분석, 군집별 고도화, 재배치·잔여자전거 해석 로직 정리
- 서비스 설계: 운영자용 재배치 화면과 일반 사용자용 잔여 자전거 예측 화면 정의
