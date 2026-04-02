# 난지 한강공원 주차장 예측 시작점

이 폴더는 난지 한강공원 주차장 빈자리 예측 프로젝트의 첫 골격입니다.

목표는 아래 4가지를 한 번에 연결하는 것입니다.

1. 주차장 원천 데이터를 읽는다.
2. 시간대 기반 feature를 만든다.
3. 머신러닝 모델을 학습하고 성능을 비교한다.
4. Swift 앱, Flutter Web, DB에 넣기 쉬운 예측 결과 CSV를 만든다.

## 현재 포함된 파일

- `run_nanji_parking_pipeline.py`
  - 입력 CSV를 읽고 feature engineering, 학습, 평가, 예측 결과 저장까지 수행
- `data/nanji_parking_input_template.csv`
  - 원천 데이터 템플릿
- `DATA_SOURCES.md`
  - 공식 데이터 소스와 추천 활용 방법 정리
- `collect_external_data.py`
  - 외부 데이터 수집 계획용 폴더와 메타 파일 생성

## 입력 데이터 규칙

입력 CSV는 최소한 아래 컬럼을 가져야 합니다.

- `timestamp`
  - 예: `2026-04-01 13:00:00`
- `total_spaces`
  - 전체 주차 가능 면수
- `available_spaces` 또는 `occupied_spaces`
  - 둘 중 하나는 반드시 있어야 함

있으면 좋은 컬럼:

- `parking_lot_id`
  - 예: `nanji_main`
- `parking_lot_name`
  - 예: `난지 한강공원 제1주차장`
- `is_holiday`
  - 공휴일이면 `1`, 아니면 `0`
- `weather_temp_c`
- `weather_precip_mm`
- `weather_humidity`
- `event_flag`
  - 행사일, 축제일, 야구 경기일 같은 특이일 표시

## 예측 타깃

현재 기본 타깃은 `available_spaces`입니다.

이유:

- 사용자에게 "지금 또는 곧 빈자리 몇 칸인지"를 직접 보여주기 쉽습니다.
- DB 저장 시 `predicted_available_spaces`, `predicted_occupied_spaces`, `predicted_occupancy_rate`를 같이 만들기 좋습니다.

## 생성되는 출력 파일

스크립트를 실행하면 `outputs/` 아래에 다음 파일이 생깁니다.

- `model_metrics.csv`
  - 모델별 RMSE, MAE, R2
- `test_predictions.csv`
  - 테스트 구간 실제값 vs 예측값
- `feature_importance.csv`
  - 랜덤포레스트 기준 중요 feature
- `db_prediction_output.csv`
  - 앱/웹/DB 적재용 예측 결과

## 실행 방법

PowerShell 기준 예시입니다.

```powershell
python yeeun\nanji_parking_ml\run_nanji_parking_pipeline.py `
  --input yeeun\nanji_parking_ml\data\nanji_parking_input_template.csv `
  --output-dir yeeun\nanji_parking_ml\outputs
```

외부 데이터 수집 계획 골격을 만드는 명령은 아래와 같습니다.

```powershell
python yeeun\nanji_parking_ml\collect_external_data.py `
  --output-dir yeeun\nanji_parking_ml\external_data_plan
```

## DB 적재용 출력 스키마

`db_prediction_output.csv`는 아래 컬럼을 만듭니다.

- `parking_lot_id`
- `parking_lot_name`
- `predicted_for`
- `actual_available_spaces`
- `predicted_available_spaces`
- `predicted_occupied_spaces`
- `predicted_occupancy_rate`
- `model_name`
- `created_at`

이 포맷이면 나중에 다음 연결이 쉬워집니다.

- Swift 앱: JSON으로 변환 후 최근 예측 목록 표시
- Flutter Web: 차트/테이블/색상 상태 표시
- DB: `parking_predictions` 테이블에 적재

## 다음 단계 제안

이 골격 다음에는 아래 순서로 가면 됩니다.

1. 난지 한강공원 실제 주차장 CSV 확보
2. 공휴일, 날씨, 행사일 데이터 결합
3. 1시간 뒤, 2시간 뒤, 3시간 뒤 다중 horizon 예측으로 확장
4. FastAPI 또는 Flask로 예측 API 생성
5. Swift 앱과 Flutter Web에서 같은 DB 또는 API 사용
