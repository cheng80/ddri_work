# Stitch 프로젝트 내보내기

**프로젝트**: DDRI 따릉이 스타일 대여소 조회  
**Stitch URL**: https://stitch.withgoogle.com/projects/17527760865324934283

## DDRI 방향 (필수)

- **참고**: 따릉이 스타일 참고. 따릉이 사이트 그대로 아님.
- **범위**: 이용권 구매, 로그인, 회원가입, 고객센터 없음. 대여소 조회만.
- **지도**: 단일 지도 1개. 카드마다 개별 지도 썸네일 없음.

---

## 다운로드된 파일

| 파일 | 설명 |
|------|------|
| `DDRI_대여소_조회_데스크탑_screenshot.png` | DDRI 전용 화면 스크린샷 (2560×2096) |
| `DDRI_대여소_조회_데스크탑.html` | DDRI 전용 Tailwind HTML |

## 화면 정보

- **화면명**: DDRI 대여소 조회 전용 웹 (데스크탑)
- **Screen ID**: `3d8c201d09ec41b4b4dc30aab65cf855`

## 레이아웃

- **좌측 45%**: 단일 지도 + 원형 반경 + 마커, 반경 선택 [300m] [500m] [1km]
- **우측 55%**: 대여소 카드 리스트 (지도 썸네일 없음)
- **카드**: 대여소명, 거리, 자전거 수, 대여가능/보통/부족 배지

## Flutter 웹 적용 시 참고

- `flutter_screenutil`로 반응형 적용
- 지도 UX 상세: [10_ddri_user_page_map_ux_spec.md](../10_ddri_user_page_map_ux_spec.md)
