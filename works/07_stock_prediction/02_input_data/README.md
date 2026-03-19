# Input Data

현재 기준 주요 입력 후보는 아래 두 축이다.

## 1. station_hour_bike_flow

- 원천 경로:
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/station_hour_bike_flow_2023_2025/station_hour_bike_flow_train_2023_2024.csv`
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/station_hour_bike_flow_2023_2025/station_hour_bike_flow_test_2025.csv`
- 핵심 컬럼:
  - `station_id`
  - `time`
  - `rental_count`
  - `return_count`
  - `bike_change`
  - `bike_count_index`
  - `year`, `month`, `day`, `weekday`, `hour`

## 2. 대여소 메타

- 원천 경로:
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/강남구 대여소 정보 (2023~2025)/2023_강남구_대여소.csv`
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/강남구 대여소 정보 (2023~2025)/2024_강남구_대여소.csv`
  - `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/강남구 대여소 정보 (2023~2025)/2025_강남구_대여소.csv`

## 보조 입력

- 날씨는 기존 canonical 경로 또는 별도 기상 원천에서 병합 검토
- 현재 재고는 운영 시점 실시간 API 입력값 사용
