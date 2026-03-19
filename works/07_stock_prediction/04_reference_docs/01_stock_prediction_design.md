# station_hour_bike_flow 기반 재고 예측 모델 설계 메모

## 목적

현재 재고와 단기 누적 순변화 예측을 결합해 `h시간 뒤` 재고를 계산하는 운영형 회귀식을 준비한다.

## 기존 모델과의 관계

- 기존 Ridge 보고서 모델:
  - canonical 기반
  - `bike_change_raw` 예측
  - 해석과 분석 보고서 목적
- 신규 모델:
  - `station_hour_bike_flow` 기반
  - `h시간 뒤 누적 순변화` 예측
  - 운영 적용 목적

기존 모델은 폐기하지 않고 `분석용 기준 모델`로 유지한다.

## 타깃 정의

### 권장 1차 타깃

- `target_net_change_h = bike_count_index(t+h) - bike_count_index(t)`

또는 같은 의미로

- `target_net_change_h = sum(bike_change(t+1) ... bike_change(t+h))`

여기서 `h`는 입력 변수(`horizon_hours`)로 함께 들어간다.

장점:
- 하나의 회귀식으로 `2시간`, `3시간`, `6시간`을 모두 처리 가능
- 운영 API에서 `horizon_hours`만 바꾸면 됨
- 수식 형태로 설명하기 쉽다

단점:
- horizon별 오차 특성이 달라서 검증을 더 꼼꼼히 봐야 한다

## 피처 후보

### 현재 흐름

- `rental_count(t)`
- `return_count(t)`
- `bike_change(t)`
- `bike_count_index(t)`
- `current_stock` (운영 추론 시 실시간 API 입력)

### 최근 이력

- `bike_change_lag_1`
- `bike_change_lag_2`
- `bike_count_index_lag_1`
- `bike_count_index_lag_2`
- `rental_count_lag_1`
- `return_count_lag_1`
- `bike_change_rollmean_3`
- `bike_change_rollstd_3`
- `bike_change_rollmean_6`
- `bike_change_rollstd_6`
- `bike_change_rollmean_24`
- `bike_change_rollstd_24`

### 시간 정보

- `hour`
- `weekday`
- `month`
- `horizon_hours`
- `horizon_hours_sq`
- `is_commute_hour`
- `is_lunch_hour`
- `is_night_hour`
- `is_weekend`

### 외생 변수

- `temperature`
- `humidity`
- `precipitation`
- `wind_speed`

### 대여소 정적 정보

- `station_id`
- `cluster`
- 필요시 위치/유형 정보

## 운영 계산식

### 일반식

- `pred_net_change_h = F(x, h)`
- `stock_t_plus_h = current_stock + pred_net_change_h`

여기서

- `x` = 현재 재고, 현재 대여/반납 상태, 최근 이력, 시간/날씨/대여소 정보
- `h` = 사용자가 요청한 미래 시간

## 다음 단계

1. `station_hour_bike_flow`에서 `h시간 뒤 누적 순변화` 타깃 생성
2. horizon-conditioned long dataset 생성
3. weather 조인 가능 여부 확인
4. baseline 모델 정의
5. horizon별 성능 평가
6. 실시간 API 입력 스키마 연결

## 개발 형식

- 실험 진행은 노트북 1개로 통합한다.
- 노트북 이름:
  - `01_stock_prediction_end_to_end.ipynb`
- 이 노트북이 아래를 모두 담당한다.
  - 데이터 점검
  - `h시간 뒤 누적 순변화` 타깃/피처 생성
  - horizon-conditioned 데이터셋 생성
  - 모델 학습과 검증
  - 모델 export
  - 리포트용 표/차트 생성

## 배포 관점

- Flutter는 `joblib`를 직접 읽지 않는다.
- Python 추론 서버가 `joblib`를 로드하고,
- Flutter는 현재 재고와 대여소 정보를 담은 요청을 서버에 보내는 구조를 전제로 한다.
