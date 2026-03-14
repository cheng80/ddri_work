# Ddri 작업물 구조 가이드

작성일: 2026-03-12  
최종 갱신일: 2026-03-14  
목적: 현재 기준 `works/`의 실제 읽기 경로와 저장 원칙만 짧게 안내한다.

## 1. 이 문서의 역할

이 문서는 상세 인벤토리 문서가 아니다.

- 현재 어떤 폴더를 정본으로 읽어야 하는지
- 중간 산출물과 보관 영역을 어떻게 구분하는지
- 새 파일을 어디에 두어야 하는지

위 세 가지만 빠르게 확인하는 안내문으로 사용한다.

상세 원천 데이터 목록과 과거 인벤토리는 `06_ddareungi_project_inventory_2026-03-11.md`를 본다.

## 2. 현재 읽기 기준 구조

### `works/00_overview`

- 프로젝트 기준 문서
- 우선 열람 문서:
  - `01_ddri_master_plan.md`
  - `03_ddri_prediction_target_definition.md`
  - `04_ddri_prediction_dataset_design.md`
  - `07_ddri_notebook_and_evidence_chart_policy.md`
  - `10_ddri_model_score_summary.md`

### `works/01_clustering`

- 군집화 정본:
  - `08_integrated/final/`
- 군집화 재생성/작업 경로:
  - `08_integrated/pipeline/`
- 군집화 중간 산출물:
  - `08_integrated/intermediate/`
- 구버전 보관:
  - `archive_1st/`

### `works/archive_data_collection`

- 외부 데이터 수집 노트북, 스크립트, 결과의 archive 경로
- 현재 학습에 쓰는 값은 이미 생성된 CSV와 학습 데이터셋 쪽에 반영되어 있다

### `works/03_prediction`

- `station-day` 예측 데이터셋과 baseline 준비 경로

### `works/04_presentation`

- 현재는 군집화 발표 자료만 유지

### `works/05_prediction_long`

- 대표 대여소 15개 `station-hour` 실험 정본 경로
- 원본 데이터는 공유폴더에 두고, 저장소 안에는 노트북/문서/산출물만 유지

### `works/06_prediction_long_full`

- 전체 161개 스테이션 `station-hour` 실험 정본 경로
- 저장소 안에는 `output/` 중심 산출물만 유지

## 3. 저장 원칙

### 문서

- 기준 문서는 `works/00_overview/`
- 파트 전용 문서는 해당 파트 루트 또는 목적별 하위 폴더

### 노트북

- 설명 가능한 정본 노트북만 전면 경로에 둔다
- 재생성/집계/중간 실험 노트북은 보관 폴더 또는 하위 목적 폴더로 분리한다

### CSV

- 최종 요약표와 서비스 연결 lookup만 정본 경로에 둔다
- 중간 집계 CSV는 재생성 가능하면 보관 경로로 이동한다

### 이미지

- 문서나 발표에서 직접 쓰는 대표 차트만 유지한다
- 같은 메시지를 반복하는 차트 묶음은 재생성 경로를 우선한다

## 4. 현재 권장 열람 순서

1. `works/00_overview`
2. `works/01_clustering/08_integrated/final`
3. `works/05_prediction_long`
4. `works/06_prediction_long_full`
5. `cheng80/`

## 5. 현재 정리 원칙

- `overview`는 정본 문서 위주로 압축한다
- `cleanup/`은 구조 정리 기간 동안만 쓰는 점검 문서 폴더로 유지한다
- `archive` 성격 자료는 정본 읽기 경로에서 뒤로 뺀다
- 새 파일을 만들 때는 `정본인지`, `재생성용인지`, `보관용인지`를 먼저 구분한다
