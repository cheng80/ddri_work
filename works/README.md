# works

`works/`는 프로젝트 실작업 폴더다.  
현재는 `정본 경로`와 `보관/중간 산출물 경로`를 구분해서 읽는 것이 중요하다.

## 1. 먼저 볼 경로

1. [00_overview](/Users/cheng80/Desktop/ddri_work/works/00_overview)
2. [01_clustering/08_integrated/final](/Users/cheng80/Desktop/ddri_work/works/01_clustering/08_integrated/final)
3. [05_prediction_long](/Users/cheng80/Desktop/ddri_work/works/05_prediction_long)
4. [06_prediction_long_full](/Users/cheng80/Desktop/ddri_work/works/06_prediction_long_full)
5. [04_presentation/01_clustering](/Users/cheng80/Desktop/ddri_work/works/04_presentation/01_clustering)

## 2. 폴더 역할

### `00_overview`

- 프로젝트 기준 문서
- 현재는 과밀 해소 중이며, 핵심 정본 위주로 압축 중

### `01_clustering`

- 최신 정본:
  - `08_integrated/final/`
- 재생성/작업 경로:
  - `08_integrated/pipeline/`
- 중간 산출물:
  - `08_integrated/intermediate/`
- 구버전 보관:
  - `archive_1st/`

### `archive_data_collection`

- 학습용 원본 CSV 생성에 이미 반영된 외부 데이터 수집 보관 경로
- 기존 `02_data_collection`을 메인 읽기 경로에서 archive로 이동한 상태

### `03_prediction`

- `station-day` baseline 정본과 보조 경로
- 핵심은 `02_data/`와 `04_scripts/`
- 설명/재생성용 산출물은 `support_data/`, `support_images/`, `support_scripts/`로 분리

### `04_presentation`

- 현재는 군집화 발표 정본 위주로 유지
- PDF, 지도 이미지, 재생성 스크립트는 `support_assets/`, `support_scripts/`로 분리

### `05_prediction_long`

- 대표 대여소 `15개` 기준 `station-hour` 실험 정본 경로
- `cheng80/` 하위에는 개인 대리 실험 및 오류 분석 정리본이 있음

### `06_prediction_long_full`

- 전체 `161개` 스테이션 `station-hour` 실험 정본 경로
- 원본 데이터는 외부 공유폴더, 저장소 안은 `output/` 중심 관리

## 3. 현재 읽기 원칙

- 최신 군집화 결과는 `01_clustering/08_integrated/final` 기준으로 읽는다
- `03_prediction`은 최종 주력 실험이 아니라 `station-day` baseline 참조 경로로 읽는다
- 대표 대여소 핵심 결론은 `05_prediction_long` 기준으로 읽는다
- 전체 스테이션 baseline은 `06_prediction_long_full` 기준으로 읽는다
- `archive_1st/`, `archive_data_collection/`, `intermediate/`는 보관/중간 경로로 보고, `support_*`는 활성 보조 경로로 본다

## 4. 참고

- 구조 정리 기간 동안의 점검 문서는 루트 [cleanup](/Users/cheng80/Desktop/ddri_work/cleanup) 폴더에서 별도로 관리한다
