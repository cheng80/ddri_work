# DDRI 군집별 최종 권장안(Final Cluster Recommendation)

작성일: 2026-03-14  
최종 갱신일: 2026-03-15  
목적: 1차 baseline, 2차 추가 피처 실험, `cluster01` 3차 심화 및 `축소 피처 조합(subset)` 실험, `cluster02` 축소 피처 조합 재검증 결과를 바탕으로 현재 시점의 군집별 권장 모델과 적용 수준을 정리한다.

## 1. 결론 요약

현재 결과만으로는 `전 군집 완성형 커스텀 모델`이 확정됐다고 보기는 어렵다.  
다만 `군집별 커스텀 피처/모델 전략이 유효하다`는 근거는 확보되었다.

현재 권장 해석:

- 공통 운영 baseline은 `LightGBM_RMSE`
- 군집별 커스텀 고도화는 `cluster01`부터 우선 적용
- `cluster00`, `cluster02`, `cluster03`, `cluster04`는 2차 피처 보강안까지를 `군집별 커스텀 초안`으로 본다

## 2. 군집별 최종 권장표


| 군집 코드       | 군집명          | 현재 권장 모델           | 대표 확인 점수                                 | 권장 추가 피처 방향                   | 현재 판단                     | 적용 권장 수준                     |
| ----------- | ------------ | ------------------ | ---------------------------------------- | ----------------------------- | ------------------------- | ---------------------------- |
| `cluster00` | 업무/상업 혼합형    | `LightGBM_RMSE`    | RMSE `0.8085`, MAE `0.5403`, R² `0.3259` | 출퇴근, 상권, 교통 접근성               | 2차에서 아주 작은 개선 확인          | `공통 baseline 유지 + 선택적 피처 보강` |
| `cluster01` | 아침 도착 업무 집중형 | `LightGBM_Poisson` | RMSE `1.3108`, MAE `0.7711`, R² `0.6585` | 출근 피크, 교통 접근성 중심 `축소 피처 조합` | 2차, 3차, 축소 피처 조합 실험까지 연속 개선 확인 | `군집별 커스텀 모델 우선 적용 후보`        |
| `cluster02` | 주거 도착형       | `LightGBM_Poisson` | RMSE `0.7990`, MAE `0.4997`, R² `0.5108` | 야간, 주말, 공휴일 전날, 주거형 입지 compact 유지 | 축소 피처 조합 축소보다 `학습 목표 함수(objective)` 전환에서 개선 확인 | `공통 baseline + compact custom 후보` |
| `cluster03` | 생활권 혼합형      | `LightGBM_RMSE`    | RMSE `0.6882`, MAE `0.4882`, R² `0.1848` | 점심, 상권, 생활편의 POI, 단기 추세       | RMSE는 낮지만 R²가 낮아 구조 보완 필요 | `추가 검토 대상`                   |
| `cluster04` | 외곽 주거형       | `LightGBM_RMSE`    | RMSE `0.7145`, MAE `0.4427`, R² `0.3811` | 야간, 외곽성, 지형, 교통 접근성           | 2차 개선폭이 매우 작음             | `공통 baseline 우선`             |


## 2.1 1차에서 3차까지의 진행 해석

중간 요약 문서들을 합치면 현재 진행 해석은 아래처럼 정리된다.

- 1차 결과 기준:
  - 다섯 군집 모두 `LightGBM_RMSE`가 validation 우세 모델이었다
  - 가장 어려운 군집은 `cluster01`
  - `cluster03`은 RMSE는 낮지만 R²가 낮아 구조 보완 후보로 읽혔다
- 2차 결과 기준:
  - 다섯 군집 모두 test RMSE가 소폭 개선되었다
  - 가장 큰 개선은 `cluster01`
  - 나머지 군집은 방향성은 좋지만 대부분 `경량 개선` 수준이었다
- 3차 결과 기준:
  - 전 군집 확장이 아니라 `cluster01` 심화 사례만 추가로 수행했다
  - `cluster01`에서는 `LightGBM_Poisson`이 최종 우세 모델로 바뀌었다
