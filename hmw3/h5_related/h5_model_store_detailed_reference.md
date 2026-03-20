# H5 Model Store Detailed Reference

## 목적

이 문서는 `hmw_h5_model_store.ipynb`에서 다루는 내용을 더 자세히 설명하는 참고 문서입니다.

주요 대상은 아래와 같습니다.

- 상위 6개 station 모델을 통합 `h5`로 저장하는 구조
- 웹서비스에서 모델을 preload 해서 쓰는 방식
- 입력값이 내부 feature로 바뀌는 과정
- JSON 결과 구조와 활용 방식
- `2026 dynamic year_weight`를 이용한 운영 중 보정 방식

## 1. 전체 구조

현재 예측 시스템은 하나의 단순 회귀식만 저장하는 구조가 아닙니다. station별로 아래 요소가 함께 필요합니다.

- `rental_count` 예측용 Ridge 파라미터
- `return_count` 예측용 Ridge 파라미터
- `feature_names`
- `day_type-hour` 기본식
- `month_weight`
- `year_weight`
- `hour_weight`
- 공휴일 기준 정보
- 운영 중 갱신되는 `dynamic_year_weight`

즉 예측은 아래 두 층으로 나뉩니다.

### 고정 모델 층

학습 시점에 만들어져 `h5` 안에 저장되는 값입니다.

- 기본식
- 월/연도/시간 가중치
- Ridge 계수

### 운영 보정 층

실서비스 운영 중 실제값이 들어오면서 계속 바뀌는 값입니다.

- `dynamic_year_weight`

이 값은 고정 학습 결과가 아니라 운영 상태값입니다.

## 2. 최종적으로 저장해야 하는 모델

최종 저장물은 station별 bundle입니다.

station 하나당 저장되어야 하는 항목은 다음과 같습니다.

### station 식별 정보

- `station_id`
- `station_name`

### rental_count 모델 정보

- `coef`
- `intercept`
- `feature_names`

### return_count 모델 정보

- `coef`
- `intercept`
- `feature_names`

### 패턴식과 가중치

- `formula`
- `month_weight`
- `year_weight`
- `hour_weight`

### 공통 메타정보

- `holiday_dates`
- `model_type`
- `version`
- `station_ids`

## 3. h5 내부 구조

권장 구조는 아래와 같습니다.

```text
top6_station_model_store.h5
├─ meta
│  ├─ model_type
│  ├─ version
│  ├─ station_ids
│  └─ holiday_dates
├─ stations
│  ├─ 2348
│  │  ├─ rental
│  │  │  ├─ coef
│  │  │  ├─ intercept
│  │  │  └─ feature_names
│  │  ├─ return
│  │  │  ├─ coef
│  │  │  ├─ intercept
│  │  │  └─ feature_names
│  │  ├─ formula
│  │  ├─ month_weight
│  │  ├─ year_weight
│  │  └─ hour_weight
│  ├─ 2335
│  ├─ 2377
│  ├─ 2384
│  ├─ 2306
│  └─ 2375
```

## 4. 서비스에서 직접 넣는 입력값

서비스에서 외부로부터 직접 받아야 하는 값은 많지 않습니다.

### 4.1 `station_id`

- 어떤 대여소 모델을 사용할지 결정하는 값
- 서버는 이 값으로 `MODEL_REGISTRY[station_id]`를 조회합니다

### 4.2 `datetime`

- 예측 대상 시각
- 여기서 아래 값들이 파생됩니다
  - `year`
  - `month`
  - `day`
  - `hour`
  - `weekday`

### 4.3 `current_bike_count_from_api`

- 현재 시점 실제 자전거 수량
- 단일 시점 예측에는 직접 들어가지 않음
- 재귀형 예측에서 `다음 시간 총 대수` 계산의 시작값이 됨

## 5. 내부 feature 상세 설명

모델이 실제로 사용하는 내부 feature는 아래 8개입니다.

### 5.1 `base_value`

- `day_type`와 `hour`를 바탕으로 기본 시간 패턴식에서 계산한 값
- station이 원래 가지는 시간대별 전형적인 흐름을 의미

### 5.2 `month_weight`

- 월별 규모 차이를 반영하는 가중치
- 같은 시간 패턴이어도 월별 총 규모가 다를 수 있기 때문에 필요

### 5.3 `year_weight`

