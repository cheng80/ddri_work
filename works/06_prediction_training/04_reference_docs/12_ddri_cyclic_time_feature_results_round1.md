# DDRI 시간·요일 원형 인코딩 결과 1차 기록

작성일: 2026-03-17

## 1. 실행 범위

이번 1차 실행은 아래 두 조건으로 수행했다.

- dataset: `rep15`
- dataset: `full161`
- target: `bike_change_deseasonalized`
- 비교 방식:
  - 기준선: 기존 피처 그대로 사용
  - 원형 인코딩 추가: `hour_sin`, `hour_cos`, `weekday_sin`, `weekday_cos` 4개 추가

학습 정책은 기존과 동일하다.

- `2023` 학습
- `2024` 검증
- 검증 기준 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

## 2. 추가된 피처

원형 인코딩 조건에서만 추가한 피처:

- `hour_sin`
- `hour_cos`
- `weekday_sin`
- `weekday_cos`

피처 수 변화:

- 기준선: `31`
- 원형 인코딩 추가: `35`

## 3. Validation 결과 비교

### 3-1. rep15

| variant | best model | RMSE | MAE | R² |
|---|---|---:|---:|---:|
| baseline | LightGBM_RMSE | 0.372257 | 0.140486 | 0.925913 |
| cyclic | LightGBM_RMSE | 0.373468 | 0.145003 | 0.925431 |

### 3-2. full161

| variant | best model | RMSE | MAE | R² |
|---|---|---:|---:|---:|
| baseline | LightGBM_RMSE | 0.309577 | 0.126492 | 0.946228 |
| cyclic | LightGBM_RMSE | 0.310344 | 0.129322 | 0.945961 |

## 4. Test 결과 비교

### 4-1. rep15

| variant | best model | RMSE | MAE | R² |
|---|---|---:|---:|---:|
| baseline | LightGBM_RMSE | 0.306413 | 0.118805 | 0.941617 |
| cyclic | LightGBM_RMSE | 0.306828 | 0.121238 | 0.941459 |

### 4-2. full161

| variant | best model | RMSE | MAE | R² |
|---|---|---:|---:|---:|
| baseline | LightGBM_RMSE | 0.259210 | 0.104047 | 0.954493 |
| cyclic | LightGBM_RMSE | 0.259574 | 0.105832 | 0.954365 |

## 5. 1차 해석

- 원형 인코딩 4개를 추가해도 우세 모델은 그대로 `LightGBM_RMSE`였다.
- `rep15`, `full161` 모두 validation, test에서 기준선보다 약간 불리했다.
- 특히 두 데이터셋 모두 `MAE`가 더 나빠졌고, `RMSE`, `R²`도 개선되지 않았다.

즉, 현재 조건에서는 시간·요일 원형 인코딩을 추가할 실익이 확인되지 않았다.

## 6. 현재 판단

1. `rep15`, `full161` 모두 `bike_change_deseasonalized` 기준으로는 원형 인코딩 4개를 채택하지 않는다.
2. `LightGBM` 트리 모델은 기존 `hour`, `weekday` 정수값만으로도 충분히 처리하는 것으로 해석할 수 있다.
3. 필요하면 아래 경우에만 추가 확인한다.

- 선형 모델 중심 비교를 별도로 하는 경우
- `bike_change_raw` 타깃에서도 별도 비교가 필요한 경우

현재 기준으로는 **무샘플링 기준선 유지**가 더 타당하다.