- 축소 피처 조합 결과 기준:
  - `cluster01` 축소 피처 조합 실험에서 `subset_a_commute_transit + LightGBM_Poisson`이 최종 우세 조합으로 확인되었다
  - 기존 3차보다 더 적은 피처로 test RMSE가 추가 개선되었다
  - `cluster02` 축소 피처 조합 재검증에서는 더 줄인 조합보다 `subset_d_current_compact_best + LightGBM_Poisson`이 최종 우세 조합으로 확인되었다
  - 즉 `cluster02`는 피처 축소보다 현재 compact 피처 유지 + `학습 목표 함수(objective)` 전환이 더 유효했다

즉 현재 결론은 `전 군집 완성형 커스텀 모델 확정`이 아니라, `공통 baseline 위에서 cluster01 compact subset 최적화와 cluster02 objective 전환 가능성이 확인된 상태`다.

## 2.2 2차 및 후속 실험 판단 기준

중간 판단 문서의 기준을 현재 권장안 기준으로 다시 쓰면 아래와 같다.

- test RMSE가 다른 군집보다 높으면 후속 실험 우선순위를 높인다
- validation 대비 test 괴리가 크면 일반화 불안정 후보로 본다
- RMSE가 낮아도 R²가 낮으면 패턴 설명 보완 후보로 본다
- 추가 피처로 개선되더라도 폭이 매우 작으면 `선택적 보강` 수준으로만 해석한다
- 후속 실험은 전 군집 일괄 확장이 아니라 `가장 어려운 군집 우선` 원칙을 유지한다

현재 이 기준을 적용한 직접 우선순위는 아래와 같다.

1. `cluster01`
2. `cluster02`
3. `cluster00`
4. `cluster04`

`cluster03`은 상위 오류 스테이션 직접 포함 기준에서는 후순위지만, 낮은 `R²` 때문에 별도 구조 보완 후보로 계속 관리한다.

## 3. 군집별 상세 판단

### 3.1 `cluster00` 업무/상업 혼합형

- 1차 test RMSE: `0.8113`
- 1차 test MAE: `0.5439`
- 2차 test RMSE: `0.8085`
- 2차 test MAE: `0.5403`
- 해석:
  - 출퇴근과 상권 피처를 보강했을 때 방향성 있는 개선은 있었다.
  - 다만 개선폭은 아주 작아, 별도 전용 모델을 강하게 주장할 수준은 아니다.
- 현재 권장:
  - `LightGBM_RMSE` 유지
  - `is_commute_hour`(출퇴근 시간대 여부), `subway_distance_m`(가까운 지하철역까지 거리), `bus_stop_count_300m`(300m 안 버스정류장 수), `restaurant_count_300m`(300m 안 음식점 수), `cafe_count_300m`(300m 안 카페 수), `rolling_mean_6h`(최근 6시간 대여량 이동평균) 정도의 보강안을 선택적으로 적용

### 3.2 `cluster01` 아침 도착 업무 집중형

- 1차 test RMSE: `1.3462`
- 1차 test MAE: `0.8042`
- 2차 test RMSE: `1.3324`
- 2차 test MAE: `0.7868`
- 3차 test RMSE: `1.3189`
- 3차 test MAE: `0.7745`
- 축소 피처 조합 test RMSE: `1.3108`
- 축소 피처 조합 test MAE: `0.7711`
- 해석:
  - 다섯 군집 중 가장 어려운 군집이지만, 동시에 추가 피처와 목적함수 변경에 가장 잘 반응했다.
  - 3차에서 `LightGBM_Poisson`이 최종 우세 모델로 바뀌었다.
  - 이어서 축소 피처 조합 실험에서는 더 적은 피처를 쓴 `subset_a_commute_transit` 조합이 기존 3차보다 test 성능도 더 좋았다.
