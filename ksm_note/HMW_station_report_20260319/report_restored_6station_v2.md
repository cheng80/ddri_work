---
title: "강남구 따릉이 6개 대여소 예측 분석 V2"
pdf_options:
  format: A4
  landscape: true
---

<!-- markdownlint-disable MD013 -->

<link rel="stylesheet" href="../HMW_ridge_end_to_end_report_20260318_reneew/references/ddri_presentation_a4_landscape.css">

# 강남구 따릉이 6개 대여소 예측 분석 V2

## 분석 목적

- `랜덤 선정 6개 대여소`를 대상으로 수요 예측 절차와 해석 가능성을 점검
- 초점은 `군집화 결과 제시`보다 `예측 파이프라인이 안정적으로 작동하는지` 확인하는 데 있음

## 핵심 메시지

- 현재 단계에서는 군집화를 생략하고 6개 대여소 예측에 집중했다.
- 예측 구조는 `패턴 기반 feature + Ridge 회귀`를 기준 모델로 사용했다.
- 향후 강남구 전체 대여소로 확장할 경우에는 군집화를 선행하는 구조가 더 적절하다.

<div class="callout">현재는 6개 대여소 파일럿, 이후 전체 확장 시 군집화 도입이라는 2단계 전략이 핵심이다.</div>

<div class="page-break"></div>

# 1. 이번 단계에서 군집화를 하지 않은 이유

## 분석 범위

- 이번 분석은 강남구 전체 대여소 운영 모형을 완성하는 단계가 아니다.
- 랜덤 선정한 6개 대여소를 대상으로 예측 가능성과 결과 해석 흐름을 먼저 검토하는 파일럿 단계다.

## 군집화를 생략한 판단 근거

- 현재 분석 범위가 6개 대여소에 한정되어 있어, 군집화를 통해 대여소 유형을 먼저 나눌 필요성이 크지 않았다.
- 표본 수가 작은 상태에서 군집화를 전면에 두면, 군집 결과 자체의 일반화 가능성을 설명하기 어렵다.
- 따라서 이번 단계에서는 군집화 없이 예측 구조와 성능 해석이 가능한지 먼저 점검하는 편이 더 자연스럽다.

## 표현 원칙

- `현재`: 군집화는 생략하고 개별 대여소 예측에 집중
- `향후`: 강남구 전체 확장 시 군집화를 도입해 대여소 유형 차이를 반영

<div class="callout compact">현재는 6개 대여소만 예측하므로 군집화를 생략한다. 향후 강남구 전체 대여소로 확장할 경우에는, 대여소 간 공간적 특성과 수요 패턴의 이질성을 반영하기 위해 군집화를 선행하는 편이 적절하다.</div>

<div class="page-break"></div>

# 2. 향후 전체 확장 시 군집화가 필요한 이유

## 군집화의 역할

- 타깃 단위: `대여소 단위(station-level)`
- 목적: 대여소의 공간 역할을 먼저 정리하고, 이후 예측 성능 차이를 군집 맥락과 함께 해석
- 효과: 비슷한 입지와 패턴을 가진 대여소끼리 묶어, 해석력과 일반화 가능성을 높임

## 향후 적용 가능한 군집화 기준

| 분류 축 | 예시 피처 |
|---|---|
| 시간대 반납 구조 | `arrival_7_10_ratio`, `arrival_11_14_ratio`, `arrival_17_20_ratio` |
| 유입/유출 구조 | `morning_net_inflow`, `evening_net_inflow` |
| 교통 접근성 | `subway_distance_m`, `bus_stop_count_300m` |

## 해석 포인트

- 업무/상업형, 주거형, 생활·상권 혼합형처럼 공간 역할이 다른 대여소는 동일한 예측 오차라도 의미가 다르다.
- 따라서 전체 대여소 분석에서는 군집화가 예측 이전의 `구조 정리 단계`로 필요해진다.

<div class="callout compact">군집화는 이번 6개 대여소 분석의 필수 절차가 아니라, 전체 대여소 확장 시 해석력을 높이기 위한 선행 정리 단계다.</div>

<div class="page-break"></div>

# 3. 군집화는 현재 결과가 아니라 향후 참고 프레임이다

