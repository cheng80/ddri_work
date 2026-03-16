# DDRI cluster01 subset experiment design

작성일: 2026-03-15  
목적: `cluster01` 아침 도착 업무 집중형의 다음 `축소 피처 조합(subset)` 실험을 바로 실행 가능한 수준으로 고정한다.

## 0. 용어 정리

- `subset`:
  - 전체 후보 피처 중 일부만 골라 만든 `축소 피처 조합`
- `objective`:
  - 모델이 무엇을 더 잘 맞추도록 학습할지 정하는 `학습 목표 함수`

## 1. 실험 목표

현재 `cluster01`은 대표 15개 군집 중 가장 어려운 군집이면서, 2차와 3차에서 개선폭이 가장 분명했다.

따라서 다음 실험 목표는 아래처럼 잡는다.

1. `cluster01`에 대해 `LightGBM_Poisson` 우세가 축소 피처 조합 조건에서도 유지되는지 확인
2. 모든 후보 피처를 다 쓰는 방식이 아니라, `핵심 피처 축소 조합(subset)`만으로도 성능이 유지되거나 개선되는지 확인
3. 최종적으로는 `적은 피처 수 + 해석 가능한 군집 전용 모델` 후보를 확보

## 2. 현재 기준선

비교 기준은 아래 3개다.

1. 1차 baseline
   - 노트북: `01_cluster_modeling.ipynb`
   - 모델: `LightGBM_RMSE`
   - test RMSE: `1.3462`
2. 2차 피처 보강
   - 노트북: `02_cluster_modeling_second_round.ipynb`
   - 모델: `LightGBM_RMSE`
   - test RMSE: `1.3324`
3. 3차 심화
   - 노트북: `03_cluster_modeling_third_round.ipynb`
   - 모델: `LightGBM_Poisson`
   - test RMSE: `1.3189`

다음 `축소 피처 조합(subset)` 실험은 반드시 위 3개와 같은 방식으로 비교한다.

## 3. 고정 조건

- 대상 군집: `cluster01`
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
  - 기본 모델은 `LightGBM`
  - 학습 목표 함수(objective)는 기본적으로 `Poisson objective`
  - 필요 시 대조군으로 `RMSE objective` 1개 유지

## 4. 축소 피처 조합(subset) 설계

### 4.1 핵심 유지 피처

다음 피처는 `cluster01` 고정 핵심 피처로 본다.

- `is_commute_hour`(출퇴근 시간대 여부)
- `commute_morning_flag`(아침 출근 시간대 여부)
- `commute_evening_flag`(저녁 퇴근 시간대 여부)
- `is_after_holiday`(공휴일 다음 날 여부)
- `subway_distance_m`(가까운 지하철역까지 거리)
- `bus_stop_count_300m`(300m 안 버스정류장 수)
- `rolling_mean_6h`(최근 6시간 대여량 이동평균)
- `rolling_mean_12h`(최근 12시간 대여량 이동평균)
- `rolling_std_6h`(최근 6시간 대여량 이동표준편차)
- `rolling_std_12h`(최근 12시간 대여량 이동표준편차)
- `lag_48h`(48시간 전 같은 대여소 대여량)

### 4.2 비교할 축소 피처 조합 묶음

다음 3개 축소 피처 조합을 비교한다.

#### subset A. commute + transit

- `is_commute_hour`(출퇴근 시간대 여부)
- `commute_morning_flag`(아침 출근 시간대 여부)
- `commute_evening_flag`(저녁 퇴근 시간대 여부)
- `subway_distance_m`(가까운 지하철역까지 거리)
- `bus_stop_count_300m`(300m 안 버스정류장 수)

의도:
- 출근/퇴근 피크와 교통 접근성만으로도 핵심 패턴 설명이 되는지 확인

#### subset B. commute + transit + short trend

- subset A 전체
- `rolling_mean_6h`(최근 6시간 대여량 이동평균)
- `rolling_std_6h`(최근 6시간 대여량 이동표준편차)
- `lag_48h`(48시간 전 같은 대여소 대여량)

의도:
- 단기 추세를 붙였을 때 가장 가벼운 고성능 조합이 나오는지 확인

#### subset C. current best compact

- `is_commute_hour`(출퇴근 시간대 여부)
- `commute_morning_flag`(아침 출근 시간대 여부)
- `commute_evening_flag`(저녁 퇴근 시간대 여부)
- `is_after_holiday`(공휴일 다음 날 여부)
- `subway_distance_m`(가까운 지하철역까지 거리)
- `bus_stop_count_300m`(300m 안 버스정류장 수)
- `rolling_mean_6h`(최근 6시간 대여량 이동평균)
- `rolling_mean_12h`(최근 12시간 대여량 이동평균)
- `rolling_std_6h`(최근 6시간 대여량 이동표준편차)
- `rolling_std_12h`(최근 12시간 대여량 이동표준편차)
- `lag_48h`(48시간 전 같은 대여소 대여량)

의도:
- 현재 3차 심화 결과를 가장 잘 설명하는 축약형 후보

## 5. 실행 순서

실행 노트북:

- `05_cluster_modeling_subset_experiment.ipynb`

1. `03_cluster_modeling_third_round.ipynb`를 기준 복사본으로 사용
2. full feature 버전 `LightGBM_Poisson` 재확인
3. subset A 실행
4. subset B 실행
5. subset C 실행
6. 필요하면 각 축소 피처 조합에 대해 `LightGBM_RMSE` 대조군 1회 실행
7. 결과를 하나의 비교표로 정리

## 6. 채택 기준

- 최우선:
  - 기존 3차(`test RMSE 1.3189`)보다 같거나 더 좋은지
- 차선:
  - 성능 차이가 작다면 피처 수가 더 적은 축소 피처 조합 우선
- 제외:
  - validation만 좋고 test에서 다시 악화되는 경우
  - `MAE`, `R²`까지 함께 악화되는 경우

## 7. 기대 산출물

- 축소 피처 조합 비교표 1개
- 최종 채택 축소 피처 조합 1개
- `cluster01` 군집 전용 권장 피처 묶음
- 이후 `z_final_delivery`에 옮길 수 있는 요약 문장

## 8. 다음 연결

이 실험이 끝나면 바로 아래 순서로 연결한다.

1. `cluster01` 최종 축소 피처 조합 확정
2. `cluster02` 경량 subset 재검증 설계
3. 전체 161개 상위 오류 스테이션 확장 분석
