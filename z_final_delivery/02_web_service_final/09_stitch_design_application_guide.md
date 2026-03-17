# Stitch MCP 디자인 적용 가이드

작성일: 2026-03-17  
목적: Stitch MCP로 생성된 디자인을 DDRI 웹(Flutter)에 적용하는 방법을 정리한다.

---

## 1. Stitch MCP에서 디자인 가져오기

### 1.1 사용 가능한 MCP 도구

| 도구 | 용도 |
|------|------|
| `list_projects` | 프로젝트 목록 조회 |
| `list_screens` | 프로젝트 내 화면 목록 조회 |
| `get_screen` | 특정 화면의 스크린샷·HTML 코드 URL 조회 |

### 1.2 화면 다운로드 절차

1. **화면 정보 조회**
   ```
   get_screen(
     name: "projects/{projectId}/screens/{screenId}",
     projectId: "17527760865324934283",
     screenId: "95619023c1d14e4e853fe5fd251f2f37"
   )
   ```

2. **응답에서 URL 추출**
   - `screenshot.downloadUrl` → 스크린샷 이미지
   - `htmlCode.downloadUrl` → Tailwind 기반 HTML 코드

3. **로컬 저장**
   ```bash
   curl -L -o screenshot.png "[screenshot.downloadUrl]"
   curl -L -o screen.html "[htmlCode.downloadUrl]"
   ```

4. **저장 위치**: `z_final_delivery/02_web_service_final/stitch_export/`

### DDRI 전용 디자인 (현재)

- **화면**: DDRI 대여소 조회 전용 웹 (데스크탑)
- **Screen ID**: `3d8c201d09ec41b4b4dc30aab65cf855`
- **파일**: `DDRI_대여소_조회_데스크탑_screenshot.png`, `DDRI_대여소_조회_데스크탑.html`
- **방향**: 이용권·로그인 없음, 단일 지도 + 카드 리스트 (카드당 지도 없음)
- **지도 UX**: [10_ddri_user_page_map_ux_spec.md](10_ddri_user_page_map_ux_spec.md)

---

## 2. 디자인 적용 방법 (Flutter 웹 기준)

Stitch는 **Flutter 직접 내보내기를 지원하지 않음**. 아래 3가지 방식 중 선택.

### 2.1 방법 A: 디자인 시스템 추출 → Flutter Theme 적용

**적합**: 색상·타이포·간격 등 시각적 일관성 유지

1. **HTML에서 design tokens 추출**
   - Stitch HTML의 `<script id="tailwind-config">` 또는 `<style>`에서:
     - `primary`: #00a857
     - `background-light`: #f5f8f7
     - `fontFamily`: Public Sans
     - `borderRadius`: 0.25rem, 0.5rem, 0.75rem

2. **Flutter ThemeData로 매핑**
   ```dart
   ThemeData(
     colorScheme: ColorScheme.fromSeed(seedColor: Color(0xFF00a857)),
     fontFamily: 'Public Sans',
     // ...
   )
   ```

3. **flutter_screenutil** designSize: Stitch 모바일 기준(375×812) 설정

### 2.2 방법 B: HTML 구조 참고 → Flutter 위젯 수동 변환

**적합**: 레이아웃·컴포넌트 구조를 그대로 반영하고 싶을 때

| HTML (Tailwind) | Flutter 위젯 |
|-----------------|--------------|
| `flex flex-col` | `Column` |
| `flex flex-row` / `flex gap-3` | `Row` + `SizedBox` |
| `rounded-xl` | `BorderRadius.circular(12)` |
| `bg-primary/5` | `Color(0xFF00a857).withOpacity(0.05)` |
| `material-symbols-outlined` | `Icon(Icons.xxx)` 또는 `MaterialIcons` |
| `p-4` | `Padding(padding: EdgeInsets.all(16))` |

**절차**:
1. 스크린샷으로 시각 확인
2. HTML DOM 구조를 위에서 아래로 읽으며 위젯 트리 설계
3. 섹션별로 `StatelessWidget` 분리 (Header, SearchActions, StationList 등)

### 2.3 방법 C: HTML을 WebView로 임베드 (비권장)

- Flutter Web에서는 `HtmlElementView` 또는 `iframe`으로 HTML 삽입 가능
- **단점**: Flutter 네이티브 위젯과 혼재, 반응형·접근성 제어 어려움
- **용도**: 프로토타입·데모용으로만 제한적 사용

---

## 3. DDRI 프로젝트 적용 체크리스트

- [ ] `stitch_export/` 폴더에 스크린샷·HTML 보관
- [ ] `09_stitch_design_application_guide.md` (본 문서) 참고
- [ ] Primary 색상 `#00a857` → `ddri_web` ThemeData 반영
- [ ] 이용권·사용자 메뉴 등 범위 밖 UI는 HTML에서 제외 후 적용
- [ ] `flutter_screenutil` designSize: `Size(375, 812)` (Stitch 모바일 기준)
- [ ] 반응형: 모바일/태블릿/데스크탑 breakpoint 적용

---

## 4. 참고: React 프로젝트인 경우

React + Vite 프로젝트라면 `react-components` 스킬 사용 가능:

- Stitch HTML → React 컴포넌트로 변환
- `tailwind.config` → `resources/style-guide.json` 동기화
- `.stitch/designs/` 폴더에 HTML·PNG 저장 후 컴포넌트 생성

DDRI는 Flutter Web이므로 위 스킬은 해당 없음.

---

## 5. 관련 문서

- [03_ddri_web_service_screen_spec.md](03_ddri_web_service_screen_spec.md) – 화면 설계
- [08_ddri_user_page_spec_detail.md](08_ddri_user_page_spec_detail.md) – 사용자 페이지 상세
- [stitch_export/README.md](stitch_export/README.md) – 다운로드된 Stitch 산출물
