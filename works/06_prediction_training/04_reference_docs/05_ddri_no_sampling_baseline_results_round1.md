# DDRI 무샘플링 기준선 결과 1차 기록

작성일: 2026-03-17

## 0. 적용 기준

이번 기록은 `cluster` 불일치 문제를 보정한 뒤 다시 생성한 정본과 모델링 데이터를 기준으로 한다.

- `rep15`, `full161` 모두 `train 2023-2024` 기준 `station_id -> cluster` 매핑을 마스터로 사용
- `test 2025`의 잘못된 `cluster` 값은 재부착하여 보정
- 이후 `canonical_data`, `modeling_data`, `training_runs`를 다시 생성

## 1. 목적

샘플링 없이 정본 전체를 사용했을 때의 기준선 성능을 먼저 기록한다.

이 결과는 이후:

- 가중치 방식
- 일단위 대표일 추출
- 기타 삭제형 샘플링

과 비교하는 1차 기준선이다.

## 2. 실행 범위

아래 4개 조합을 모두 실행했다.

- `rep15 + bike_change_raw`
- `rep15 + bike_change_deseasonalized`
- `full161 + bike_change_raw`
- `full161 + bike_change_deseasonalized`

공통 조건:

- 샘플링 없음
- 정본 행 삭제 없음
- `2023` 학습
- `2024` 검증
- 검증 기준 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

## 3. 결과 요약

| dataset | target | best model | valid RMSE | valid MAE | valid R² | test RMSE | test MAE | test R² |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| rep15 | bike_change_raw | LightGBM_RMSE | 0.381777 | 0.143463 | 0.933885 | 0.309620 | 0.121293 | 0.946012 |
| rep15 | bike_change_deseasonalized | LightGBM_RMSE | 0.372257 | 0.140486 | 0.925913 | 0.306413 | 0.118805 | 0.941617 |
| full161 | bike_change_raw | LightGBM_RMSE | 0.314080 | 0.129130 | 0.948969 | 0.263338 | 0.105791 | 0.955216 |
| full161 | bike_change_deseasonalized | LightGBM_RMSE | 0.309577 | 0.126492 | 0.946228 | 0.259210 | 0.104047 | 0.954493 |

## 4. 1차 해석

- 4개 조합 모두 `LightGBM_RMSE`가 우세했다.
- `bike_change_deseasonalized`는 `RMSE`, `MAE` 기준으로 더 좋게 나왔다.
- `bike_change_raw`는 `R²`가 약간 더 높게 유지되는 경향이 있었다.
- `full161`이 `rep15`보다 전체적으로 더 낮은 오차를 보였다.
- 군집 보정 후에도 전체 결론은 유지됐다. 즉, `LightGBM_RMSE` 우세와 `deseasonalized`의 오차 우세 경향은 그대로다.

## 5. 현재 판단

현재 기준으로는 아래 해석이 가능하다.

- 오차 최소화를 더 중시하면 `bike_change_deseasonalized`가 유리하다.
- 설명력 `R²`를 함께 보면 `bike_change_raw`도 버릴 정도로 약하지 않다.
- 따라서 샘플링 실험은 두 타깃 중 하나만 바로 고정하기보다,
  우선 `bike_change_deseasonalized`를 1순위 후보로 두고 비교를 이어가는 것이 합리적이다.

## 6. 다음 단계

다음 실험은 샘플링 1안으로 진행한다.

샘플링 1안:

- 정본은 유지
- `2023 train`만 대상으로 함
- 같은 `station_id`, 같은 `weekday` 안에서
- 일단위 24시간 프로파일을 비교
- 유사한 일들은 대표일 1개만 남기는 방식

즉, 주단위/월단위 연쇄 삭제가 아니라
`일단위 대표일 추출`만 소규모로 시작한다.