- 2023~2025 학습 데이터 기반의 연도별 규모 차이 가중치
- 2026 이후에는 이것만으로 부족할 수 있어 `dynamic_year_weight`를 추가로 사용

### 5.4 `hour_weight`

- 기본 시간 패턴식이 설명하지 못한 특정 시간대 편차를 보정하는 가중치
- 예: 출퇴근 피크 강화

### 5.5 `pattern_prior`

- `base_value * month_weight * year_weight`
- 1차 패턴 예측값

### 5.6 `corrected_pattern_prior`

- `pattern_prior * hour_weight`
- 최종적으로 보정된 패턴값

### 5.7 `day_type_weekday`

- 평일이면 `1`, 아니면 `0`

### 5.8 `day_type_offday`

- 주말 또는 공휴일이면 `1`, 아니면 `0`

## 6. 입력값이 feature로 바뀌는 과정

전체 흐름은 아래와 같습니다.

1. 요청에서 `station_id`, `datetime`을 받음
2. `datetime`에서 `year`, `month`, `day`, `hour`, `weekday` 계산
3. 공휴일 테이블과 비교해서 `day_type = weekday / offday` 결정
4. 해당 station의 `formula`를 이용해 `base_value` 계산
5. 해당 station의 `month_weight`, `year_weight`, `hour_weight` 조회
6. `pattern_prior` 계산
7. `corrected_pattern_prior` 계산
8. `day_type` 더미값 생성
9. 이 8개 feature를 Ridge 입력으로 사용

## 7. 예측 결과 항목 설명

### 7.1 `rental_count_pred`

- 해당 시간 예상 대여량
- 내부 계산은 float 유지

### 7.2 `return_count_pred`

- 해당 시간 예상 반납량
- 내부 계산은 float 유지

### 7.3 `bike_change_pred`

- `rental_count_pred - return_count_pred`
- 순변화량

### 7.4 `display`

- 화면 출력용 반올림 정수값
- 내부 계산에는 사용하지 않음

## 8. 왜 내부 계산은 float로 유지하는가

실제 관측 데이터는 정수이지만, 모델의 예측값은 기대값 성격이 강합니다.

따라서 운영 원칙은 아래가 적절합니다.

- 내부 계산: float 유지
- 재귀형 다음 시간 계산: float 유지
- dynamic year_weight 업데이트: float 유지
- 최종 출력: `display`에만 반올림 정수 추가

이렇게 해야 매 시간 반올림으로 인해 누적 오차가 커지는 문제를 줄일 수 있습니다.

## 9. JSON 출력 구조

### 9.1 단일 시점 예측 JSON

```json
{
  "station_id": 2348,
  "station_name": "포스코사거리(기업은행)",
  "datetime": "2026-04-25T16:00:00",
  "input": {
    "year": 2026,
    "month": 4,
    "day": 25,
    "hour": 16
  },
  "prediction": {
    "rental_count_pred": 0.9800,
    "return_count_pred": 0.3849,
    "bike_change_pred": 0.5951
  },
  "display": {
    "rental_count_pred": 1,
    "return_count_pred": 0,
    "bike_change_pred": 1
  }
}
```

### 9.2 재귀형 예측 JSON

재귀형 예측에서는 아래 필드가 추가됩니다.

- `bike_count_from_api_or_prev_step`
- `next_bike_count_pred`
- `forecast`

각 step은 아래 정보를 가집니다.

- 현재 기준 자전거 수량
- 다음 시간 예상 대여량
- 다음 시간 예상 반납량
- 변화량
- 다음 시간 총 대수
- 정수 display 값

## 10. 재귀형 예측 구조

목표는 최대 1주일, 즉 168시간까지 예측하는 것입니다.

### 재귀형 예측 순서

1. 현재 API 자전거 수량을 입력받음
2. 다음 1시간의 `rental_count`, `return_count` 예측
3. `bike_change = rental - return` 계산
4. `next_bike_count = current_bike_count + bike_change`
5. 이 값을 다음 step 입력으로 사용
6. 최대 168시간까지 반복

### 핵심 상태값

- `bike_count_from_api_or_prev_step`
- `next_bike_count_pred`

이 두 값이 재귀 루프를 이어주는 핵심입니다.

## 11. 2026 Dynamic Year Weight 상세 설명

### 문제

