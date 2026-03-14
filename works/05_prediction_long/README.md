# DDRI Representative-Station Prediction

이 폴더는 대표 스테이션 `15개` 기준 `station-hour` 예측 실험의 정본 작업 경로다.

## 1. 먼저 볼 정본

1. [03_ddri_station_hour_model_comparison.ipynb](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/03_ddri_station_hour_model_comparison.ipynb)
2. [05_ddri_team_cluster_modeling_protocol.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/05_ddri_team_cluster_modeling_protocol.md)
3. [cheng80/07_ddri_cluster_final_recommendation.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/cheng80/07_ddri_cluster_final_recommendation.md)
4. [cheng80/rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/cheng80/rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md)

## 2. 입력 정본

- 학습/테스트 CSV 정본:
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/대표대여소_예측데이터_15개`
- 저장소 안 경로는 노트북, 문서, 산출물만 유지한다

즉 이 폴더의 원본 입력은 저장소 밖 공유폴더가 기준이다.

## 3. 폴더 역할

### 루트

- [03_ddri_station_hour_model_comparison.ipynb](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/03_ddri_station_hour_model_comparison.ipynb)
  - 대표 15개 baseline 모델 비교 정본
- [04_ddri_station_hour_evidence_charts.ipynb](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/04_ddri_station_hour_evidence_charts.ipynb)
  - 비교 차트 재생성
- [05_ddri_team_cluster_modeling_protocol.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/05_ddri_team_cluster_modeling_protocol.md)
  - 팀 공용 군집 실험 규약
- [06_ddri_cluster_modeling_template.ipynb](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/06_ddri_cluster_modeling_template.ipynb)
  - 군집별 실행 템플릿

### `output/`

- 모델 성능표, 비교표, 이미지 산출물 보관 경로
- 현재 대표 성능표:
  - [ddri_station_hour_model_metrics.csv](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/output/data/ddri_station_hour_model_metrics.csv)

### `cheng80/`

- 개인 대리 실험과 후속 오류 분석 정리 경로
- summary 정본은 아래 두 문서로 수렴했다
  - [07_ddri_cluster_final_recommendation.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/cheng80/07_ddri_cluster_final_recommendation.md)
  - [12_ddri_rep15_top5_feature_linkage_summary.md](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long/cheng80/rep15_error_analysis/12_ddri_rep15_top5_feature_linkage_summary.md)
- 단계별 중간 요약 문서는 `cheng80/archive_docs/`, `cheng80/rep15_error_analysis/archive_docs/`에 보관한다

## 4. 현재 읽기 원칙

- 대표 15개 baseline 비교는 루트 `03` 기준으로 읽는다
- 군집별 실험 결론은 `cheng80/07` 기준으로 읽는다
- 오류 해석과 subset 우선순위는 `rep15_error_analysis/12` 기준으로 읽는다
- 중간 summary 문서는 archive 기준으로 본다
