# DDRI cluster02 subset recheck design

작성일: 2026-03-15  
목적: `cluster02` 주거 도착형의 경량 subset 재검증 실험 범위를 바로 실행 가능한 수준으로 고정한다.

## 1. 실험 목표

`cluster02`는 1차에서 이미 비교적 안정적이었고, 2차 피처 보강 후에도 작지만 일관된 개선이 있었다.

따라서 다음 실험 목표는 아래처럼 잡는다.

1. `cluster02`에서 2차 보강안 전체를 계속 유지할 필요가 있는지 확인
2. `주거형 아침 이동`을 설명하는 최소 subset만으로도 현재 성능을 유지할 수 있는지 확인
3. 최종적으로는 `경량 subset + LightGBM_RMSE` 조합이 가능한지 판단

## 2. 현재 기준선

비교 기준은 아래 2개다.

1. 1차 baseline
   - 노트북: `01_cluster_modeling.ipynb`
   - 모델: `LightGBM_RMSE`
   - test RMSE: `0.8088`
2. 2차 피처 보강
   - 노트북: `02_cluster_modeling_second_round.ipynb`
   - 모델: `LightGBM_RMSE`
   - test RMSE: `0.8059`

다음 재검증은 반드시 위 2개와 같은 방식으로 비교한다.

## 3. 고정 조건

- 대상 군집: `cluster02`
- 검증 전략:
  - `Train=2023`
  - `Validation=2024`
  - `Final Train=2023+2024`
  - `Test=2025`
- 비교 지표:
  - `RMSE`
  - `MAE`
  - `R²`
- 최우선 선택 지표:
  - `test RMSE`
- 비교 대상 모델:
  - 기본은 `LightGBM_RMSE`
  - 필요 시 `LightGBM_Poisson`은 참고용 1회만 확인

## 4. subset 설계

### 4.1 현재 권장 피처

현재 `cluster02`에서 유지 가치가 높다고 보는 피처는 아래와 같다.

- `is_night_hour`
- `is_weekend`
- `is_holiday_eve`
- `heavy_rain_flag`
- `station_elevation_m`
- `bus_stop_count_300m`

### 4.2 비교할 subset 묶음

#### subset A. living pattern core

- `is_night_hour`
- `is_weekend`
- `is_holiday_eve`

의도:
- 주거형 생활 리듬만으로 핵심 설명이 되는지 확인

#### subset B. living pattern + rain

- subset A 전체
- `heavy_rain_flag`

의도:
- 기상 이벤트가 실제로 추가 설명력을 주는지 확인

#### subset C. living pattern + location

- subset A 전체
- `station_elevation_m`
- `bus_stop_count_300m`

의도:
- 주거형 입지 특성이 성능 유지에 더 중요한지 확인

#### subset D. current compact best

- `is_night_hour`
- `is_weekend`
- `is_holiday_eve`
- `heavy_rain_flag`
- `station_elevation_m`
- `bus_stop_count_300m`

의도:
- 현재 2차 보강안의 축약형 후보를 그대로 재검증

## 5. 실행 순서

1. `02_cluster_modeling_second_round.ipynb`를 기준 복사본으로 사용
2. full feature 기준 `LightGBM_RMSE` 재확인
3. subset A 실행
4. subset B 실행
5. subset C 실행
6. subset D 실행
7. 필요 시 `LightGBM_Poisson` 참고 비교 1회
8. 결과를 하나의 비교표로 정리

## 6. 채택 기준

- 최우선:
  - 기존 2차(`test RMSE 0.8059`)보다 같거나 더 좋은지
- 차선:
  - 성능 차이가 작다면 피처 수가 더 적은 subset 우선
- 제외:
  - validation은 좋지만 test에서 악화되는 경우
  - `MAE`, `R²`까지 함께 악화되는 경우

## 7. 기대 산출물

- subset 비교표 1개
- 최종 채택 subset 1개
- `cluster02` 경량 유지 피처 묶음
- 이후 최종 통합본에 넣을 요약 문장

## 8. 다음 연결

이 실험이 끝나면 바로 아래 순서로 연결한다.

1. `cluster02` 최종 subset 확정
2. 전체 161개 상위 오류 스테이션 확장 분석
3. 상위 오류 스테이션의 군집 집중 여부 확인
