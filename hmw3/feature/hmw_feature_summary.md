# Feature Expansion Summary For Top 6 Stations

## 개요

이 문서는 [hmw_feature.ipynb](C:\Users\TJ\ddri_work\hmw3\feature\hmw_feature.ipynb) 실험 결과를 요약한 자료이다.  
대상은 상위 6개 station이며, 기존 `hmw_station.ipynb`의 baseline 구조를 유지한 상태에서 추가 feature를 가중치 기반으로 붙여 보며 어떤 조합이 가장 좋은 `RMSE`, `MAE`, `R²`를 만드는지 비교했다.

실험 대상 station:

- `2306` 압구정역 2번 출구 옆
- `2335` 3호선 매봉역 3번출구앞
- `2348` 포스코사거리(기업은행)
- `2375` 수서역 1번출구 앞
- `2377` 수서역 5번출구
- `2384` 자곡사거리

데이터 분할:

- `Train`: 2023년
- `Valid`: 2024년
- `Test`: 2025년

## 비교한 Feature Set

### `baseline`

기존 모델에서 사용하던 기본 feature 조합이다.

- `base_value`
- `month_weight`
- `year_weight`
- `hour_weight`
- `pattern_prior`
- `corrected_pattern_prior`
- `day_type_weekday`
- `day_type_offday`

### `baseline_plus_weekday`

요일별 차이를 추가 반영한 조합이다.

- baseline
- `weekday_weight`
- `weekday_adjusted_prior`

### `baseline_plus_season`

계절별 규모 차이를 추가 반영한 조합이다.

- baseline
- `season_weight`
- `season_adjusted_prior`

### `baseline_plus_quarter`

분기 단위 차이를 추가 반영한 조합이다.

- baseline
- `quarter_weight`
- `quarter_adjusted_prior`

### `baseline_plus_rush_hour`

출퇴근 피크 시간대 효과를 추가 반영한 조합이다.

- baseline
- `rush_hour_weight`
- `rush_hour_adjusted_prior`

### `baseline_plus_month_day_type`

월과 `weekday/offday`의 결합 효과를 추가 반영한 조합이다.

- baseline
- `month_day_type_weight`
- `month_day_type_adjusted_prior`

### `all_extended`

위의 확장 feature를 전부 결합한 조합이다.

## 전체 요약

station별로 최적인 feature set이 달랐다. 즉, 모든 station에 공통으로 가장 좋은 feature가 하나로 고정되지는 않았다.

전반적인 경향은 다음과 같았다.

- `2306`, `2335`, `2375`는 `weekday` 계열 feature를 추가했을 때 가장 안정적으로 개선됐다.
- `2377`은 `month × day_type` 조합이 가장 잘 맞아, 월별 패턴과 평일/비근무일 차이를 함께 반영하는 것이 중요했다.
- `2348`, `2384`는 더 많은 확장 feature를 함께 쓰는 것이 유리했고, 특히 `2348`은 피크 시간대와 복합 보정 효과가 컸다.

## Station별 결과 해석

### `2306` 압구정역 2번 출구 옆

- `rental_count`: `baseline_plus_weekday`
  - `R²`: `0.3770 -> 0.3788`로 거의 변화 없거나 매우 소폭 개선
  - `RMSE`: `1.6549 -> 1.6525`로 아주 소폭 개선
  - `MAE`: `1.1608 -> 1.1569`로 아주 소폭 개선
- `return_count`: `baseline_plus_weekday`
  - `R²`: `0.5576 -> 0.5666`로 소폭 개선
  - `RMSE`: `1.7205 -> 1.7029`로 개선
  - `MAE`: `1.1473 -> 1.1496`로 거의 변화 없고 아주 미세하게 악화
- 종합:
  - `baseline_plus_weekday`
  - 요일 차이를 추가했을 때 가장 안정적이었지만, 개선 폭은 전체적으로 크지 않은 편이다.
  - 해석:
    - 압구정역 출구 바로 옆이라는 입지 특성상, 생활권 이동과 지하철 연계 수요가 꾸준히 발생하는 station으로 볼 수 있다.
    - 이런 station은 패턴 자체가 아주 복잡하기보다는 평일과 주말, 또는 요일별 이동 강도의 차이가 조금씩 누적되는 경우가 많아 `weekday_weight`가 잔차를 줄이는 데 도움을 준 것으로 해석할 수 있다.
    - 다만 개선 폭이 크지 않다는 점은, 역세권 고정 수요가 강해서 기존 시간 패턴만으로도 이미 대부분의 변동이 설명되고 있음을 뜻한다.

