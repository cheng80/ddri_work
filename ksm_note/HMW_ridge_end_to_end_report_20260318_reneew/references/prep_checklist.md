# Reneew Prep Checklist

## 확정된 입력 데이터

- 공유폴더 `ksm_note_large_files_20260318/data/`의 `v3`, `v3_with_sample_weight`, `test_v3`

## 현재 재사용 가능한 보조 산출물

- 선형 회귀 계수/성능
- 월 유사도 및 월 가중치
- 누수 및 split audit
- LightGBM 비교
- cluster별 Ridge 점수
- 기존 feature_hitmap 산출물

## 새 문서 전 남은 결정 사항

- 새 스타일 원본 문서 경로를 `references/`에 둘 것
- 스타일 CSS 기준 선택
  - 기본 발표형: `references/ddri_presentation_a4_landscape.css`
  - 2장 축약형: `references/ddri_presentation_a4_landscape_compact.css`
  - 스타일 운용 원칙 참고: `references/04_presentation_README.md`
- 공선성 파트를 기존 산출물 재사용으로 갈지, `v3` 기준 재생성으로 갈지 결정
- 기존 복구본 문장을 얼마나 재사용할지 결정

## 권장 순서

1. 새 스타일 원본 확보
2. 사용할 CSS가 기본형인지 compact형인지 결정
3. 공선성 파트 `v3` 기준 재생성 여부 결정
4. 빌드 스크립트 문안 구조 조정
5. 산출물 생성
