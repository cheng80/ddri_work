# DDRI Clustering Basis Summary

이 문서는 `15개 대표 스테이션`과 `161개 전체 스테이션` 실험에 공통으로 들어간 `cluster` 컬럼의 출처를 설명하는 군집 근거 요약본이다.

## 왜 이 문서가 필요한가

- `05_prediction_long`의 대표 15개 실험은 군집별 대표 스테이션 선정 결과를 기반으로 시작했다
- `06_prediction_long_full`의 161개 실험도 같은 군집 기준을 `cluster` 컬럼으로 이어받았다
- 따라서 최종 패키지에서 `cluster`의 생성 근거가 빠지면, 이후 모델링 단계의 출발점이 비게 된다

## 군집화 목적

1차 군집화는 수요 규모 중심 분리에는 유효했지만, `업무지구`, `주거지구`, `상권`, `복합 거점` 같은 공간적 성격을 설명하는 데 한계가 있었다.

그래서 최종 통합 군집화는 아래 두 축을 결합했다.

- 반납 시간대 기반 도착 수요 패턴
- 교통 접근성과 순유입 기반 공간 역할

즉 단순한 이용량이 아니라 `어떤 성격의 목적지인가`를 군집으로 다시 해석했다.

## 군집화 핵심 입력 피처

핵심 입력 7개:

- `arrival_7_10_ratio`: 07~10시 반납 비율
- `arrival_11_14_ratio`: 11~14시 반납 비율
- `arrival_17_20_ratio`: 17~20시 반납 비율
- `morning_net_inflow`: 아침 순유입
- `evening_net_inflow`: 저녁 순유입
- `subway_distance_m`: 최근접 지하철 거리
- `bus_stop_count_300m`: 300m 내 버스정류장 수

쉬운 해석:

- 반납 시간대 3개는 `언제 사람이 이 대여소로 모이는가`를 본다
- 순유입 2개는 `언제 자전거가 실제로 들어오고 빠져나가는가`를 본다
- 교통 접근성 2개는 `중심 교통축에 가까운가`를 본다

## 군집 수 선택

탐색 범위는 `k = 5 ~ 7`이었다.

- `k = 5`: silhouette `0.2033`
- `k = 6`: silhouette `0.1795`
- `k = 7`: silhouette `0.1708`

최종 선택은 `k = 5`다.

이유:

- silhouette가 가장 높았다
- 이번 군집화는 분리도 자체보다 `지구판단 해석력` 확보를 우선했다

## 최종 군집 의미

- `cluster 0`: 업무/상업 혼합형
- `cluster 1`: 아침 도착 업무 집중형
- `cluster 2`: 주거 도착형
- `cluster 3`: 생활·상권 혼합형
- `cluster 4`: 외곽 주거형

이 라벨은 이후 `cluster01`, `cluster02` 등 군집별 예측 실험 해석의 직접 근거가 된다.

## 15개 대표 스테이션과의 연결

대표 15개는 각 군집에서 대표성을 가지는 스테이션을 추린 결과다.

- 군집별 특성 해석
- 군집별 피처 탐색
- 군집별 대표 오류 분석

이 세 작업이 모두 이 군집화 결과를 기반으로 진행됐다.

즉 `15개`는 군집화의 후속 해석 경로다.

## 161개 전체 스테이션과의 연결

`161개` 전체 스테이션 데이터에도 같은 군집 결과가 `cluster` 컬럼으로 연결됐다.

이 연결 덕분에 다음이 가능해졌다.

- 라우팅 실험
- 군집별 피처 gating 실험
- 상위 오류 스테이션의 군집 집중도 확인

비록 최종 운영안은 단일 모델이 채택됐지만, `cluster` 컬럼은 여전히 해석과 비교 실험의 핵심 축으로 남았다.

## 최종 판단

- `cluster` 컬럼은 최종 모델보다 먼저 만들어진 상위 구조다
- `15개`는 군집 해석과 피처 발굴의 경로다
- `161개`는 같은 군집 기준을 운영 전체 데이터에 연결한 경로다
- 따라서 이 군집화 근거는 최종 패키지 안에서 별도 참조 문서와 노트북으로 유지해야 한다

## 패키지 내 로컬 자산

- [ddri_integrated_second_clustering_report.md](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/04_reference_docs/ddri_integrated_second_clustering_report.md)
- [ddri_final_district_clustering_feature(입력 변수)s_train_2023_2024.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_final_district_clustering_feature(입력 변수)s_train_2023_2024.csv)
- [ddri_second_cluster_summary.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_second_cluster_summary.csv)
- [ddri_second_cluster_representative_stations.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_second_cluster_representative_stations.csv)
- [ddri_second_cluster_hypothesis_crosstab.csv](/Users/cheng80/Desktop/ddri_work/z_final_delivery/01_analysis_ml_final/02_input_data/ddri_second_cluster_hypothesis_crosstab.csv)