- 현재 권장:
  - `LightGBM_Poisson`을 군집별 우선 커스텀 모델 후보로 채택
  - 현재 최우선 권장 subset은 `subset_a_commute_transit`
  - 핵심 유지 피처:
    - `is_commute_hour`(출퇴근 시간대 여부)
    - `commute_morning_flag`(아침 출근 시간대 여부)
    - `commute_evening_flag`(저녁 퇴근 시간대 여부)
    - `subway_distance_m`(가까운 지하철역까지 거리)
    - `bus_stop_count_300m`(300m 안 버스정류장 수)
  - 즉 `cluster01`은 `출근 피크 + 교통 접근성`만으로도 가장 강한 설명 축이 유지된다고 해석한다

### 3.3 `cluster02` 주거 도착형

- 1차 test RMSE: `0.8088`
- 1차 test MAE: `0.5059`
- 2차 test RMSE: `0.8059`
- 2차 test MAE: `0.5053`
- 축소 피처 조합 재검증 validation RMSE: `0.8109`
- 축소 피처 조합 재검증 test RMSE: `0.7990`
- 축소 피처 조합 재검증 test MAE: `0.4997`
- 해석:
  - 원래도 비교적 안정적이었고, 2차 보강 후에도 작지만 일관된 개선이 있었다.
  - 이번 재검증에서는 subset A/B/C처럼 더 적은 피처 묶음은 2차 기준을 넘지 못했다.
  - 대신 `subset_d_current_compact_best + LightGBM_Poisson`이 test RMSE `0.7990`으로 기존 2차보다 더 개선되었다.
- 현재 권장:
  - `LightGBM_Poisson`을 현재 우세 후보로 갱신
  - 축소 subset보다는 현재 compact 피처 묶음을 유지
  - 핵심 유지 피처:
    - `is_night_hour`(야간 시간대 여부)
    - `is_weekend`(주말 여부)
    - `is_holiday_eve`(공휴일 전날 여부)
    - `heavy_rain_flag`(강한 비 여부)
    - `station_elevation_m`(대여소 표고)
    - `bus_stop_count_300m`(300m 안 버스정류장 수)
  - 즉 `cluster02`는 `생활 리듬 + 주거형 입지` 축을 유지한 상태에서 `학습 목표 함수(objective)` 전환 효과를 보는 군집으로 해석한다

### 3.4 `cluster03` 생활권 혼합형

- 1차 test RMSE: `0.6901`
- 1차 test MAE: `0.4928`
- 2차 test RMSE: `0.6882`
- 2차 test MAE: `0.4882`
- 해석:
  - RMSE 자체는 낮지만 R²가 낮다.
  - 즉 평균 오차는 작아도 패턴 설명력이 충분하다고 보긴 어렵다.
  - 생활권/상권 관련 정적 피처를 더 정교화할 여지가 있다.
- 현재 권장:
  - 현재는 `LightGBM_RMSE` 유지
  - `restaurant_count_300m`(300m 안 음식점 수), `cafe_count_300m`(300m 안 카페 수), `convenience_store_count_300m`(300m 안 편의점 수), `is_lunch_hour`(점심 시간대 여부), `rolling_mean_6h`(최근 6시간 대여량 이동평균) 중심으로 유지
  - 후속 보완 후보 군집으로 분류

### 3.5 `cluster04` 외곽 주거형

- 1차 test RMSE: `0.7160`
- 1차 test MAE: `0.4425`
- 2차 test RMSE: `0.7145`
- 2차 test MAE: `0.4427`
- 해석:
  - 방향은 개선이지만 폭이 매우 작다.
  - 현재 지형/외곽성 피처가 큰 차이를 만들었다고 해석하긴 어렵다.
- 현재 권장:
  - `LightGBM_RMSE` 공통 baseline 우선
  - 필요할 때만 `station_elevation_m`(대여소 표고), `elevation_diff_nearest_subway_m`(가까운 지하철역과의 표고 차이), `distance_naturepark_m`(자연공원까지 거리), `distance_river_boundary_m`(하천 경계까지 거리), `bus_stop_count_300m`(300m 안 버스정류장 수) 보강

