# DDRI 학습 실험 종합 레포트 1차

작성일: 2026-03-17

## 1. 목적

`06_prediction_training/04_reference_docs`에 흩어진 현재 판단을 한 문서로 묶는다.

이번 종합 레포트는 아래를 한 번에 정리한다.

- 무샘플링 기준선
- 샘플링 1안 결과
- 가중치 2안 결과
- 군집 관련 해석
- 현재 시점의 우선순위

## 2. 현재 실험 기준

공통 학습 정책:

- train: `2023`
- validation: `2024`
- validation 기준 우세 모델 선택
- `2023+2024` 재학습
- test: `2025`

공통 지표:

- `RMSE`
- `MAE`
- `R²`

후보 모델:

- `LightGBM_RMSE`
- `CatBoost_RMSE`
- `StackingRegressor`
- `SoftVotingRegressor`

현재까지는 모든 주요 조합에서 `LightGBM_RMSE`가 우세했다.

## 3. 정본과 실험 위치

정본 입력:

- `canonical_data`

학습 실험 원칙:

- 정본은 유지
- 샘플링/가중치는 학습 단계에서만 비교
- 검증 `2024`, 테스트 `2025`는 원래 분할 유지

즉, `05_prediction_canonical`은 정본 생성,
`06_prediction_training`은 정본을 받은 뒤 학습 전략을 비교하는 경로다.

## 4. 무샘플링 기준선 요약

기준 문서:

- [01_ddri_no_sampling_baseline_cycle.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/01_ddri_no_sampling_baseline_cycle.md)
- [05_ddri_no_sampling_baseline_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/05_ddri_no_sampling_baseline_results_round1.md)

요약 결과:

| dataset | target | best model | valid RMSE | valid MAE | valid R² | test RMSE | test MAE | test R² |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| rep15 | bike_change_raw | LightGBM_RMSE | 0.381777 | 0.143463 | 0.933885 | 0.309620 | 0.121293 | 0.946012 |
| rep15 | bike_change_deseasonalized | LightGBM_RMSE | 0.372257 | 0.140486 | 0.925913 | 0.306413 | 0.118805 | 0.941617 |
| full161 | bike_change_raw | LightGBM_RMSE | 0.314080 | 0.129130 | 0.948969 | 0.263338 | 0.105791 | 0.955216 |
| full161 | bike_change_deseasonalized | LightGBM_RMSE | 0.309577 | 0.126492 | 0.946228 | 0.259210 | 0.104047 | 0.954493 |

1차 해석:

- 4개 조합 모두 `LightGBM_RMSE`가 우세
- `bike_change_deseasonalized`는 `RMSE`, `MAE` 기준 우세
- `bike_change_raw`는 `R²`가 약간 더 높게 유지되는 경향
- 현재 기준선 후보 타깃은 `bike_change_deseasonalized`가 1순위
- 이 결론은 군집 보정 후 다시 계산한 기준선에서도 유지됐다.

## 5. 샘플링 1안 요약

기준 문서:

- [02_ddri_temporal_sampling_policy_review.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/02_ddri_temporal_sampling_policy_review.md)
- [06_ddri_sampling_plan1_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/06_ddri_sampling_plan1_results_round1.md)

샘플링 1안 정의:

- `2023 train`만 대상
- 같은 `station_id`, 같은 `weekday` 안에서
- 일단위 24시간 프로파일을 비교
- 유사한 날짜는 대표일만 남기기

1차 실행 조건:

- dataset: `rep15`
- target: `bike_change_deseasonalized`
- `retain_ratio = 0.7`

결과:

- 행 수: `131,400 -> 93,600`
- 실제 유지율: `0.712329`
- validation RMSE: `0.375739`
- test RMSE: `0.305396`

해석:

- 행 수는 약 `28.8%` 줄었음
- validation은 무샘플링보다 불리
- test는 `RMSE`, `R²`가 약간 좋아졌지만 `MAE`는 약간 나빠짐
- 현재 설정만 보면 실익은 제한적임

현재 판단:

- 샘플링 1안은 작동은 정상적임
- 하지만 현재 기준선을 대체할 정도의 안정적 성능 이득은 없음

## 6. 가중치 2안 요약

기준 문서:

- [02_ddri_temporal_sampling_policy_review.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/02_ddri_temporal_sampling_policy_review.md)
- [07_ddri_sampling_plan2_weighting_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/07_ddri_sampling_plan2_weighting_results_round1.md)

가중치 2안 정의:

