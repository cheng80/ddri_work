# DDRI `cluster` 컬럼 일관성 문제 점검 및 보정

작성일: 2026-03-17

## 1. 결론

원천 `OLD_DATA`에서는 `cluster` 컬럼이 **train 2023-2024와 test 2025 사이에서 일관되지 않았다.**

현재는 아래 방식으로 보정이 끝난 상태다.

- `train 2023-2024` 기준 `station_id -> cluster` 매핑을 마스터로 사용
- `test 2025`의 `cluster` 값을 동일 매핑으로 다시 부착
- `canonical_data`, `modeling_data`, `training_runs`를 다시 생성

## 2. 확인 기준

비교한 파일:

- [OLD_DATA train](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/OLD_DATA/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_train_2023_2024.csv)
- [OLD_DATA test](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/OLD_DATA/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_test_2025.csv)
- [canonical train](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/대표대여소_예측데이터_15개/canonical_data/ddri_prediction_canonical_train_2023_2024.csv)
- [canonical test](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/대표대여소_예측데이터_15개/canonical_data/ddri_prediction_canonical_test_2025.csv)

원천 비교 결과:

- `OLD_DATA train`과 `OLD_DATA test`의 `cluster` 값이 서로 달랐다.
- 문제는 정본 생성 과정이 아니라 **원천 입력의 train/test 라벨 불일치**였다.
- 이후 정본 생성기에서 train 기준 마스터 매핑을 사용하도록 수정했다.

## 3. 실제 차이

`rep15` 기준 군집 분포:

### train 2023-2024

- cluster 0: 3개
- cluster 1: 3개
- cluster 2: 3개
- cluster 3: 3개
- cluster 4: 3개

### test 2025

- cluster 0: 6개
- cluster 1: 1개
- cluster 2: 3개
- cluster 3: 3개
- cluster 4: 2개

즉, 군집 수 자체는 같지만 스테이션의 라벨이 일부 바뀌어 있다.

## 4. 라벨이 바뀐 스테이션

train/test 비교 시 `cluster`가 달라진 스테이션:

| station_id | station_name | train cluster | test cluster |
|---|---|---:|---:|
| 2323 | 주식회사 오뚜기 정문 앞 | 1 | 0 |
| 2354 | 청담역 2번출구 | 2 | 3 |
| 2377 | 수서역 5번출구 | 1 | 0 |
| 2392 | 구룡산 입구 (구룡산 서울둘레길 입구) | 4 | 0 |
| 3616 | 역삼중학교 앞(체육관 방향) | 3 | 2 |

## 5. 왜 중요한가

이 문제 때문에 아래 해석은 현재 바로 하면 안 된다.

- `cluster=1`이 유독 어렵다
- 군집 1은 단일 스테이션 군집이다
- 예전 `cluster01`과 현재 숫자형 `cluster=1`을 직접 비교한다

왜냐하면 test 2025에서 `cluster` 숫자 자체가 바뀐 상태라,
군집별 오차 분해가 안정적인 기준 위에 서 있지 않기 때문이다.

## 6. 보정 조치

실제 조치는 아래처럼 적용했다.

1. `train 2023-2024` 기준 `station_id -> cluster` 매핑표 생성
2. `rep15`, `full161` 모두 train/test에 동일 매핑 재부착
3. 그 상태로 `canonical_data` 재생성
4. 이어서 `modeling_data`, `training_runs` 재생성

## 7. 현재 상태

현재 보정 후 확인 결과는 아래다.

- `rep15 canonical train/test`의 `station_id -> cluster`는 일치한다.
- `full161 canonical train/test`의 `station_id -> cluster`도 일치한다.
- 따라서 이후 군집 포함 모델, 군집별 오차표, `station_group` 대조는 이 보정된 정본 기준으로 봐야 한다.

## 8. 다음 단계

지금부터 필요한 작업은 아래다.

1. 보정된 기준선 성능을 기준 문서에 반영
2. 샘플링 1안과 가중치 2안을 보정 후 데이터로 재실행
3. 그 뒤 `cluster` 포함/제외 비교와 군집별 오차 해석 진행
