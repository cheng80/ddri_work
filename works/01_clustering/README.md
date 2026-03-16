# 01 Clustering

이 폴더는 군집화 정본과 재생성 경로를 관리하는 루트다.

현재 전면 정본은 `08_integrated/final` 기준으로 읽고, 과거 1차 군집화는 `archive_1st`로 분리해서 본다.

## 먼저 볼 정본

1. [08_integrated/final/results/second_clustering_results/ddri_integrated_second_clustering_report.md](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/final/results/second_clustering_results/ddri_integrated_second_clustering_report.md)
2. [08_integrated/final/features/ddri_final_district_clustering_features_train_2023_2024.csv](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/final/features/ddri_final_district_clustering_features_train_2023_2024.csv)
3. [08_integrated/README.md](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/README.md)
4. [01_ddri_clustering_presentation_a4_landscape.md](/Users/cheng80/Desktop/ddri_work/works/04_presentation/01_clustering/01_ddri_clustering_presentation_a4_landscape.md)

## 폴더 역할

### `08_integrated/final`

- 현재 군집화 정본 결과
- 최종 피처 CSV, 최종 리포트, 최종 지도 HTML 유지

### `08_integrated/pipeline`

- 정본 재생성 스크립트와 노트북
- 현재 실행이 직접 바라보는 생성 경로

### `08_integrated/intermediate`

- 환경 보강, POI 보강, 반납 시간대 지구 판단 등 중간 산출물
- 비교 실험과 재생성 추적용 경로

### `archive_1st`

- 1차 군집화 결과와 과거 발표 자료 보관 경로
- 현재 핵심 읽기 경로의 정본은 아님

## 현재 읽기 원칙

- 최신 군집화 결과는 `08_integrated/final` 기준으로 읽는다
- 다시 만들 때만 `pipeline`을 연다
- 중간 실험 검토가 필요할 때만 `intermediate`를 연다
- 과거 군집화는 `archive_1st`로 본다
