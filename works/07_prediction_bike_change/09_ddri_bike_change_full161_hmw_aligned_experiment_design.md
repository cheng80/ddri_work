# DDRI bike_change full161 HMW 정렬 실험 설계

작성일: 2026-03-16  
목적: `bike_change` 실험을 `rep15` 대표 대여소 기준이 아니라, 서비스 대상 `161개` 전체 대여소 기준으로 다시 비교할 수 있도록 HMW와 정렬된 실험 축을 정의한다.

## 1. 왜 이 실험이 필요한가

기존 `rep15` 실험은 대표 15개 대여소 기준이다.  
반면 HMW 전체재학습 실험은 `station_hour_bike_flow` 원본을 기반으로 전체 서비스 범위를 다루는 축에 가깝다.

따라서 아래 문제를 분리해서 보려면 `161개 전체 대여소` 기준 실험이 필요하다.

- 성능 차이가 `대표 대여소(rep15)` 때문인가
- 성능 차이가 `피처셋 차이` 때문인가
- 성능 차이가 `모델군 차이` 때문인가

## 2. 이번 실험의 고정 기준

- 대상 대여소:
  - `cheng80/api_output/ddri_station_id_api_lookup.csv` 기준 `161개`
- 입력 원본:
  - `3조 공유폴더/station_hour_bike_flow_2023_2025/station_hour_bike_flow_train_2023_2024.csv`
  - `3조 공유폴더/station_hour_bike_flow_2023_2025/station_hour_bike_flow_test_2025.csv`
- 타깃:
  - `bike_change`
- 피처셋:
  - HMW 회귀앙상블 스크립트와 동일한 lag/time 기반 피처
- 모델군:
  - `Ridge`
  - `RandomForest`
  - `ExtraTrees`
  - `GradientBoosting`
  - `AdaBoost`
  - `BaggingTree`
  - `SoftVoting`
  - `Stacking`

## 3. 서비스 대상 161개와 원본 flow 파일의 관계

`station_hour_bike_flow` 원본 파일에는 `182개 station_id`가 들어 있다.  
하지만 서비스 대상은 `161개`로 고정되어 있으므로, 이번 실험은 원본 전체를 쓰지 않고 lookup 기준으로 먼저 필터링한다.

즉 이번 실험은 아래 의미를 가진다.

- 원본 flow 피처 체계는 유지
- 서비스 대상 161개만 남김
- HMW와 동일한 축의 `bike_change` 비교 실험으로 사용

## 4. split 기준

- `train_2023`
  - 2023년
- `validation_2024`
  - 2024년
- `test_2025_refit`
  - 2023~2024 전체로 재학습 후 2025 평가

## 5. 이번 실험에서 보는 것

1. HMW 정렬 피처셋 기준으로 `161개 bike_change`에서 어떤 회귀앙상블이 가장 안정적인가
2. `rep15 + full_36 + LightGBM_RMSE`와 비교했을 때 전체 확장 시 난이도가 얼마나 커지는가
3. HMW 계열의 단순 lag/time 피처만으로 전체 서비스 대상에서도 baseline이 성립하는가

## 6. 산출물

- `ddri_bike_change_full161_hmw_aligned_model_metrics.csv`
- `ddri_bike_change_full161_hmw_aligned_residual_summary.csv`
- `ddri_bike_change_full161_hmw_aligned_top100_errors.csv`
- `ddri_bike_change_full161_hmw_aligned_rmse.png`
- `ddri_bike_change_full161_hmw_aligned_summary.md`
- `ddri_bike_change_full161_hmw_aligned_meta.json`

## 7. 해석 원칙

- 이 실험은 `최종 운영 모델 확정`보다 `비교축 정렬`이 목적이다
- 따라서 `rep15` 결과와 숫자만 단순 비교하지 않고, 범위와 피처 구조 차이를 함께 읽는다
- 이후 필요하면 다음 비교로 확장한다
  - `161개 + HMW 피처셋 + 회귀앙상블`
  - `161개 + richer feature set + LightGBM`
  - `161개 + cluster/정적 피처 추가`