## 4. 최종 적용 전략

현재 시점의 가장 현실적인 적용 전략은 아래와 같다.

1. 공통 기본 모델은 여전히 `LightGBM_RMSE`로 유지한다.
2. `cluster01`은 별도 군집 커스텀 모델(`subset_a_commute_transit + LightGBM_Poisson`) 적용 후보로 분리한다.
3. `cluster02`는 현재 compact 피처 묶음을 유지한 `LightGBM_Poisson` 적용 후보로 별도 관리한다.
4. `cluster00`, `cluster03`, `cluster04`는 2차 피처 보강안을 유지하되, 보고서에서는 `군집별 커스텀 초안`으로 표현한다.
5. 전 군집 완성형 커스텀 모델 체계라고 주장하기보다는, `군집별 최적화 가능성 확인 + cluster01 compact subset 사례 + cluster02 objective 전환 사례`로 정리한다.

## 5. 예측력은 어떤 점수로 확인하나

현재 군집별 권장안 판단에서는 아래 3개 지표를 함께 본다.

- `RMSE`
  - 최우선 선택 지표
  - 큰 오차를 더 민감하게 반영하므로 모델 선택 기준으로 가장 먼저 본다
- `MAE`
  - 평균적으로 몇 대 차이 나는지 보여주는 직관 지표
  - 운영자/사용자 설명 문구에 쓰기 좋다
- `R²`
  - 패턴 설명력 보조 지표
  - RMSE는 낮지만 구조 설명력이 낮은 군집을 따로 읽을 때 사용한다

현재 해석 원칙:

1. 모델 우열은 먼저 `RMSE`로 본다
2. 평균 체감 오차는 `MAE`로 읽는다
3. 패턴 설명력은 `R²`로 보조 해석한다

## 6. 보고서용 표현 권장안

- 권장 표현:
  - `군집별 커스텀 모델 가능성 확인`
  - `군집별 맞춤 피처 보강의 유효성 검증`
  - `cluster01 compact subset 최적화 사례 확보`
  - `cluster02 objective 전환 기반 경량 커스텀 사례 확보`
- 아직 과한 표현:
  - `전 군집 최적 모델 확정`
  - `완성형 군집별 운영 모델 구축 완료`

## 7. 바로 참고할 문서

| 구분 | 참고 문서 | 재생성 노트북 | 집계/결과 CSV |
|---|---|---|---|
| 전체 결과 집계 | `archive_docs/01_ddri_cluster_result_collection.md` | `summary_aggregation/11_ddri_cluster_result_collection.ipynb` | `summary_aggregation/output/data/ddri_cluster_model_metrics_collection_template.csv` |
| 2차 비교 요약 | `archive_docs/04_ddri_second_round_result_summary.md` | `summary_aggregation/12_ddri_cluster_second_round_comparison.ipynb` | `summary_aggregation/output/data/ddri_cluster_second_round_comparison_summary.csv` |
| cluster01 3차 진행 | `archive_docs/05_ddri_cluster01_third_round_summary.md` | `summary_aggregation/13_ddri_cluster01_third_round_progression.ipynb` | `summary_aggregation/output/data/cluster01_third_round_progression_summary.csv` |
| 전체 실험 종합 | `archive_docs/06_ddri_cluster_experiment_overall_summary.md` | - | - |
| cluster01 subset 설계 | `cluster01/04_ddri_cluster01_subset_experiment_design.md` | `cluster01/05_cluster_modeling_subset_experiment.ipynb` | `output/team_cluster_subset_outputs/ddri_아침_도착_업무_집중형_subset_experiment_model_metrics.csv` |
| cluster02 subset 재검증 | `cluster02/03_ddri_cluster02_subset_recheck_design.md` | `cluster02/04_cluster_modeling_subset_recheck.ipynb` | `output/team_cluster_subset_outputs/ddri_주거_도착형_subset_recheck_model_metrics.csv` |
