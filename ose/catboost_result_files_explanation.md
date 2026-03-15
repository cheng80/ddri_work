# CatBoost 결과 파일 설명

`catboost_rmse_jugeo_dochak_test_predictions_2025.csv`는 모델 성능 요약 파일이 아니라, `2025 test` 데이터에 대해 모델이 실제로 예측한 행별 결과표다.

이 파일에는 보통 이런 의미가 들어 있다.

- `station_id`, `station_name`, `station_group`, `date`, `hour`: 어느 대여소의 언제 시점인지 식별하는 정보
- `actual_rental_count`: test CSV에 들어 있던 실제 대여량
- `predicted_rental_count`: `CatBoostRegressor`가 예측한 대여량
- `residual`: `실제값 - 예측값`

즉 이 CSV는 "모델이 각 시점마다 얼마나 맞췄는지"를 보는 용도다.

반면 `catboost_rmse_jugeo_dochak_metrics.json`은 전체 성능을 요약한 결과 파일이다. 여기에는 `RMSE`, `MAE`, `R²`, 행 수 같은 집계 지표만 담겨 있다.

정리하면 아래와 같다.

- `catboost_rmse_jugeo_dochak_test_predictions_2025.csv`: 상세 예측 결과표
- `catboost_rmse_jugeo_dochak_metrics.json`: 모델 성능 요약표

`ose` 경로를 최종 저장 위치로 쓸 경우, 앞으로도 같은 형식으로 결과 파일과 설명 문서를 함께 정리하면 다시 보기 편하다.