### `2335` 3호선 매봉역 3번출구앞

- `rental_count`: `baseline_plus_weekday`
  - `R²`: `0.5365 -> 0.5492`로 소폭 개선
  - `RMSE`: `1.8079 -> 1.7829`로 개선
  - `MAE`: `1.2319 -> 1.2160`로 개선
- `return_count`: `baseline_plus_weekday`
  - `R²`: `0.5397 -> 0.5452`로 소폭 개선
  - `RMSE`: `1.8421 -> 1.8312`로 개선
  - `MAE`: `1.2838 -> 1.2730`로 개선
- 종합:
  - `baseline_plus_weekday`
  - 평일/요일별 흐름 차이를 반영했을 때 세 지표가 모두 좋아졌다.
  - 해석:
    - 매봉역 출구 앞이라는 점에서 출퇴근 통행과 지하철 환승 보조 수요가 핵심인 station으로 볼 수 있다.
    - 이런 역세권 station은 시간대 패턴은 유사해도 월요일부터 금요일, 금요일과 주말 직전 같은 세부 요일 차이가 실제 이용량에 반영될 수 있다.
    - 그래서 `weekday_weight`를 넣으면 시간 패턴 위에 요일별 규모 차이를 한 번 더 보정할 수 있어 성능이 고르게 개선됐다.

### `2348` 포스코사거리(기업은행)

- `rental_count`: `baseline_plus_rush_hour`
  - `R²`: `0.6638 -> 0.6638`로 사실상 변화 없음
  - `RMSE`: `1.9736 -> 1.9736`으로 변화 없음
  - `MAE`: `1.1840 -> 1.1858`로 아주 미세하게 악화
- `return_count`: `all_extended`
  - `R²`: `0.6702 -> 0.7106`으로 뚜렷하게 개선
  - `RMSE`: `2.4764 -> 2.3197`로 크게 개선
  - `MAE`: `1.5107 -> 1.3764`로 크게 개선
- 종합:
  - `all_extended`
  - 이 station은 단순 월/시간 보정보다 출퇴근 시간, 요일, 월-비근무일 결합 효과를 함께 반영하는 편이 더 유리했다.
  - 해석:
    - 포스코사거리와 기업은행 인근이라는 점에서 전형적인 강남 업무지구형 station 특성을 가진다.
    - 이런 곳은 출퇴근 시간대의 급격한 수요 변화, 평일 중심 수요, 월별 업무일수 차이, 비근무일 패턴 변화가 동시에 작용하기 쉽다.
    - `rental_count`는 특히 출근/퇴근 피크의 국소적 변화가 중요해서 `rush_hour`가 효과적이었다.
    - `return_count`는 요일, 계절, 월-비근무일 조합까지 함께 들어간 `all_extended`에서 크게 좋아졌는데, 이는 반납 패턴이 단일 규칙보다 여러 조건의 결합으로 결정되는 업무지구형 station의 성격을 잘 보여준다.

### `2375` 수서역 1번출구 앞

- `rental_count`: `baseline_plus_weekday`
  - `R²`: `0.4757 -> 0.4838`로 소폭 개선
  - `RMSE`: `1.5100 -> 1.4984`로 개선
  - `MAE`: `1.0333 -> 1.0249`로 개선
- `return_count`: `baseline_plus_weekday`
  - `R²`: `0.4751 -> 0.4792`로 거의 변화 없거나 소폭 개선
  - `RMSE`: `1.6136 -> 1.6072`로 소폭 개선
  - `MAE`: `1.1552 -> 1.1502`로 소폭 개선
- 종합:
  - `baseline_plus_weekday`
  - 요일 차이를 반영하는 것만으로도 가장 안정적인 개선이 나왔다.
  - 해석:
    - 수서역 출구 앞은 광역철도/지하철 연계 성격이 강한 환승형 station으로 볼 수 있다.
    - 환승형 station은 하루 패턴은 비교적 안정적이지만, 실제 이용량은 요일별 통근 강도 차이에 영향을 많이 받는 경우가 많다.
    - 그래서 복잡한 확장 feature를 많이 넣기보다 `weekday` 계열 feature만 반영해도 잔차가 줄어들었고, 가장 효율적인 보정으로 작동했다.

### `2377` 수서역 5번출구

- `rental_count`: `baseline_plus_month_day_type`
  - `R²`: `0.4517 -> 0.4760`으로 뚜렷하게 개선
  - `RMSE`: `1.8682 -> 1.8264`로 개선
  - `MAE`: `1.2470 -> 1.2476`으로 사실상 변화 없음
