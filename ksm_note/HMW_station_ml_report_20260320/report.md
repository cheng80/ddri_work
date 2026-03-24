# HMW3 Station 머신러닝 및 분석 보고서

## 1. 보고서 목적

이 문서는 `hmw3` 폴더 안의 `Data`, `Note`, `scripts` 산출물을 바탕으로, 강남구 주요 따릉이 대여소 20개에 대한 머신러닝 예측 결과를 보고서 형태로 재정리한 문서다.  
분석 대상은 시간대별 `rental_count`, `return_count`이며, 모델 구조는 패턴 기반 feature와 Ridge 회귀를 결합한 형태다.

## 2. 사용한 근거 파일

### Data

- `hmw3/Data/top20_station_metrics_summary.csv`
- `hmw3/Data/top20_station_combined_test_r2_ranking.csv`
- `hmw3/Data/station_*_feature_importance.csv`
- `hmw3/Data/station_*_2025_high_error_points.csv`
- `hmw3/Data/station_*_offday_month_ridge_metrics.csv`
- `hmw3/Data/station_*_offday_hour_formulas.csv`
- `hmw3/Data/station_*_month_weights.csv`

### Note

- `hmw3/Note/hmw_station.ipynb`
- `hmw3/Note/hmw_top5_station_trends_2023_2025.ipynb`
- `hmw3/Note/hmw2306.ipynb` ~ `hmw3/Note/hmw4906.ipynb`

### Scripts

- `hmw3/scripts/generate_top20_station_suite.py`

스크립트와 노트북 내용을 함께 보면, 전체 분석 흐름은 다음과 같다.

1. 이용량 상위 station 후보를 모은다.
2. station별 시계열 데이터와 파생 산출물을 생성한다.
3. `day_type`, `month_weight`, `hour_weight`, `pattern_prior`, `corrected_pattern_prior` 등 패턴 중심 feature를 만든다.
4. `2023=train`, `2024=valid`, `2025=test` 기준으로 Ridge alpha를 고른다.
5. station별 성능, 중요 feature, 고오차 시점을 비교한다.

## 3. 분석 설계 요약

- 분석 대상 station 수: 20개
- 예측 target: `rental_count`, `return_count`
- 데이터 분할: `2023=train`, `2024=valid`, `2025=test`
- 핵심 모델: `pattern feature + Ridge regression`
- 평가 지표: `RMSE`, `MAE`, `R^2`

노트북 `hmw_station.ipynb` 기준으로 보면, 이 프로젝트는 단순 회귀가 아니라 시간대 패턴을 먼저 만들고 그 패턴을 Ridge로 보정하는 방식에 가깝다.  
즉, 모델 성능은 "기본 패턴이 얼마나 안정적인가"에 크게 의존하고, 그 위에 월별/시간대별 가중치가 보조적으로 얹히는 구조다.

## 4. 전체 성능 요약

`top20_station_combined_test_r2_ranking.csv` 기준 2025년 테스트 성능을 종합하면 다음과 같다.

- 평균 Combined Test R^2: `0.364`
- 중앙값 Combined Test R^2: `0.333`
- 평균 Rental Test R^2: `0.350`
- 평균 Return Test R^2: `0.378`

해석하면, 반납량 예측이 대여량 예측보다 소폭 안정적이며, station별 편차는 꽤 큰 편이다.  
상위권 station은 `0.43 ~ 0.61` 수준의 Combined Test R^2를 보이지만, 하위권은 `0.24 ~ 0.29` 수준까지 떨어진다.

![Top 20 Combined R2 Ranking](assets/top20_combined_r2_ranking.png)

### 상위 5개 station

| 순위 | station_id | station_name | Combined Test R^2 | Combined Test RMSE | Combined Test MAE |
|---|---:|---|---:|---:|---:|
| 1 | 2348 | 포스코사거리(기업은행) | 0.614 | 1.972 | 1.151 |
| 2 | 2335 | 3호선 매봉역 3번출구앞 | 0.546 | 1.806 | 1.222 |
| 3 | 2377 | 수서역 5번출구 | 0.456 | 1.934 | 1.326 |
| 4 | 2384 | 자곡사거리 | 0.436 | 1.527 | 1.065 |
| 5 | 2306 | 압구정역 2번 출구 옆 | 0.432 | 1.474 | 1.002 |

### 하위 5개 station

| 순위 | station_id | station_name | Combined Test R^2 | Combined Test RMSE | Combined Test MAE |
|---|---:|---|---:|---:|---:|
| 16 | 4906 | 섬유센터 앞 | 0.288 | 1.409 | 1.030 |
| 17 | 3614 | 은마아파트 입구 사거리 | 0.283 | 1.270 | 0.926 |
| 18 | 2369 | KT선릉타워 | 0.267 | 1.220 | 0.905 |
| 19 | 2413 | 도곡역 1번 출구 | 0.254 | 1.352 | 0.951 |
| 20 | 2423 | 영희초교 사거리(래미안개포루체하임) | 0.244 | 1.349 | 0.997 |

### 상위 10개 station의 target별 Test R^2

