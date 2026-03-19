# Output Data

이 폴더에는 end-to-end 노트북 실행 결과를 둔다.

## 우선 산출 목표

- 최종 모델
  - `stock_model_horizon.joblib`
- 입력 스키마
  - `model_input_schema.json`
- 모델 메타데이터
  - `model_metadata.json`
- 리포트용 메트릭
  - `metrics_by_horizon.csv`
- 예측 샘플
  - `predictions_by_horizon.csv`
- 중요 피처 요약
  - `feature_importance_horizon.csv`

## 선택 산출

- horizon별 학습 데이터셋
  - `stock_horizon_train.csv`
- Flutter / API 예시
  - `sample_inference_request.json`
  - `sample_inference_response.json`
