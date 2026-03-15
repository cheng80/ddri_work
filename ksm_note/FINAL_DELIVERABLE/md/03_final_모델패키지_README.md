# 외곽 Top3 최종 모델 패키지 결과

- 모델: LightGBM_RMSE
- feature: baseline + is_weekend
- 전처리: hour/weekday/month 원핫 인코딩
- 예측 대상: 2025
- 혼동행렬 클래스: 0 / 1 / 2 / 3+
- 추가 혼동행렬 클래스: 0 / 1 / 2 / 3 / 4 / ... (정확 건수)

## 클래스 의미 설명
- `0`: 해당 시간대 실제(또는 예측) 대여건수가 0건
- `1`: 1건
- `2`: 2건
- `3`: 3건
- `4`: 4건
- 즉 `0,1,2,3,4`는 대여건수 그 자체를 뜻한다.
- 기존 `3+`는 3건 이상을 하나로 묶은 버킷 클래스다.

## 대여소별 성능 요약
|   station_id | station_name                         | model         | feature_strategy                                    |     rmse |      mae |        r2 |   exact_match_hits_rounded |   exact_match_rate_rounded |   n_samples_test |   n_model_features_after_onehot |
|-------------:|:-------------------------------------|:--------------|:----------------------------------------------------|---------:|---------:|----------:|---------------------------:|---------------------------:|-----------------:|--------------------------------:|
|         2359 | 국립국악중,고교 정문 맞은편          | LightGBM_RMSE | baseline + is_weekend (one-hot: hour/weekday/month) | 0.922901 | 0.649356 |  0.329876 |                       4629 |                   0.528425 |             8760 |                              56 |
|         2392 | 구룡산 입구 (구룡산 서울둘레길 입구) | LightGBM_RMSE | baseline + is_weekend (one-hot: hour/weekday/month) | 0.286323 | 0.145926 | -0.043669 |                       8121 |                   0.927055 |             8760 |                              56 |
|         3643 | 더시그넘하우스 앞                    | LightGBM_RMSE | baseline + is_weekend (one-hot: hour/weekday/month) | 0.810575 | 0.566583 |  0.248748 |                       5109 |                   0.583219 |             8760 |                              56 |

## 정확도 요약(전체)
- 정수 반올림 정확일치(실제 건수 == 예측 건수): `67.96%` (`17,859 / 26,280`)
- 버킷 기준 정확도(0/1/2/3+): `68.25%` (`17,937 / 26,280`)

대여소별 정수 반올림 정확일치:
- `2359`: `52.84%` (`4,629 / 8,760`)
- `2392`: `92.71%` (`8,121 / 8,760`)
- `3643`: `58.32%` (`5,109 / 8,760`)

## Train / Valid / Test 점수표
분할 정책:
- `train_2023`: 2023 데이터
- `validation_2024`: 2023으로 학습한 모델을 2024에 평가
- `test_2025_refit`: 2023+2024 재학습 모델을 2025에 평가

전체(Top3 통합):

| split | RMSE | MAE | R2 | exact_match_hits_rounded | exact_match_rate_rounded | n_samples |
|---|---:|---:|---:|---:|---:|---:|
| train_2023 | 0.542548 | 0.344375 | 0.711956 | 19,810 | 0.753805 | 26,280 |
| validation_2024 | 0.809750 | 0.512763 | 0.293770 | 17,091 | 0.648566 | 26,352 |
| test_2025_refit | 0.728185 | 0.453955 | 0.357147 | 17,859 | 0.679566 | 26,280 |

대여소별:

