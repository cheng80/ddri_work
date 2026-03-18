# HMW Ridge End-to-End Report Reneew

이 폴더는 `HMW_ridge_end_to_end_report_20260318`를 새 스타일 기준으로 다시 작성하기 위한 작업용 폴더다.

## 구조

- `build_ridge_end_to_end_report.py`
  - 기존 보고서 빌드 스크립트를 복사한 작업본
- `data/`
  - 공유폴더 대용량 CSV를 심볼릭 링크로 연결한 입력 폴더
- `outputs/`
  - 새 보고서와 새 그림 산출물 저장 위치
- `references/`
  - 새 스타일 원본, 메모, 중간 정리 문서를 둘 위치

## 현재 연결된 입력 데이터

- `data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3_with_sample_weight.csv`
- `data/ddri_prediction_canonical_test_2025_multicollinearity_removed_v3.csv`
- `data/ddri_prediction_canonical_train_2023_2024_multicollinearity_removed_v3.csv`

실제 원본은 아래 공유폴더에 있고, 여기서는 심볼릭 링크로 연결해 사용한다.

- `/Users/cheng80/Desktop/ddri_work/3조 공유폴더/ksm_note_large_files_20260318/data/`

## 현재 빌드 스크립트 상태

- `DATA_DIR`는 이 폴더 내부 `data/`를 보도록 수정됨
- 나머지 보조 산출물 경로는 기존 `ksm_note` 하위 폴더 출력물을 참조함

즉 현재 상태만으로도 아래 산출물을 재사용한다.

- `HMW_linear_regression_coefficients_20260318/outputs/*`
- `feature_weight/outputs/*`
- `HMW_cluster_ridge_regression_20260318/outputs/*`
- `lightgbm_reason/outputs/*`
- `lightgbm_reason_1/outputs/*`
- `feature_hitmap/outputs/*`

## 주의

- 공선성 노트북은 원래 `v2`를 기대하지만 현재 확보된 데이터는 `v3` 계열뿐이다.
- 따라서 새 보고서에서 공선성 파트를 엄밀하게 다시 만들려면 `feature_hitmap` 분석을 `v3` 기준으로 재생성하는 쪽이 맞다.
- 깨진 예전 스타일 Markdown은 무시하고, 새 스타일 원본은 이후 `references/`에 추가하는 전제로 준비 중이다.
