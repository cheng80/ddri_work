# DDRI Prediction Training

이 폴더는 `canonical_data`를 받아 무샘플링 기준 1사이클을 수행하는 작업 경로다.

현재 기준선:

- 샘플링 없음
- 정본 행 삭제 없음
- `2023` 학습
- `2024` 검증
- 검증 기준 우세 모델 선택
- `2023+2024` 재학습
- `2025` 테스트

즉, 이 폴더의 역할은 아래 전체를 한 번에 다루는 것이다.

- 전처리
- 학습
- 검증
- 최종 재학습
- 테스트

## 현재 폴더 구조

- [01_notebook](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook)
- [04_reference_docs](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs)
- [05_scripts](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts)

## 먼저 볼 문서

- 종합 레포트:
  - [09_ddri_training_integrated_report_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/09_ddri_training_integrated_report_round1.md)
- 무샘플링 1사이클:
  - [01_ddri_no_sampling_baseline_cycle.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/01_ddri_no_sampling_baseline_cycle.md)
- 무샘플링 1차 결과:
  - [05_ddri_no_sampling_baseline_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/05_ddri_no_sampling_baseline_results_round1.md)
- 샘플링 1안 1차 결과:
  - [06_ddri_sampling_plan1_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/06_ddri_sampling_plan1_results_round1.md)
- 가중치 2안 1차 결과:
  - [07_ddri_sampling_plan2_weighting_results_round1.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/07_ddri_sampling_plan2_weighting_results_round1.md)
- `cluster` 컬럼 일관성 점검:
  - [08_ddri_cluster_consistency_issue.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/08_ddri_cluster_consistency_issue.md)
- 대표 15개 군집 재매칭:
  - [10_ddri_rep15_station_cluster_rematch.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/10_ddri_rep15_station_cluster_rematch.md)
- 샘플링 검토:
  - [02_ddri_temporal_sampling_policy_review.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/02_ddri_temporal_sampling_policy_review.md)
- 모델링 피처 설계:
  - [03_ddri_prediction_modeling_feature_design.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/03_ddri_prediction_modeling_feature_design.md)
- 학습 정책:
  - [04_ddri_prediction_training_policy.md](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/04_reference_docs/04_ddri_prediction_training_policy.md)

## 대표 실행 파일

- 기준선 노트북:
  - [04_ddri_prediction_train_eval_run_all.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/04_ddri_prediction_train_eval_run_all.ipynb)
- 샘플링 1안 시작 노트북:
  - [05_ddri_sampling_plan1_day_profile_start.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/05_ddri_sampling_plan1_day_profile_start.ipynb)
- 가중치 2안 시작 노트북:
  - [06_ddri_sampling_plan2_weighting_start.ipynb](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/01_notebook/06_ddri_sampling_plan2_weighting_start.ipynb)
- 보조 스크립트:
  - [03_ddri_prediction_modeling_feature_builder.py](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts/03_ddri_prediction_modeling_feature_builder.py)
  - [04_ddri_prediction_train_eval.py](/Users/cheng80/Desktop/ddri_work/works/06_prediction_training/05_scripts/04_ddri_prediction_train_eval.py)

추가 원칙:

- 모든 실행 노트북은 `임포트 전용 셀`을 별도로 둔다.
- 샘플링 노트북은 배치 스크립트 호출용이 아니라 단계별 직접 실행형으로 유지한다.
- 샘플링 1안의 현재 기본 결과는 `retain_ratio=0.7` 기준 약 `71.23%` 유지다.
- 샘플링 노트북에는 반드시 `행 수 비교 셀`과 `샘플링 후 재학습·검증·테스트 셀`을 포함한다.
- 가중치 노트북에는 반드시 `가중치 분포 확인 셀`과 `가중치 적용 후 재학습·검증·테스트 셀`을 포함한다.
