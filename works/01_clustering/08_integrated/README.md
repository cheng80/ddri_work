# 08 Integrated

`01_clustering`의 현재 최신 통합 군집화 작업 루트다.

## 먼저 볼 정본

- 최종 결과 리포트:
  - [ddri_integrated_second_clustering_report.md](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/final/results/second_clustering_results/ddri_integrated_second_clustering_report.md)
- 최종 입력 피처:
  - [ddri_final_district_clustering_features_train_2023_2024.csv](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/final/features/ddri_final_district_clustering_features_train_2023_2024.csv)
- 재생성 시작점:
  - [12_ddri_integrated_clustering_report_builder.ipynb](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/pipeline/12_ddri_integrated_clustering_report_builder.ipynb)

## 폴더 역할

### `final/`

- 문서와 상위 README에서 직접 참조하는 최신 정본 결과
- `features/`에는 최종 입력 피처 CSV
- `results/second_clustering_results/`에는 최종 리포트와 최종 지도 HTML
- PDF 같은 보조 자산은 `results/second_clustering_results/support_assets/`로 분리

### `pipeline/`

- 통합 군집화 재생성 스크립트, 노트북, 작업 메모
- 실제 생성 흐름은 이 경로 기준으로 다시 돌린다

### `intermediate/`

- 반납 시간대, 환경 보강, POI 보강 등 중간 산출물
- 비교 실험과 세부 추적용 경로

### `source_data/`

- 공통 기준표와 입력 기준 데이터

## 현재 읽기 원칙

- 최종 결과만 볼 때는 `final/`만 연다
- 재생성할 때만 `pipeline/`을 연다
- 비교 실험이나 근거 추적이 필요할 때만 `intermediate/`를 연다
