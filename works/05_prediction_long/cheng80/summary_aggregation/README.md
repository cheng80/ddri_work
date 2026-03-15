# summary_aggregation(요약 집계)

목적: `cheng80` 군집별 대리 실험의 루트 집계 산출물을 재생성하는 작업 폴더다.

## 용어 정리

- `summary`(요약 정본)
  - 여러 실험 결과를 짧게 정리한 대표 요약
- `aggregation`(집계)
  - 여러 파일과 결과를 모아 하나의 표로 만드는 작업
- `comparison`(비교)
  - 이전 실험과 다음 실험 결과를 나란히 보는 작업
- `progression`(진행 경과)
  - 1차, 2차, 3차처럼 단계별 변화 흐름

## 노트북

- `11_ddri_cluster_result_collection.ipynb`
  - 5개 군집 1차 실험 결과를 취합해 `ddri_cluster_model_metrics_collection_template.csv`를 생성
- `12_ddri_cluster_second_round_comparison.ipynb`
  - 1차와 2차 결과를 비교해 `ddri_cluster_second_round_comparison_summary.csv`를 생성
- `13_ddri_cluster01_third_round_progression.ipynb`
  - `cluster01`의 1차/2차/3차 진행표를 만들어 `cluster01_third_round_progression_summary.csv`를 생성

## 출력 경로

- `output/data/ddri_cluster_model_metrics_collection_template.csv`
- `output/data/ddri_cluster_second_round_comparison_summary.csv`
- `output/data/cluster01_third_round_progression_summary.csv`
