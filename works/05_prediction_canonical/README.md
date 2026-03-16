# DDRI Prediction Canonical

이 폴더는 `canonical_data` 정본을 정의하고 재생성하는 전용 경로다.

범위:

- `bike_change` 기준 정본 설계
- 시간패턴 제거 및 시계열 파생 컬럼 정의
- 대표 15개, 전체 161개 `canonical_data` 재생성

이 폴더에 없는 것:

- 모델링용 피처셋 생성
- 학습
- 검증
- 테스트

위 작업은 별도 경로인 [works/06_prediction_training](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training)에서 진행한다.

## 현재 폴더 구조

- [01_notebook](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/01_notebook)
- [02_input_data](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/02_input_data)
- [03_output_data](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/03_output_data)
- [04_reference_docs](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/04_reference_docs)
- [05_scripts](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/05_scripts)

## 핵심 문서와 스크립트

- 점검 노트북:
  - [01_ddri_prediction_canonical_build_review.ipynb](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/01_notebook/01_ddri_prediction_canonical_build_review.ipynb)
- 설계 문서:
  - [01_ddri_prediction_canonical_design.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/04_reference_docs/01_ddri_prediction_canonical_design.md)
- 재생성 스크립트:
  - [02_ddri_prediction_canonical_builder.py](/Users/cheng80/Desktop/ddri_work/works/05_prediction_canonical/05_scripts/02_ddri_prediction_canonical_builder.py)

## 현재 상태 메모

- 대표 실행은 노트북에서 단계별로 확인하는 방식으로 맞춘다.
- 모든 실행 노트북은 `임포트 전용 셀`을 별도로 둔다.
- 파이썬 스크립트는 일괄 재생성 보조 용도로만 둔다.
- 기존 `raw_data`, `full_data` 합본 스냅샷 일부는 삭제되어 있어, 현재 노트북은 먼저 `정본 생성 과정 점검`과 `핵심 변환 검증`을 중심으로 구성한다.

## 실제 정본 출력 경로

- [rep15 canonical_data](/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개/canonical_data)
- [full161 canonical_data](/Users/cheng80/Desktop/ddri_work/3조 공유폴더/군집별 데이터_전체 스테이션/canonical_data)
