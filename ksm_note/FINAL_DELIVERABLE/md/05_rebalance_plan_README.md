# Rebalance Plan (외곽 Top3)

## 목적
- 많은 대여소에서 자전거를 빼서 부족 대여소로 옮기는 시간대별 이동권고 생성
- 입력은 `ksm_note/final`의 대여소별 2025 예측 결과 사용

## 사용 가정
- 안전버퍼: `1`대
- 필요대수(예측 기준) = `predicted_rounded + 안전버퍼`
- 기준재고(baseline_stock)는 대여소별 연간 평균 필요대수(반올림)
- 시간대별로 기준재고 대비 부족/여유를 계산해 여유->부족으로 greedy 이동
- 주의: 실제 실시간 재고/차량 제약/거리비용 최적화는 아직 미반영

## 0,1,2,3,4 의미
- `0` = 해당 시간대 대여건수 0건
- `1` = 1건
- `2` = 2건
- `3` = 3건
- `4` = 4건
- 즉 숫자 자체가 시간당 대여건수 클래스

## 기준재고(baseline_stock)
|   station_id | station_name                         |   baseline_stock |
|-------------:|:-------------------------------------|-----------------:|
|         2359 | 국립국악중,고교 정문 맞은편          |                2 |
|         2392 | 구룡산 입구 (구룡산 서울둘레길 입구) |                1 |
|         3643 | 더시그넘하우스 앞                    |                2 |

## 대여소별 요약
|   station_id | station_name                         |   hours |   predicted_shortage_hours |   actual_shortage_hours |   total_pred_gap |   total_actual_gap |   total_received |   total_sent |   predicted_shortage_ratio |   actual_shortage_ratio |
|-------------:|:-------------------------------------|--------:|---------------------------:|------------------------:|-----------------:|-------------------:|-----------------:|-------------:|---------------------------:|------------------------:|
|         2359 | 국립국악중,고교 정문 맞은편          |    8760 |                       1093 |                    1697 |            -2205 |              -2082 |               27 |           29 |                  0.124772  |               0.193721  |
|         2392 | 구룡산 입구 (구룡산 서울둘레길 입구) |    8760 |                        131 |                     557 |              131 |                606 |                7 |            0 |                  0.0149543 |               0.0635845 |
|         3643 | 더시그넘하우스 앞                    |    8760 |                        632 |                    1168 |            -3830 |              -3993 |               23 |           28 |                  0.0721461 |               0.133333  |

## 전체 요약
|   hours_total |   total_transfer_records |   total_moved_bikes |   predicted_shortage_hours_any_station |   actual_shortage_hours_any_station |
|--------------:|-------------------------:|--------------------:|---------------------------------------:|------------------------------------:|
|          8760 |                       57 |                  57 |                                   1280 |                                2690 |

## 산출물
- `rebalance_baseline_stock.csv`
- `rebalance_transfer_orders.csv`
- `rebalance_hourly_status.csv`
- `rebalance_station_summary.csv`
- `rebalance_overall_summary.csv`

## 컬럼 설명
- `move_bikes`: 해당 시간대 이동 권고 대수
- `final_gap_pred`: 이동 후 예측 기준 부족(+)/여유(-) 대수
- `final_gap_actual`: 이동 후 실제 기준 부족(+)/여유(-) 대수 (백테스트 참고)