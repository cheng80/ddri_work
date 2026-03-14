# DDRI Final Notebook Input Manifest

작성일: 2026-03-14  
목적: 앱 제작 직전 기준 `핵심 노트북 2~3개`를 다시 실행할 때 필요한 `정본 입력 CSV`와 주요 출력 CSV를 고정한다.

## 1. 왜 이 문서가 필요한가

구조 정리 과정에서는 폴더를 archive로 옮기거나 README를 줄일 수 있다.

하지만 최종 노트북 실행에 필요한 입력이 어디에 고정돼 있는지 먼저 정하지 않으면, 구조 정리 자체가 실행 경로를 흔들 수 있다.

따라서 이 문서는 아래를 고정한다.

- 어떤 노트북이 최종 핵심 노트북 후보인지
- 그 노트북이 실제로 읽는 정본 CSV가 무엇인지
- 입력이 `공유폴더 정본`인지, `저장소 내부 산출물`인지
- 노트북이 생성하는 핵심 출력 CSV가 무엇인지

## 2. 현재 기준 핵심 노트북 후보

1. `works/05_prediction_long/03_ddri_station_hour_model_comparison.ipynb`
2. `works/06_prediction_long_full/02_ddri_station_hour_full_model_comparison.ipynb`
3. `cheng80/01_ddri_api_verification.ipynb`

## 3. 입력 경로 고정 원칙

- 대표 대여소 및 전체 스테이션 예측 원본은 `3조 공유폴더` 안의 정본 CSV를 우선 사용한다
- API 검증 노트북은 공유폴더의 테스트용 예측 CSV와 `cheng80/api_output/` lookup/output을 함께 사용한다
- `works/02_data_collection`은 현재 archive 경로로 이동했으며, 최종 노트북 직접 입력 경로로 보지 않는다

## 3.1 1차 정본 데이터와 실험 경로 대응

현재 구조 정리에서 먼저 고정해야 하는 `1차 정본 데이터`는 아래 두 개다.

1. `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개`
   - 의미:
     - `15개` 대표 스테이션, `5개 군집` 기준 정본 데이터
   - 이 정본으로 실험한 작업 폴더:
     - `/Users/cheng80/Desktop/ddri_work/works/05_prediction_long`

2. `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션`
   - 의미:
     - `161개` 전체 스테이션 기준 정본 데이터
   - 이 정본으로 실험한 작업 폴더:
     - `/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full`

즉 현재는 `공유폴더 정본 2개 -> 실험 작업 폴더 2개` 대응으로 읽는 것이 맞다.

중요 판단:

- `works/archive_data_collection/02_data_collection`은 재수집/보관 경로다
- 최종 노트북 실행 기준의 실질 정본 입력은 이미 아래 공유폴더 경로에 들어 있다고 본다
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/raw_data`
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/full_data`

## 4. 노트북별 입력/출력 manifest

### A. 대표 15개 모델 비교 노트북

노트북:

- `works/05_prediction_long/03_ddri_station_hour_model_comparison.ipynb`

정본 입력 CSV:

- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_train_2023_2024.csv`
- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_test_2025.csv`

주요 출력 CSV:

- `/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/output/data/ddri_station_hour_model_metrics.csv`
- `/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/output/data/ddri_station_hour_lightgbm_feature_importance.csv`

판단:

- 이 노트북은 이미 공유폴더 `raw_data`를 직접 읽으므로, `02_data_collection` archive 이동과 직접 충돌하지 않는다

### B. 전체 161개 모델 비교 노트북

노트북:

- `works/06_prediction_long_full/02_ddri_station_hour_full_model_comparison.ipynb`

정본 입력 CSV:

- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_train_2023_2024.csv`
- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_test_2025.csv`

주요 출력 CSV:

- `/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full/output/data/ddri_station_hour_full_model_comparison_metrics.csv`
- `/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full/output/data/ddri_station_hour_full_model_comparison_lightgbm_feature_importance.csv`

판단:

- 이 노트북도 이미 공유폴더 `full_data`를 직접 읽는다
- 따라서 원천 수집 폴더 archive 전환과 직접 충돌하지 않는다

### C. API 검증 노트북

노트북:

- `cheng80/01_ddri_api_verification.ipynb`

정본 입력 CSV:

- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/raw_data/ddri_prediction_long_test_2025.csv`
- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/full_data/ddri_prediction_long_test_2025.csv`
- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_station_id_api_lookup.csv`

주요 출력 CSV:

- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_rep15_station_api_validation_official.csv`
- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_full161_station_api_validation_official.csv`
- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_unmatched_station_master_crosscheck.csv`
- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_service_realtime_join_preview.csv`
- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_api_summary_revalidation_checklist.csv`
- `/Users/cheng80/Desktop/ddri_work/cheng80/api_output/ddri_api_key_compatibility_check.csv`

판단:

- 이 노트북도 핵심 입력은 공유폴더 test CSV와 `cheng80/api_output/`에 고정돼 있다
- 따라서 최종 서비스 연결 근거를 볼 때는 `02_data_collection`보다 이 노트북과 `api_output` 쪽이 우선이다

## 5. 현재 결론

현재 기준으로는 `최종 노트북 실행 입력`이 이미 아래 두 공유폴더 정본으로 사실상 수렴해 있다.

- 대표 대여소:
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/raw_data`
- 전체 스테이션:
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/full_data`

이 두 정본의 실험 대응 경로는 아래처럼 고정한다.

- 대표 대여소 정본 -> `works/05_prediction_long`
- 전체 스테이션 정본 -> `works/06_prediction_long_full`

따라서 `works/archive_data_collection/02_data_collection`은 `최종 실행 입력`이 아니라 `재수집/보관 경로`로 유지하는 해석이 맞다.

## 6. 다음 단계 후보

다음 구조 정리에서 선택할 수 있는 방향은 아래 두 가지다.

### 옵션 A. 공유폴더 정본 유지

- 현재 공유폴더 경로를 최종 입력 경로로 그대로 인정
- 저장소 안에는 manifest와 출력 산출물만 유지

장점:

- 중복 CSV 복사가 필요 없다
- 현재 노트북 경로와 가장 잘 맞는다

주의:

- 공유폴더 의존성이 계속 남는다

### 옵션 B. 최종 입력 CSV 묶음 별도 고정

- `final_inputs/` 같은 경로를 만들어 최종 노트북에 필요한 CSV만 별도로 복제 또는 링크
- 이후 핵심 노트북은 그 경로만 읽도록 고정

장점:

- 최종 실행 기준이 더 단순해진다
- 구조 정리와 archive 이동 판단이 쉬워진다

주의:

- 어떤 CSV를 복제할지 먼저 엄격히 고정해야 한다
- 공유폴더 정본과의 동기화 기준이 필요하다

## 7. 현재 권장

지금 단계에서는 `옵션 A`가 더 안전하다.

즉 먼저 공유폴더 정본을 `최종 입력 경로`로 공식화하고, 구조 정리가 더 진행된 뒤에만 `final_inputs/` 별도 고정 여부를 다시 판단하는 편이 충돌이 적다.