<div class="chart-block">
  <img class="chart-image" src="../../works/01_clustering/08_integrated/final/results/second_clustering_results/images/ddri_second_kmeans_pca_scatter.png" alt="군집 PCA 산점도" />
</div>

<div class="chart-block">
  <img class="chart-image" src="../../works/01_clustering/08_integrated/final/results/second_clustering_results/images/ddri_second_cluster_profile_heatmap.png" alt="군집 특성 히트맵" />
</div>

## 이 페이지에서 볼 점

- 산점도는 군집이 완전히 겹치지 않고 역할별로 분리되는 경향을 보여준다.
- 히트맵은 군집별 시간대 반납 비율, 순유입, 교통 접근성 조합이 다름을 한눈에 요약한다.
- 이 자료는 `이번 6개 대여소 예측 결과`가 아니라, `향후 전체 대여소 확장 분석의 해석 프레임`을 보여주는 참고 예시다.

<div class="page-break"></div>

# 4. 전체 예측 파이프라인 안에서 현재 단계의 위치

## 현재 파일럿 단계

1. 랜덤 선정 6개 대여소를 대상으로 예측 파이프라인 점검
2. 전처리, 패턴 기반 feature, Ridge 예측, 오차 해석까지 연결
3. 소수 대여소 기준에서도 해석 가능한 기준 모델이 되는지 확인

## 향후 확장 단계

1. 강남구 전체 대여소 수집 및 공통 운영 기준 정리
2. `station-level` 군집화로 대여소 유형화
3. 군집별 패턴과 예측 성능을 함께 해석하는 구조로 확장

<div class="chart-block tight">
  <img class="appendix-map-image" src="../../works/01_clustering/08_integrated/final/results/second_clustering_results/images/ddri_second_cluster_static_map.png" alt="군집 지도" />
</div>

<div class="callout compact">즉, 현재는 예측 파이프라인 검증 단계이고, 군집화는 이후 전체 대여소 해석 단계에서 다시 도입할 예정이다.</div>

<div class="page-break"></div>

# 5. 데이터와 전처리 구조

## 데이터 범위

| 항목 | 값 |
|---|---|
| 관측 기간 | `2023-01-01 00:00:00` ~ `2025-12-31 23:00:00` |
| 공휴일 개수 | 56 |
| 기준 분할 | `train=2023`, `valid=2024`, `test=2025` |

## 사용 자산 구조

| 자산 | 개수 |
|---|---:|
| station 원천 csv | 20 |
| 공휴일 기준 csv | 20 |
| 패턴 공식 csv | 20 |
| 가중치 csv | 20 |
| 튜닝 결과 csv | 20 |
| 성능 지표 csv | 20 |
| feature 중요도 csv | 20 |
| 고오차 지점 csv | 20 |

## 품질 점검 요약

| 항목 | 결과 |
|---|---|
| station별 row 수 | 모두 26304 |
| unique_time | 모두 26304 |
| 결측 | 0 |
| 음수 대여/반납 | 없음 |
| duplicate time row | 0 |

## 해석

- 기본적인 시계열 길이와 결측 상태는 양호했다.
- 따라서 초점은 데이터 정제보다 `예측 구조 설계`와 `오차 해석`에 둘 수 있다.

<div class="page-break"></div>

# 6. 분할 구조와 기본 패턴

## 분할 원칙

- `train`: 2023년
- `valid`: 2024년
- `test`: 2025년
- `day_type`: `weekday`, `offday`

## 분할 요약

| split | day_type | rows | rental_mean | return_mean |
|---|---|---:|---:|---:|
| train | offday | 56640 | 1.2911 | 1.3941 |
| train | weekday | 118560 | 1.7291 | 1.9181 |
| valid | offday | 57600 | 1.2688 | 1.3616 |
| valid | weekday | 118080 | 1.7358 | 1.9396 |
| test | offday | 58080 | 1.0250 | 1.1125 |
| test | weekday | 117120 | 1.4745 | 1.6507 |

<div class="chart-block">
  <img class="chart-image" src="./report_clean_files/report_clean_9_0.png" alt="day_type별 평균 이용량과 모델링 이전 시간대 패턴" />
</div>

## 해석

