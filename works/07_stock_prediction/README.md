# 07 Stock Prediction

이 폴더는 `station_hour_bike_flow` 기반의 운영형 재고 예측 모델 작업 공간이다.

목표는 `현재 재고 + 예측 누적 순변화` 방식으로 `h시간 뒤` 재고를 계산할 수 있는 단일 회귀식을 준비하는 것이다.

## 작업 원칙

- 기존 `05_prediction_canonical`, `06_prediction_training`은 분석용 수요 변화 모델 경로로 유지한다.
- 이 경로는 운영 적용을 위한 `재고/누적 순변화 예측`에 집중한다.
- 1차 타깃은 `시간별 단일 변화량`이 아니라 `h시간 뒤 누적 순변화`로 잡는다.
- `horizon_hours`를 입력으로 받는 단일 회귀식 구조를 지향한다.
- 실시간 API의 현재 재고를 시작점으로 받아 최종 재고를 계산하는 구조를 전제로 한다.

## 폴더 구분

- `01_notebook`
  - 최종 end-to-end 노트북 1개를 중심으로 작업
- `02_input_data`
  - 입력 데이터 안내
- `03_output_data`
  - 생성 산출물 안내
- `04_reference_docs`
  - 설계 문서와 정책 메모
- `05_scripts`
  - 데이터셋 점검 및 모델링 스크립트

## 현재 결론

- `station_hour_bike_flow`에는 `rental_count`, `return_count`, `bike_change`, `bike_count_index`가 있다.
- `bike_change = return_count - rental_count`가 성립한다.
- `bike_count_index`는 절대 재고량이 아니라 누적 순변화 지표로 해석된다.
- 따라서 현재 공개 데이터만으로는 `절대 재고`보다 `누적 순변화` 회귀식이 더 자연스럽다.
- `h=2`, `h=3`, `h=6`을 각각 따로 학습하기보다 `h`를 입력으로 넣으면 결과가 나오는 모델이 목표다.

## 작업 방식

- 개발 중심 문서는 아래 노트북 1개로 통합한다.
  - `01_notebook/01_stock_prediction_end_to_end.ipynb`
- 이 노트북 안에서 아래 흐름을 모두 수행한다.
  - 데이터 로드
  - `h시간 뒤 누적 순변화` 타깃 생성
  - horizon-conditioned long dataset 생성
  - 피처 생성
  - baseline 학습
  - 최종 모델 선택
  - `joblib` 모델 저장
  - 입력 스키마 저장
  - 리포트용 표와 차트 생성

## 최종 산출물 목표

- 모델 파일
  - `stock_model_horizon.joblib`
- 메타데이터
  - `model_input_schema.json`
  - `model_metadata.json`
- 리포트
  - `02_stock_prediction_experiment_report.md`
- 필요시 추론 예시
  - `sample_inference_request.json`
  - `sample_inference_response.json`
