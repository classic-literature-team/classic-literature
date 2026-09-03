# AGENTS.md

한국고전소설DB 프로젝트의 기준 가이드. 정적 HTML/CSS 시안을 React + TypeScript + Vite 스택으로
이식할 때 지켜야 할 핵심 규칙만 정리한다. (base를 잡고 점진적으로 보완하는 문서)

## 0. 스코프 / 방침

- 로그인/인증 기능은 다루지 않는다. 헤더의 "로그인" 링크도 넣지 않는다.
- 시안 CSS의 디자인 토큰과 레이아웃 구조를 "정답"으로 삼는다.
- 콘텐츠(작품명, 양소유 상담 답변 등)는 한국어 원문을 그대로 보존한다.

## 1. 디자인 토큰

시안은 "Ghibli Meadow" 톤의 하늘색 팔레트를 쓴다. Tailwind 테마/CSS 변수로 옮긴다.

### 색상 (CSS 변수 기준)
- 주색(하늘색): green-50 `#f0f7ff` -> green-600 `#1e6fa0` (변수명은 green이지만 실제 톤은 파랑)
  - green-300 `#7dbfe8`, green-400 `#4ba3d8`(주요 액션), green-500 `#2d8bc4`
- 보조: sky `#e8f4fd`, peach `#f2a87a` / peach-pale `#fef2ea`, earth `#7a8fa0`
- 배경: 상단 `#e8f3fc` -> 하단 `#f5faff` 세로 그라디언트 (fixed attachment)
- 텍스트: text `#050e14`, text-sub `#0f2030`, text-muted `#2a4560`
- 보더: border `#cfe0ed`, border-light `#e2eef6`

### 타이포그래피
- 본문(font-body): `Gowun Dodum`
- 제목(font-title): `Gowun Batang` — h2, 카드 h4, 작품 칩, 통계 숫자에 사용
- 양소유 연애상담소 섹션 본문: `Noto Sans KR`
- 기준 폰트 크기 14.5px, line-height 1.8

### 형태
- radius: 기본 18px(--radius), 작은 요소 12px(--radius-sm), 알약형 20~30px
- shadow: 기본 `0 4px 16px rgba(45,139,196,0.06)`, hover `0 8px 28px rgba(45,139,196,0.1)`
- 카드 hover: translateY(-3px) + 상단 4px 그라디언트 바 노출

## 2. 레이아웃 구조 (위 -> 아래)

1. Hero 헤더: 타이틀("한국고전소설DB", DB만 accent 색), 부제, 하단 그라디언트 라인
2. 메인 네비: sticky, 알약형 탭 8개. active 탭은 green-400 배경 + 흰 글씨
3. 듀얼 검색바: "AI 질문"(보라 `#7b5ea7`) / "키워드 검색"(주황 `#d4915a`) 모드 탭 전환
4. 통계 스트립: 4칸 그리드 (노드/관계/클래스·관계유형/이본·작품 수)
5. 본문: 2컬럼 그리드 `1fr / 300px` (좌: 탭 패널, 우: 사이드바 공지)
6. 푸터: "Produced by Lee Gil-Hwan"

- 반응형: <=900px 사이드바 아래로, <=768px 네비 가로 스크롤 + 통계 2칸 + 카드 1열

## 3. 탭(도메인) 8종

| 탭 | 영문 | 내용 |
|----|------|------|
| DB소개 | Overview | 개요/구조/목적/활용 카드 |
| 서지적요소 | Bibliographic | 이본, 작품집, 인물, 작품(기타) |
| 참여적요소 | Participatory | 비점, 외평, 연관 작품 |
| 배열적요소 | Content | 장면/등장인물/신분/목차/배경/논평/평비 등 |
| 표현적요소 | Expressive | 전고, 소작품 |
| 지식그래프 | Knowledge Graph | 시대별 작품 칩(나말여초~조선전기 / 조선중기 이후) |
| 장르별 목록 | Genre List | 13개 장르 아코디언 |
| 양소유의 연애상담소 | Love Counseling | Q&A 카드 + 관련 장면 토글 (분홍 탭) |

탭 전환은 클라이언트 상태(현재 `data-tab`/`.visible` 토글)로, React에서는 라우트 또는 상태로 관리.

## 4. 카드 색상 그룹 (배열/표현 요소 구분용 left-border)

- brown `#a07040` / bg `#fdf5ec` — 서지적요소
- teal(실제 자홍) `#c94070` / bg `#fef0f4` — 장면
- blue `#4a90c8` / bg `#f0f7ff` — 인물/신분/요소
- green `#4aae5a` / bg `#f0faf2` — 목차
- purple `#8a60c0` — 외평/논평/평비
- yellow(실제 민트) `#40a0a0` / bg `#eef9f9` — 배경
- indigo `#4858a0` — 전고
- coral `#d06060` — 소작품
- other(분홍) `#e880a0` / bg `#fef0f4` — 기타 요소
- clickable 카드: hover 시 우상단 "데이터 보기 ->" 노출

## 5. React 이식 매핑 (가이드)

- 시안의 `styles.css` -> `src/styles/globals.css`의 Tailwind 테마 변수로 흡수
- 탭 패널/네비 -> `layouts/` + `pages/` 또는 라우트 분리
- 카드/칩/아코디언/검색바 -> `components/`의 재사용 컴포넌트
- 데이터(작품 목록, 상담 Q&A, 공지) -> `hooks/` + `utils/api.ts`로 서버 연동 (현재는 정적)
- 아이콘/장식 -> `assets/`
- shadcn `cn()`은 `@/lib/utils` 유지 (규약)

## 6. 접근성 / 품질 기준

- 탭/토글은 키보드 접근 가능해야 함(버튼 시맨틱, aria-selected 등)
- 한자 병기는 `<span>` 보조 텍스트로, 스크린리더 흐름 확인
- 커밋 전 `npm run lint` / `npm run build` 통과
