# 난지 주차 수요 예측과 외부데이터 정제

이 폴더는 난지권 주차 또는 캠핑 수요 예측에 필요한 기본 ML 파이프라인과 외부데이터 수집/정제 보조 스크립트를 담고 있습니다.

현재 구성은 두 갈래입니다.

1. `run_nanji_parking_pipeline.py`
   - 주차 가용면수 CSV를 읽어 feature engineering, 학습, 평가, 예측 출력까지 수행합니다.
2. `collect_external_data.py` + `prepare_external_datasets.py`
   - 원천 링크와 API 후보를 정리하고, `2023`, `2024`, `2025` 연도 기준으로 결측치와 이상치를 제거한 정제본을 만듭니다.

## 주요 파일

- `data/nanji_parking_input_template.csv`
  - 모델 입력 예시 템플릿
- `external_data_plan/source_catalog.csv`
  - 캠핑장, 날씨, 특일, 공연정보 소스 목록
- `external_data_plan/request_plan.json`
  - 확인한 링크와 API 메모
- `prepare_external_datasets.py`
  - `raw` 폴더의 CSV/XLS/XLSX를 읽어 `processed` 폴더에 정제 결과 저장

## 모델 입력 최소 스키마

입력 CSV에는 아래 컬럼이 필요합니다.

- `timestamp`
- `total_spaces`
- `available_spaces` 또는 `occupied_spaces`

있으면 좋은 컬럼은 아래와 같습니다.

- `parking_lot_id`
- `parking_lot_name`
- `is_holiday`
- `weather_temp_c`
- `weather_precip_mm`
- `weather_humidity`
- `event_flag`

## 외부데이터 정제 흐름

1. 원본 파일을 `external_data_plan/data/raw/` 아래에 넣습니다.
2. 아래 명령으로 수집 계획 파일을 다시 생성합니다.

```powershell
python yeeun\nanji_parking_ml\collect_external_data.py
```

3. 아래 명령으로 `2023~2025` 데이터만 남기고 결측치/이상치를 제거합니다.

```powershell
python yeeun\nanji_parking_ml\prepare_external_datasets.py `
  --input-dir yeeun\nanji_parking_ml\external_data_plan\data\raw `
  --output-dir yeeun\nanji_parking_ml\external_data_plan\data\processed `
  --years 2023 2024 2025
```

4. 결과는 아래 파일로 저장됩니다.

- `cleaning_summary.csv`
- `cleaning_summary.json`
- `{원본파일명}_cleaned.csv`

## 모델 실행 예시

```powershell
python yeeun\nanji_parking_ml\run_nanji_parking_pipeline.py `
  --input yeeun\nanji_parking_ml\data\nanji_parking_input_template.csv `
  --output-dir yeeun\nanji_parking_ml\outputs
```

## 현재 반영한 외부데이터 후보

- 마포구 캠핑장 현황 파일데이터
- 기상자료개방포털 Open API
- Open-Meteo 이력 기상 API
- 공공데이터포털 특일 정보 API
- KOPIS 공연목록 API
- KOPIS 공연시설목록 API
- 한강공원 이용 패턴 논문 참고자료