- `return_count`: `baseline_plus_month_day_type`
  - `R²`: `0.5775 -> 0.5986`으로 뚜렷하게 개선
  - `RMSE`: `2.0871 -> 2.0343`로 개선
  - `MAE`: `1.4491 -> 1.4422`로 소폭 개선
- 종합:
  - `baseline_plus_month_day_type`
  - 이 station은 단순 월 효과보다 `월 + weekday/offday` 결합 효과가 중요했다.
  - 해석:
    - 같은 수서역 권역이라도 5번 출구 주변은 1번 출구와 다른 보행 동선이나 주변 시설 영향이 반영될 가능성이 있다.
    - 그래서 단순히 역세권 환승 수요만 보기보다, 특정 월에 평일과 비근무일 패턴이 얼마나 달라지는지가 더 중요하게 작용한 것으로 보인다.
    - 단순 `month_weight`보다 `month_day_type_weight`가 더 잘 맞았다는 점은, 계절성 자체보다 “특정 월의 평일/주말 운영 패턴 차이”를 잡는 것이 더 효과적이었다는 뜻이다.

### `2384` 자곡사거리

- `rental_count`: `baseline_plus_weekday`
  - `R²`: `0.4878 -> 0.4966`로 소폭 개선
  - `RMSE`: `1.7618 -> 1.7466`로 개선
  - `MAE`: `1.2286 -> 1.2161`로 개선
- `return_count`: `all_extended`
  - `R²`: `0.4490 -> 0.4902`로 뚜렷하게 개선
  - `RMSE`: `1.8967 -> 1.8245`로 개선
  - `MAE`: `1.3663 -> 1.3054`로 개선
- 종합:
  - `all_extended`
  - rental은 요일 효과 중심, return은 복합 확장 feature가 더 유리한 혼합형 패턴이었다.
  - 해석:
    - 자곡사거리는 역 출구 바로 앞보다는 교차로 생활권/업무권 이동이 섞인 지점 성격으로 볼 수 있다.
    - 이런 곳은 대여는 비교적 규칙적으로 발생하더라도, 반납은 주변 목적지나 시간대, 비근무일 활동에 따라 더 복합적으로 흔들릴 수 있다.
    - 그래서 대여 쪽은 `weekday`만으로도 충분한 보정이 가능했고, 반납 쪽은 특정 시간대, 계절, 월-비근무일 조합까지 함께 작용하는 패턴이 있는 것으로 보여 `all_extended`에서 성능이 더 좋아졌다.
    - 즉 이 station은 target별로 필요한 feature 복잡도가 다르다는 점이 특징이다.

## 최종 정리

이번 실험으로 확인된 핵심은 다음과 같다.

- station마다 최적 feature 조합이 다르다.
- `weekday`는 여러 station에서 반복적으로 유효했다.
- 일부 station은 `rush_hour`나 `month_day_type`처럼 더 구체적인 보정이 필요했다.
- `all_extended`가 항상 최고는 아니지만, 패턴이 복합적인 station에서는 가장 좋은 결과를 만들 수 있다.
- `R²`가 좋아졌다고 해서 항상 `MAE`까지 같이 좋아지는 것은 아니었다.
- 따라서 최종 feature 선택은 `R²`만이 아니라 `RMSE`, `MAE`까지 함께 보고 판단하는 것이 적절하다.
- 추가 feature가 도움이 되는 이유는, 기본 시간 패턴만으로 설명되지 않는 “요일 차이”, “피크 시간대 효과”, “월과 비근무일의 결합 효과” 같은 잔차 구조를 한 번 더 보정해주기 때문이다.

따라서 이후 운영 또는 서비스 적용 시에는 모든 station에 같은 feature 조합을 일괄 적용하기보다, station별 최적 조합을 따로 가져가는 것이 더 적절하다.

## 결과 파일

- [feature_top6_experiment_metrics.csv](C:\Users\TJ\ddri_work\hmw3\Data\summaries\feature_top6_experiment_metrics.csv)
- [feature_top6_best_by_target.csv](C:\Users\TJ\ddri_work\hmw3\Data\summaries\feature_top6_best_by_target.csv)
- [feature_top6_best_by_station.csv](C:\Users\TJ\ddri_work\hmw3\Data\summaries\feature_top6_best_by_station.csv)
- [feature_top6_station_optimal_summary.csv](C:\Users\TJ\ddri_work\hmw3\Data\summaries\feature_top6_station_optimal_summary.csv)
- [feature_top6_station_interpretation.csv](C:\Users\TJ\ddri_work\hmw3\Data\summaries\feature_top6_station_interpretation.csv)
