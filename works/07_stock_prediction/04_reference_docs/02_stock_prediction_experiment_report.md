# station_hour_bike_flow 기반 재고 예측 실험 보고서

## 목적

`현재 재고 + 예측 누적 순변화` 계산 구조를 기준으로 `h시간 뒤` 재고 예측에 필요한 운영형 모델을 구축한다.

## 데이터

- 원천: `station_hour_bike_flow_2023_2025`
- 단위: `station_id + hour`
- 핵심 컬럼:
  - `rental_count`
  - `return_count`
  - `bike_change`
  - `bike_count_index`

## 타깃 정의

- `h시간 뒤 누적 순변화`

예:

- `target_net_change_h = bike_count_index(t+h) - bike_count_index(t)`

최종 정의는 end-to-end 노트북 실행 결과에 따라 갱신한다.

## 피처 정의

- 현재 흐름
- 최근 이력
- 시간 정보
- 날씨
- 대여소 정적 정보

세부 피처 목록은 노트북 산출 기준으로 갱신한다.

## 실험 결과

추후 기록:

- 모델 종류
- 학습 구간
- 검증 구간
- 테스트 구간
- RMSE
- MAE
- R²

## 배포 산출물

- `stock_model_horizon.joblib`
- `model_input_schema.json`
- `model_metadata.json`

## Flutter 연동 메모

- Flutter 입력:
  - `station_id`
  - `current_stock`
  - `request_time`
  - `horizon_hours`
- 서버 내부에서 피처를 생성하고 `joblib` 모델로 추론한다.
- 최종 계산:
  - `stock_t_plus_h = current_stock + pred_net_change_h`