- `weekday`가 `offday`보다 평균 대여·반납량이 높았다.
- 시간대 패턴은 출근·퇴근 시간대 피크가 뚜렷했고, 이 구조가 후속 패턴 기반 feature 설계의 출발점이 된다.

<div class="page-break"></div>

# 7. 패턴 기반 feature + Ridge 구조

## 왜 원천 count를 바로 넣지 않았는가

- 원천 count만으로는 시간 구조를 해석하기 어렵다.
- 먼저 `day_type`별 시간 패턴을 기본 형태로 만들고, 여기에 월·연도·시간 보정치를 얹는 편이 더 해석 가능했다.

## 핵심 feature 구조

| Feature | 역할 |
|---|---|
| `base_value` | 요일유형별 기본 시간 패턴 |
| `month_weight` | 월/계절 단위 수준 보정 |
| `year_weight` | 연도별 수준 이동 보정 |
| `hour_weight` | 세부 시간대 편차 보정 |
| `pattern_prior` | 패턴 기반 1차 예측값 |
| `corrected_pattern_prior` | 시간 보정까지 반영한 최종 prior |

## 모델 선정 이유

1. 해석 가능성
2. station 단위 분리 학습에서의 안정성
3. Ridge `alpha`를 통한 과적합 제어
4. 고성능 블랙박스보다 비교 가능한 기준 모델이라는 점

<div class="callout">이 모델은 최고 복잡도의 예측기보다, 시간 패턴을 보존하면서 station별 차이를 비교하기 위한 기준 모델에 가깝다.</div>

<div class="page-break"></div>

# 8. 가중치 구조는 어떤 패턴을 반영하는가

<div class="chart-block">
  <img class="chart-image" src="./report_clean_files/report_clean_15_0.png" alt="월 가중치 범위" />
</div>

<div class="image-row">
  <img class="half-image" src="./report_clean_files/report_clean_17_0.png" alt="연도 가중치 범위" />
  <img class="half-image" src="./report_clean_files/report_clean_18_0.png" alt="시간 가중치 범위" />
</div>

## 해석

- `month_weight`는 계절성, `year_weight`는 연도별 수준 차이, `hour_weight`는 세부 시간대 오차를 반영한다.
- 특히 `hour_weight`는 출근·퇴근 피크처럼 반복적으로 발생하는 시간대 오차를 보정하는 데 중요하다.
- `year_weight`는 해당 연도의 실제 데이터를 보고 계산되므로, 완전히 새로운 연도를 미리 고정적으로 예측하는 변수라기보다 사후적 보정값에 가깝다.

<div class="page-break"></div>

# 9. Ridge 튜닝과 전체 성능 해석

## 선택된 alpha 분포

| target | 대표 alpha 분포 |
|---|---|
| rental_count | `0.001`가 가장 많고, 일부 station은 `1000`까지 사용 |
| return_count | `100` 비중이 높고, `0.001`, `10`, `1000`이 함께 분포 |

<div class="chart-block">
  <img class="chart-image" src="./report_clean_files/report_clean_22_0.png" alt="선택 alpha 분포" />
</div>

## split별 평균 성능

| target | test RMSE | test MAE | test R^2 |
|---|---:|---:|---:|
| rental_count | 1.4124 | 0.9889 | 0.3498 |
| return_count | 1.5161 | 1.0562 | 0.3781 |

## 해석

- `return_count`가 `rental_count`보다 평균 R^2가 조금 더 높았다.
- train-valid-test 간 성능 격차가 과도하게 벌어지지 않아 기준 모델로는 비교적 안정적이다.

<div class="image-row">
  <img class="half-image" src="./report_clean_files/report_clean_25_0.png" alt="rental_count split별 성능" />
  <img class="half-image" src="./report_clean_files/report_clean_25_1.png" alt="return_count split별 성능" />
</div>

<div class="page-break"></div>

# 10. 파일럿에서 주목한 6개 station

## 상위 6개 station

- `2348` 포스코사거리(기업은행)
- `2335` 3호선 매봉역 3번출구앞
- `2377` 수서역 5번출구
- `2384` 자곡사거리
- `2306` 압구정역 2번 출구 옆
- `2375` 수서역 1번출구 앞

