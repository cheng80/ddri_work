# DDRI Bike-Change Full161 Base

이 폴더는 `161개 정본 데이터 + 기본 컬럼만 사용 + bike_change 타깃 재생성` 실험의 새 정본 경로다.

기존 `works/07_prediction_bike_change`의 `rep15` 실험과 섞지 않고, 아래 원칙으로 별도 관리한다.

## 고정 원칙

- 정본 입력:
  - `3조 공유폴더/군집별 데이터_전체 스테이션/full_data/`
- 대상:
  - `161개` 공통 스테이션
- 피처:
  - 정본 CSV 기본 컬럼만 사용
- 타깃:
  - `bike_change_raw`
  - `bike_change_deseasonalized`
- 시간 분할:
  - Train `2023`
  - Validation `2024`
  - Test `2025`
- 재학습:
  - Validation 우세 모델 선택
  - `2023+2024` 재학습
  - `2025` 평가

## 현재 문서

1. [01_ddri_bike_change_full161_base_dataset_design.md](/Users/cheng80/Desktop/ddri_work/works/08_prediction_bike_change_full161_base/01_ddri_bike_change_full161_base_dataset_design.md)
2. [02_ddri_bike_change_full161_base_dataset_builder.py](/Users/cheng80/Desktop/ddri_work/works/08_prediction_bike_change_full161_base/02_ddri_bike_change_full161_base_dataset_builder.py)
3. [02_ddri_bike_change_full161_base_dataset_builder_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/08_prediction_bike_change_full161_base/02_ddri_bike_change_full161_base_dataset_builder_run_all.ipynb)
4. [03_ddri_bike_change_full161_base_pattern_evidence.ipynb](/Users/cheng80/Desktop/ddri_work/works/08_prediction_bike_change_full161_base/03_ddri_bike_change_full161_base_pattern_evidence.ipynb)

## 출력 경로

- Git 관리 문서/스크립트:
  - `works/08_prediction_bike_change_full161_base/`
- 대용량 산출물(공유폴더, Git 제외):
  - `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/data/`
  - `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/reports/`
  - `3조 공유폴더/군집별 데이터_전체 스테이션/bike_change_full161_base_outputs/evidence/`