현재 `year_weight`는 2023~2025 데이터로만 학습되었습니다.

따라서 2026 이후에는 다음 문제가 생길 수 있습니다.

- 전체 규모 변화
- 대여와 반납의 불균형 변화
- 특정 연도 특유의 운영 패턴 변화

### 해결 방식

운영 중 실제값이 들어오면 `dynamic_year_weight`를 계속 갱신합니다.

즉 최종 예측은 아래처럼 해석할 수 있습니다.

`최종예측 = 기존예측 × dynamic_year_weight`

### 분리 관리 이유

- `rental_count`와 `return_count`는 변화 방향이 다를 수 있음
- 그래서 각각 별도 weight를 둠

예:

```json
{
  "2348": {
    "rental_count": 1.0628,
    "return_count": 0.9704
  }
}
```

## 12. Dynamic Year Weight 업데이트 방식

실제값이 들어오면 아래 값을 계산합니다.

### 12.1 `observed_ratio`

- `actual / predicted`

예:

- 예측 2.0, 실제 3.0 이면 ratio = 1.5
- 예측 2.0, 실제 1.0 이면 ratio = 0.5

### 12.2 `alpha`

- 새 관측값을 얼마나 강하게 반영할지 정하는 값
- 일반적으로 너무 크면 흔들리고, 너무 작으면 적응이 느림

### 12.3 업데이트 식

```python
new_weight = old_weight * (1 - alpha) + observed_ratio * alpha
```

이 방식은 이동평균 형태라서 즉시 반응하면서도 너무 급격하게 흔들리지 않게 합니다.

## 13. Dynamic 보정 결과 JSON 구조

동적 보정 결과는 아래 3개 블록으로 보면 됩니다.

### `before_update_prediction`

- 보정 업데이트 전 예측 결과

### `update_result`

- 실제값 기반 ratio
- alpha
- 새로 업데이트된 dynamic year weight

### `after_update_next_hour_prediction`

- 업데이트된 weight를 반영한 다음 시간 예측 결과

즉 이 JSON 하나로 아래 흐름을 모두 볼 수 있습니다.

- 처음 예측
- 실제값 도착
- 보정 업데이트
- 다음 시간 재예측

## 14. 웹서비스에서 불러와 사용하는 절차

### 서버 시작 시

1. `top6_station_model_store.h5`를 한 번 읽음
2. station별 bundle을 메모리에 적재
3. `dynamic_year_weight` 상태를 별도 저장소에서 읽음

예:

```python
MODEL_REGISTRY = load_model_store("top6_station_model_store.h5")
DYNAMIC_STATE = load_dynamic_state()
```

### 예측 요청 시

1. 요청 JSON 수신
2. `station_id`, `datetime`, `current_bike_count_from_api` 파싱
3. `station_id`로 station bundle 선택
4. 내부 feature 생성
5. 기본 예측 수행
6. `dynamic_year_weight` 반영
7. `bike_change`, `next_bike_count` 계산
8. JSON 응답 반환

### 실제값 수신 시

1. 해당 시점의 예측값 조회
2. 실제 `rental_count`, `return_count` 수신
3. `observed_ratio` 계산
4. `dynamic_year_weight` 업데이트
5. 업데이트 상태 저장

### 다음 예측 시

- 새로 저장된 `dynamic_year_weight`를 반영해서 다시 예측

## 15. 운영 시 저장물 구분

### 고정 파일

- `top6_station_model_store.h5`

### 운영 상태 파일 또는 DB

- `dynamic_year_weight_state.json`
- 또는 DB 테이블

### 선택 로그

- 예측 결과 로그
- 실제값 로그
- 보정 업데이트 로그

## 16. 최종 정리

이 시스템의 핵심은 다음과 같습니다.

- station별 고정 모델은 `h5`에 저장
- 서비스는 서버 시작 시 preload
- 요청마다 `station_id`, `datetime`으로 feature 생성
- 예측은 float로 수행
- 결과는 `prediction`과 `display`를 함께 반환
- API 현재 수량을 이용해 재귀형으로 최대 7일까지 예측
- 실제값이 들어오면 `dynamic_year_weight`를 갱신
- 다음 예측부터 보정 반영

즉, 이 구조는 **고정 학습 모델 + 운영 중 적응형 보정 계층**의 조합입니다.