| station_id | station_name | split | train_policy | RMSE | MAE | R2 | exact_match_hits_rounded | exact_match_rate_rounded | n_samples |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 2359 | 국립국악중,고교 정문 맞은편 | train_2023 | train_on_2023 | 0.665264 | 0.474931 | 0.683059 | 5,575 | 0.636416 | 8,760 |
| 2359 | 국립국악중,고교 정문 맞은편 | validation_2024 | train_on_2023 | 1.004942 | 0.706606 | 0.194521 | 4,411 | 0.502163 | 8,784 |
| 2359 | 국립국악중,고교 정문 맞은편 | test_2025_refit | train_on_2023_2024_refit | 0.922901 | 0.649356 | 0.329876 | 4,629 | 0.528425 | 8,760 |
| 2392 | 구룡산 입구 (구룡산 서울둘레길 입구) | train_2023 | train_on_2023 | 0.252745 | 0.134568 | 0.559197 | 8,173 | 0.932991 | 8,760 |
| 2392 | 구룡산 입구 (구룡산 서울둘레길 입구) | validation_2024 | train_on_2023 | 0.352805 | 0.197235 | 0.010485 | 7,941 | 0.904030 | 8,784 |
| 2392 | 구룡산 입구 (구룡산 서울둘레길 입구) | test_2025_refit | train_on_2023_2024_refit | 0.286323 | 0.145926 | -0.043669 | 8,121 | 0.927055 | 8,760 |
| 3643 | 더시그넘하우스 앞 | train_2023 | train_on_2023 | 0.613694 | 0.423628 | 0.698420 | 6,062 | 0.692009 | 8,760 |
| 3643 | 더시그넘하우스 앞 | validation_2024 | train_on_2023 | 0.912527 | 0.634447 | 0.274666 | 4,739 | 0.539504 | 8,784 |
| 3643 | 더시그넘하우스 앞 | test_2025_refit | train_on_2023_2024_refit | 0.810575 | 0.566583 | 0.248748 | 5,109 | 0.583219 | 8,760 |

원본 파일:
- `cluster04_station_top3_split_scores_overall.csv`
- `cluster04_station_top3_split_scores_by_station.csv`
- `cluster04_station_top3_split_scores.md`

## 궁극 목표(재배치) 반영 여부
질문한 목표인  
`수요가 많은 대여소/여유 대여소에서 자전거를 빼서, 특정 시간대에 부족 대여소로 재배치`  
관점에서 보면, 현재 결과는 **부분 반영** 상태다.

- 현재 반영된 것:
  - 시간대별 수요(대여건수) 예측
  - 대여소별 부족/여유 신호를 판단할 기초 예측값 생성
- 아직 미반영된 것:
  - 대여소별 실시간 재고(보유 대수)
  - 최소/목표 재고 정책(안전재고)
  - 이동 가능한 차량/인력 제약
  - 이동 거리/시간/비용을 고려한 최적 재배치 경로

즉, 지금 모델은 `어디가 필요할지 예측` 단계이고,  
`어디서 몇 대를 빼서 어디로 몇 대를 보낼지`를 결정하는 최적화 단계는 다음 작업이다.

재배치 의사결정으로 바로 연결하려면 아래 산식이 추가로 필요하다.
- 필요량(부족량) = `max(0, 목표재고 - (현재재고 + 예측순유입))`
- 여유량 = `max(0, (현재재고 + 예측순유입) - 목표재고)`
- 이후 `여유 대여소 -> 부족 대여소` 매칭을 비용 최소화(거리/시간/차량수)로 최적화

## 통합 혼동행렬
### 버킷 클래스(0/1/2/3+)
![cluster04 top3 confusion](images/cluster04_station_top3_confusion_matrix_all.png)

### 정확 개수 클래스(0/1/2/3/4/...)
![cluster04 top3 confusion exact](images/cluster04_station_top3_confusion_matrix_all_exact_counts.png)

## 산출물 목록
- `cluster04_station_top3_final_metrics_summary.csv`
- `cluster04_station_top3_predictions_2025_all.csv`
- `cluster04_station_top3_confusion_matrix_all.csv`
- `cluster04_station_top3_confusion_matrix_all_exact_counts.csv`
- `images/cluster04_station_top3_confusion_matrix_all.png`
- `images/cluster04_station_top3_confusion_matrix_all_exact_counts.png`
- `station_2359_predictions_2025.csv`
- `station_2359_confusion_matrix.csv`
- `station_2359_confusion_matrix_exact_counts.csv`
- `images/station_2359_confusion_matrix.png`
- `images/station_2359_confusion_matrix_exact_counts.png`
- `station_2392_predictions_2025.csv`
- `station_2392_confusion_matrix.csv`
- `station_2392_confusion_matrix_exact_counts.csv`
- `images/station_2392_confusion_matrix.png`
- `images/station_2392_confusion_matrix_exact_counts.png`
- `station_3643_predictions_2025.csv`
- `station_3643_confusion_matrix.csv`
- `station_3643_confusion_matrix_exact_counts.csv`
- `images/station_3643_confusion_matrix.png`
- `images/station_3643_confusion_matrix_exact_counts.png`
