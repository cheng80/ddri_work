# Stitch MCP 사용 이후 진행 상황 및 참고 주소

작성일: 2026-03-17  
목적: Stitch MCP 도입 이후 진행 상황과 참고해야 할 주소·경로를 정리한다.

---

## 1. 진행 상황 타임라인

| 시점 | 작업 | 결과 |
|------|------|------|
| 1차 | [서울시 따릉이 앱 사용법](https://news.seoul.go.kr/traffic/archives/505738) 참고, Stitch MCP로 모바일 화면 생성 | `가까운 대여소 조회` (Screen ID: 95619023...) 생성, 502 에러로 다운로드 지연 |
| 2차 | `get_screen`으로 화면 정보 조회, curl로 스크린샷·HTML 다운로드 | `stitch_export/` 폴더에 저장 |
| 3차 | 반응형 구조 적용 (1/2/3열 그리드, max-width 1200px) | `반응형 대여소 조회` (Screen ID: 3d39d561...) 생성 |
| 4차 | 범위 밖 항목 명시 (이용권·사용자 정보) | 03, README, stitch_export README 수정 |
| 5차 | 지도 UX 개선 (단일 지도 + 원형 반경 + 마커) | `10_ddri_user_page_map_ux_spec.md` 작성 |
| 6차 | 사용 안 하는 이미지·HTML 삭제 | `가까운_대여소_조회.*`, `반응형_대여소_조회.*` 삭제 |
| 7차 | DDRI 전용 디자인 재생성 (이용권·로그인 제외, 단일 지도) | `DDRI 대여소 조회 전용 웹` (Screen ID: 3d8c201d...) 생성, 현재 기준 |

---

## 2. 참고 주소 (URL)

### 2.1 Stitch

| 용도 | URL |
|------|-----|
| **Stitch 프로젝트** | https://stitch.withgoogle.com/projects/17527760865324934283 |
| **프로젝트 ID** | `17527760865324934283` |

### 2.2 참고 사이트 (스타일만 참고)

| 용도 | URL |
|------|-----|
| 서울시 따릉이 앱 사용법 | https://news.seoul.go.kr/traffic/archives/505738 |

※ DDRI는 따릉이 사이트 그대로가 아님. 이용권·로그인 없음.

---

## 3. 참고 경로 (로컬)

### 3.1 Stitch 산출물

| 파일 | 경로 |
|------|------|
| 스크린샷 | `z_final_delivery/02_web_service_final/stitch_export/DDRI_대여소_조회_데스크탑_screenshot.png` |
| HTML 코드 | `z_final_delivery/02_web_service_final/stitch_export/DDRI_대여소_조회_데스크탑.html` |

### 3.2 관련 문서

| 문서 | 경로 |
|------|------|
| Stitch 적용 가이드 | `z_final_delivery/02_web_service_final/09_stitch_design_application_guide.md` |
| 지도 UX 설계 | `z_final_delivery/02_web_service_final/10_ddri_user_page_map_ux_spec.md` |
| 화면 설계서 | `z_final_delivery/02_web_service_final/03_ddri_web_service_screen_spec.md` |
| 사용자 페이지 상세 | `z_final_delivery/02_web_service_final/08_ddri_user_page_spec_detail.md` |
| stitch_export README | `z_final_delivery/02_web_service_final/stitch_export/README.md` |

### 3.3 웹 프로젝트

| 항목 | 경로 |
|------|------|
| Flutter 웹 | `/Users/cheng80/Desktop/ddri_web` |

---

## 4. 현재 Stitch 화면 (기준)

| 항목 | 값 |
|------|-----|
| **화면명** | DDRI 대여소 조회 전용 웹 (데스크탑) |
| **Screen ID** | `3d8c201d09ec41b4b4dc30aab65cf855` |
| **해상도** | 2560×2096 |

### MCP get_screen 호출 예시

```
name: "projects/17527760865324934283/screens/3d8c201d09ec41b4b4dc30aab65cf855"
projectId: "17527760865324934283"
screenId: "3d8c201d09ec41b4b4dc30aab65cf855"
```

---

## 5. DDRI 방향 (필수 준수)

- **참고**: 따릉이 스타일 참고. 따릉이 사이트 그대로 아님.
- **범위 밖**: 이용권 구매, 로그인, 회원가입, 고객센터, 프로필
- **지도**: 단일 지도 1개. 카드마다 개별 지도 썸네일 없음.
- **레이아웃**: 좌측 지도(45%) + 우측 카드 리스트(55%)

---

## 6. MCP 도구 요약

| 도구 | 용도 |
|------|------|
| `list_projects` | 프로젝트 목록 |
| `list_screens` | 프로젝트 내 화면 목록 |
| `get_screen` | 화면 스크린샷·HTML URL 조회 |
| `generate_screen_from_text` | 텍스트 프롬프트로 새 화면 생성 |
| `edit_screens` | 기존 화면 수정 |

---

## 7. 다운로드 절차 (추가 화면 있을 때)

1. `get_screen`으로 `screenshot.downloadUrl`, `htmlCode.downloadUrl` 조회
2. `curl -L -o 파일명 "[URL]"` 로 저장
3. `stitch_export/` 폴더에 저장
4. `stitch_export/README.md` 업데이트