아래 그림은 상위권 station에서도 대여량과 반납량의 난이도가 서로 다르다는 점을 보여준다.  
예를 들어 2348은 두 target 모두 강하지만, 일부 station은 한쪽 target만 상대적으로 강한 비대칭 구조를 보인다.

![Top 10 Target R2 Comparison](assets/top10_target_r2_comparison.png)

## 5. 모델이 실제로 의존한 feature

20개 station의 feature importance를 평균하면, 두 target 모두 거의 같은 패턴이 나온다.

### Rental Count 평균 importance ratio 상위 feature

| 순위 | feature | 평균 importance ratio |
|---|---|---:|
| 1 | corrected_pattern_prior | 0.555 |
| 2 | pattern_prior | 0.157 |
| 3 | hour_weight | 0.141 |
| 4 | month_weight | 0.080 |
| 5 | base_value | 0.050 |

### Return Count 평균 importance ratio 상위 feature

| 순위 | feature | 평균 importance ratio |
|---|---|---:|
| 1 | corrected_pattern_prior | 0.549 |
| 2 | pattern_prior | 0.149 |
| 3 | hour_weight | 0.146 |
| 4 | month_weight | 0.074 |
| 5 | base_value | 0.048 |

핵심 해석은 명확하다.

- 모델의 중심은 `corrected_pattern_prior`다.
- 그 다음은 `pattern_prior`, `hour_weight`, `month_weight`가 받쳐준다.
- `year_weight` 영향은 사실상 거의 없다.

즉, 이 모델은 "연도별 장기 추세"를 학습하는 구조라기보다, 이미 만들어진 시간 패턴을 보정하는 구조에 가깝다.

![Feature Importance Summary](assets/feature_importance_summary.png)

## 6. 2025 테스트 고오차 구간 분석

`station_*_2025_high_error_points.csv`를 합쳐 보면, 오차는 특정 월과 특정 시간대에 반복적으로 몰린다.

### Rental Count 고오차 hotspot

- 월: `5월`, `6월`, `9월`, `4월`, `10월`
- 시간: `18시`, `17시`, `8시`, `19시`, `16시`
- day type: `weekday`가 `offday`보다 훨씬 많음

### Return Count 고오차 hotspot

- 월: `6월`, `9월`, `5월`, `4월`, `10월`
- 시간: `18시`, `17시`, `8시`, `19시`, `7시`
- day type: `weekday`가 `offday`보다 훨씬 많음

정리하면, 출퇴근 직전·직후 시간대와 계절 전환기 구간에서 예측이 흔들리는 경향이 강하다.  
특히 `17~19시`, `07~08시`는 실제 수요 급증이나 국소 이벤트가 패턴 기반 보정만으로는 충분히 설명되지 않는 구간으로 해석할 수 있다.

![Error Hotspots](assets/error_hotspots.png)

## 7. 해석과 시사점

이번 결과는 다음 세 가지를 보여준다.

1. 상위 station은 반복적 이용 패턴이 뚜렷해 Ridge 기반 구조만으로도 일정 수준의 예측력이 확보된다.
2. 성능 차이는 station 자체의 인기보다도 패턴 안정성과 급변 이벤트 빈도에 더 크게 좌우된다.
3. 현재 구조는 "평균적인 시간 패턴 재현"에는 강하지만, 갑작스러운 수요 급증이나 특수 이벤트 대응에는 약하다.

따라서 운영 측면에서는 다음 방향이 유효하다.

- 단기 재고 운영에는 상위권 station 예측을 우선 활용한다.
- 하위권 station은 날씨, 행사, 주변 교통 변수 같은 외생 변수를 추가하는 편이 낫다.
- `17~19시`, `07~08시` 집중 구간은 별도 보정 로직 또는 분리 모델 검토 가치가 높다.

## 8. 결론

`hmw3`의 산출물을 종합하면, 이 프로젝트의 머신러닝 파이프라인은 "pattern prior를 중심으로 한 Ridge 보정 모델"로 요약된다.  
전체 20개 station 기준 평균 Combined Test R^2는 `0.364`이며, 최상위 station은 `0.614`까지 도달했다.

반면, 성능 하락 구간은 분명하다.

- 특정 station은 패턴 안정성이 낮아 일반화 성능이 약하다.
- 고오차는 평일 출퇴근 시간과 4~6월, 9~10월에 집중된다.
- `year_weight` 기여가 거의 없다는 점은 현재 모델이 구조적 장기 변화 포착에는 약하다는 뜻이다.

따라서 현재 보고서 기준의 최종 판단은 다음과 같다.

- 이 모델은 "반복 패턴이 강한 station의 시간대별 대여/반납량 예측"에는 실무적으로 의미가 있다.
- 다만 "급격한 수요 변화"나 "장기 구조 변화"까지 설명하는 범용 예측기로 보기에는 아직 한계가 있다.

## 9. 파일 위치

- 보고서 본문: `ksm_note/HMW_station_ml_report_20260320/report.md`
- 이미지 폴더: `ksm_note/HMW_station_ml_report_20260320/assets`

