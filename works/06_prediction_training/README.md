# DDRI Prediction Training

이 폴더는 `full161` 기준 예측 실험을 수행하는 작업 경로다.

현재 기준:

- 입력 정본: [canonical_data_no_multicollinearity](/Users/cheng80/Desktop/ddri_work/3조%20공유폴더/군집별%20데이터_전체%20스테이션/canonical_data_no_multicollinearity)
- 대상 데이터셋: `full161`
- 타깃 기본값: `bike_change_deseasonalized`
- 시간 정책:
  - `2023` 학습
  - `2024` 검증
  - 검증 기준 우세 모델 선택
  - `2023+2024` 재학습
  - `2025` 테스트

현재 이 폴더에는 아래 두 실험만 둔다.

1. 무필터링 기준선 실험
2. 가중치 기반 실험

## 현재 폴더 구조

- [01_notebook](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook)
- [03_output_data](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/03_output_data)
- [04_reference_docs](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs)
- [05_scripts](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts)

## 먼저 볼 문서

- 요약본:
  - [00_ddri_experiment_summary.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/00_ddri_experiment_summary.md)
- 결과 요약본:
  - [04_ddri_experiment_results_summary.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/04_ddri_experiment_results_summary.md)
- 학습 정책:
  - [03_ddri_prediction_training_policy.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/03_ddri_prediction_training_policy.md)
- 무필터링 실험:
  - [01_ddri_no_filtering_experiment.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/01_ddri_no_filtering_experiment.md)
- 가중치 실험:
  - [02_ddri_weighting_experiment.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/02_ddri_weighting_experiment.md)

## 대표 실행 파일

- 무필터링 노트북:
  - [04_ddri_prediction_train_eval_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/04_ddri_prediction_train_eval_run_all.ipynb)
- 가중치 노트북:
  - [06_ddri_sampling_plan2_weighting_start.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/06_ddri_sampling_plan2_weighting_start.ipynb)
- 보조 스크립트:
  - [03_ddri_prediction_modeling_feature_builder.py](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts/03_ddri_prediction_modeling_feature_builder.py)
  - [04_ddri_prediction_train_eval.py](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts/04_ddri_prediction_train_eval.py)

## 실행 원칙

- 모든 실행 노트북은 `임포트 전용 셀`을 별도로 둔다.
- 노트북은 배치 스크립트 호출용이 아니라 단계별 직접 실행형으로 유지한다.
- 무필터링과 가중치 실험 모두 같은 입력 정본과 같은 시간 분할 정책을 쓴다.
- 가중치 실험은 행을 삭제하지 않고 `2023` 학습 구간에만 샘플 가중치를 적용한다.