<div class="chart-block">
  <img class="appendix-map-image" src="./report_clean_files/report_clean_map_top6_static.png" alt="상위 6개 station 위치도" />
</div>

<div class="chart-block">
  <img class="chart-image" src="./report_clean_files/report_clean_30_0.png" alt="상위 6개 station 성능 요약" />
</div>

## 해석

- 파일럿 대상 안에서도 station별 재현력 차이는 분명하게 존재했다.
- 따라서 이후 전체 확장 단계에서는 대여소 차이를 체계적으로 설명할 장치가 필요하고, 그 역할을 군집화가 맡게 된다.

<div class="page-break"></div>

# 11. 모델은 무엇을 가장 크게 참고했는가

## 공통 중요 feature

| target | 1순위 | 2순위 | 3순위 |
|---|---|---|---|
| rental_count | `corrected_pattern_prior` (0.5548) | `pattern_prior` (0.1575) | `hour_weight` (0.1406) |
| return_count | `corrected_pattern_prior` (0.5494) | `pattern_prior` (0.1490) | `hour_weight` (0.1465) |

<div class="image-row">
  <img class="half-image" src="./report_clean_files/report_clean_36_0.png" alt="평균 feature 중요도 rental" />
  <img class="half-image" src="./report_clean_files/report_clean_36_1.png" alt="평균 feature 중요도 return" />
</div>

<div class="image-row">
  <img class="half-image" src="./report_clean_files/report_clean_31_0.png" alt="상위 6개 station rental 중요도" />
  <img class="half-image" src="./report_clean_files/report_clean_31_1.png" alt="상위 6개 station return 중요도" />
</div>

## 해석

- 중요도는 거의 모든 station에서 `corrected_pattern_prior`에 집중됐다.
- 즉, 이 모델의 중심은 “패턴 기반 사전 예측값을 얼마나 잘 보정하느냐”에 있다.

<div class="page-break"></div>

# 12. 어디서 오차가 커졌는가

## hotspot 요약

| 구분 | 관찰 결과 |
|---|---|
| station별 큰 오차 | `2348`, `2377`, `2335`에서 상대적으로 크게 관찰 |
| 시간대 hotspot | 주로 `17~19시` |
| 월별 hotspot | 4~6월, 9~10월 구간에서 반복 |

<div class="chart-block">
  <img class="chart-image" src="./report_clean_files/report_clean_39_0.png" alt="평균 절대오차 hotspot 히트맵" />
</div>

<div class="image-row">
  <img class="half-image" src="./report_clean_files/report_clean_32_0.png" alt="상위 6개 station 연도별 패턴 비교 rental" />
  <img class="half-image" src="./report_clean_files/report_clean_32_1.png" alt="상위 6개 station 연도별 패턴 비교 return" />
</div>

## 해석

- 최상위 station일수록 시간대 패턴 자체가 안정적으로 반복되는 경향이 있었다.
- 오차 hotspot은 저녁 피크와 계절 전환 구간에 몰려 있어, 후속 단계에서는 날씨, 이벤트, 재배치, 혼잡도 같은 외생 변수 보강이 필요하다.

<div class="page-break"></div>

# 13. 결론과 다음 단계

## 핵심 정리

- 현재 분석 범위는 `6개 대여소 파일럿`이다.
- 군집화는 이번 단계에서 생략하고, `향후 전체 대여소 확장 시 필요한 단계`로 정리했다.
- 예측 구조는 `패턴 기반 feature + Ridge 회귀` 기준 모델로서 충분한 해석 가능성을 보였다.
- station별 재현력 차이와 시간대 hotspot을 통해, 현재 구조의 강점과 한계도 함께 드러났다.

## 다음 단계 제안

1. 강남구 전체 대여소 확장 시 `station-level` 군집화 재도입
2. hotspot 구간 보강을 위한 외생 변수 추가 검토

## 재고 예측 해석 가이드

`다음 시점 재고 = 현재 재고 - 예측 rental_count + 예측 return_count`

- 단기 재고 흐름 추적에는 활용 가능
- 장기 재고 예측에는 누적 오차가 커져 별도 구조가 필요

<div class="callout">현재는 6개 대여소 예측 검증, 다음 단계는 전체 대여소 확장과 군집화 재도입이다.</div>