- 행은 삭제하지 않음
- `2023 train`에만 가중치 부여
- 같은 `station_id`, 같은 `weekday` 안에서
- 비슷한 일 패턴이 많이 반복될수록 가중치를 낮춤
- 기본 공식: `1 / sqrt(cluster_size)` 후 평균 1로 정규화

1차 실행 조건:

- dataset: `rep15`
- target: `bike_change_deseasonalized`
- `cluster_ratio = 0.7`

결과:

- 행 수: `131,400 -> 131,400` 유지
- weight min: `0.301225`
- weight mean: `1.000000`
- weight max: `1.241983`
- validation RMSE: `0.374683`
- test RMSE: `0.304924`

해석:

- 샘플링 1안보다 보수적이고 안정적
- validation은 무샘플링보다 약간 불리
- test는 `RMSE`, `R²`가 약간 좋아졌고 `MAE`는 약간 불리

현재 판단:

- 가중치 2안은 샘플링 1안보다 더 타당함
- 다만 개선 폭이 작아 아직 무샘플링을 대체한다고 보기 어려움

## 7. 군집 관련 판단

기준 문서:

- [08_ddri_cluster_consistency_issue.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/08_ddri_cluster_consistency_issue.md)
- [10_ddri_rep15_station_cluster_rematch.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/10_ddri_rep15_station_cluster_rematch.md)

중요한 정리:

- 대표 15개 기준 군집은 아래 Top3 구성이 맞다.
  - 업무/상업 혼합형: `4908`, `2328`, `4902`
  - 아침 도착 업무 집중형: `2377`, `2323`, `2348`
  - 주거 도착형: `2312`, `2354`, `4917`
  - 생활권 혼합형: `2321`, `2320`, `3616`
  - 외곽 주거형: `3643`, `2359`, `2392`
- 원천 `OLD_DATA`에서는 `rep15`, `full161` 모두 `train 2023-2024`와 `test 2025` 사이에서 `cluster` 값이 일부 달랐다.
- 이 문제는 정본 생성 과정이 아니라 원천 입력 단계에서 이미 존재했다.

현재 확인된 사실:

- 보정 전에는 군집 라벨 불일치가 입력 스냅샷 자체의 문제였다.
- 현재는 `train 2023-2024` 기준 `station_id -> cluster` 매핑을 마스터로 삼아 정본과 후속 데이터를 다시 생성했다.
- 따라서 현재 `canonical_data`와 `modeling_data`의 `cluster`는 train/test에서 일치한다.
- 최신 `2025` 군집별 오차표는 [ddri_cluster_error_breakdown_2025.csv](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/03_output_data/ddri_cluster_error_breakdown_2025.csv)에 다시 저장했다.
- 보정 후에도 `cluster 1`은 여전히 가장 어려운 군집이다.
  - `rep15 + bike_change_deseasonalized`: cluster 1 RMSE `0.547215`
  - `full161 + bike_change_deseasonalized`: cluster 1 RMSE `0.613313`

따라서 지금 단계의 타당한 해석은 아래다.

1. `cluster` 컬럼 자체는 의미가 있을 수 있다.
2. 원천 `OLD_DATA`의 `cluster`는 그대로 믿으면 안 된다.
3. 현재는 고정 매핑으로 보정한 뒤 다시 생성한 정본 기준으로만 해석해야 한다.

## 8. 현재까지의 종합 판단

현재 시점에서 가장 타당한 정리는 아래와 같다.

1. 기본 기준선은 여전히 `무샘플링 + LightGBM_RMSE`다.
2. 타깃은 현재로선 `bike_change_deseasonalized`가 1순위다.
3. 샘플링 1안은 현재 설정에서는 실익이 약하다.
4. 가중치 2안은 샘플링 1안보다 낫지만 개선 폭이 매우 작다.
5. 현재 `cluster` 컬럼은 버릴 정보가 아니라, 해석과 분기 전략 검토 대상이다.
6. 특히 `rep15`는 `station_group`가 안정적으로 남아 있어 `cluster` 보정 검증축으로 함께 쓸 수 있다.

## 9. 다음 우선순위

현재 우선순위는 아래 순서가 적절하다.

1. 보정 후 기준선, 샘플링 1안, 가중치 2안 문서를 현재 상태로 유지
2. `cluster` 포함 vs 제외 모델 비교
3. 필요하면 `station_group`을 함께 보는 `rep15` 해석 보강
4. 샘플링 1안과 가중치 2안을 `full161`으로 확대 재확인

즉, 군집 라벨 고정 자체는 끝났고, 다음 단계는
**보정 후 데이터 기준으로 샘플링/가중치 실험을 다시 평가한 뒤 `cluster` 기여도를 비교하는 것**이다.
