# Requirements Document

## Introduction

이 스펙은 제공된 정적 HTML 시안(`ai-chat-2`)의 "AI 질문" 화면을 현재 React + TypeScript + Vite 프로젝트의 `ChatPage`(`frontend/src/pages/ChatPage.tsx`)로 이식하는 작업을 정의한다. 화면은 좌측 대화 영역(Chat Area)과 우측 안내 패널(Guide Panel)의 2컬럼 레이아웃이며, 시안의 상단 topbar는 이식 대상에서 제외한다.

핵심 방침:
- 시안의 데모 목업(`demoAnswers`)은 사용하지 않고, 이미 구축·검증된 실제 스트리밍 백엔드(`POST /api/chat/stream`, SSE)에 연결한다. 스트리밍 연동은 기존 훅 `useChatStream()`(`frontend/src/hooks/useChat.ts`)을 그대로 재사용한다.
- 양소유 프로필 아바타는 이미 존재하는 이미지 파일 `frontend/src/assets/images/yangsoyu.png`를 사용한다(시안의 `yang-soyu-avatar.png` 자리).
- 시안 CSS의 디자인 토큰/레이아웃을 "정답"으로 삼는다(AGENTS.md). 로그인/인증 기능은 다루지 않는다. 한국어 원문 콘텐츠(노드 목록, 설명 텍스트, 예시 질문, 인사말 등)는 그대로 보존한다.
- 어시스턴트 답변은 기존과 동일하게 `react-markdown` + `remark-gfm`으로 렌더링한다.

이식 대상 화면 요소:
- **Chat Area(좌)**: 헤더(제목 + 설명 + "새 대화" 버튼), 메시지 로그(양소유 아바타 + 이름 + 말풍선 + source-note), 하단 composer(자동 높이 조절 textarea, Enter 전송 / Shift+Enter 줄바꿈, 전송 버튼, 안내 문구). 첫 진입 시 양소유 페르소나 인사말이 기본 표시된다.
- **Guide Panel(우)**: kicker + 제목 + 설명, 4개 카테고리 탭(서지적요소/참여적요소/배열적요소/표현적요소), 카테고리별 노드 버튼 그룹, 노드 설명 박스, 예시 질문 6개.
- **반응형**: 960px 이하 단일 컬럼(Guide Panel이 Chat Area 아래로), 620px 이하 모바일 조정, `prefers-reduced-motion` 대응.

## Glossary

- **Chat_Page**: 이식 대상인 React 페이지 컴포넌트(`ChatPage`). Chat Area와 Guide Panel을 포함한다.
- **Chat_Area**: 화면 좌측 영역. 헤더, 메시지 로그, composer로 구성된다.
- **Guide_Panel**: 화면 우측 영역. 카테고리 탭, 노드 그룹, 노드 설명 박스, 예시 질문으로 구성된다.
- **Message_Log**: 대화 메시지들이 시간순으로 쌓이는 스크롤 영역.
- **Message**: 하나의 대화 항목. `role`(`user` 또는 `assistant`)과 `content`(문자열)를 가진다.
- **Persona_Greeting**: 양소유 페르소나의 초기 인사말 어시스턴트 메시지(한국어 원문, 시안에서 제공됨).
- **Composer**: 하단 입력 영역. 자동 높이 조절 textarea와 전송 버튼, 안내 문구로 구성된다.
- **Category_Tab**: Guide Panel 상단의 카테고리 선택 탭. 4종(`bibliographic` 서지적요소, `participatory` 참여적요소, `arrangement` 배열적요소, `expressive` 표현적요소). 각 탭은 고유 색상 토큰과 SVG 아이콘을 가진다.
- **Node_Group**: 특정 Category_Tab에 속한 노드 버튼들의 묶음. 선택된 카테고리의 그룹만 노출된다.
- **Node_Button**: Node_Group 안의 개별 노드 선택 버튼(한국어 원문 라벨).
- **Node_Description**: 선택된 노드의 설명을 보여주는 박스. `strong` 제목과 `p` 설명으로 구성되며, 카테고리에 따라 왼쪽 보더 색이 달라진다.
- **Example_Question**: Guide Panel의 예시 질문 버튼(총 6개, 한국어 원문).
- **Chat_Stream_Hook**: 기존 스트리밍 연동 훅 `useChatStream()`. `send(message, { onDelta })`와 `isStreaming`을 제공한다.
- **Design_Tokens**: `home.css`의 `.home-root` 스코프에 정의된 Ghibli Meadow 디자인 토큰(`--green-*`, `--font-title`, `--font-body`, `--white`, `--text`, `--border`, `--shadow` 등).
- **ApiError**: 백엔드 오류를 나타내는 예외 타입(`frontend/src/utils/api.ts`). `status` 필드를 가진다.

## Requirements

### Requirement 1: 페이지 레이아웃 및 디자인 토큰 이식

**User Story:** 사용자로서, 시안과 동일한 2컬럼 레이아웃과 톤의 AI 질문 화면을 보고 싶다. 그래야 일관된 디자인 경험을 얻을 수 있다.

#### Acceptance Criteria

1. THE Chat_Page SHALL render a two-column layout consisting of Chat_Area on the left and Guide_Panel on the right, excluding the design mockup's top topbar.
2. THE Chat_Page SHALL apply the Design_Tokens defined in the `.home-root` scope for colors, typography, radius, and shadow.
3. WHERE the design mockup defines local CSS variables that duplicate existing Design_Tokens, THE Chat_Page SHALL reuse the existing Design_Tokens rather than redefining conflicting global variables.
4. THE Chat_Page SHALL preserve existing markdown styles (`.chat-bubble` rules) and SHALL NOT break CSS classes reused by other pages (for example KeywordSearchPage and placeholder-page).
5. WHILE the viewport width is 960px or less, THE Chat_Page SHALL render Guide_Panel below Chat_Area in a single column.
6. WHILE the viewport width is 620px or less, THE Chat_Page SHALL apply the mobile layout adjustments defined in the design mockup media queries.
7. WHERE the user agent requests reduced motion, THE Chat_Page SHALL disable non-essential animations in accordance with the `prefers-reduced-motion` media query.

### Requirement 2: 메시지 로그 및 페르소나 인사말

**User Story:** 사용자로서, 대화 내역을 양소유 페르소나 형태로 보고 싶다. 그래야 몰입감 있게 질문하고 답변을 읽을 수 있다.

#### Acceptance Criteria

1. WHEN the Chat_Page first loads, THE Message_Log SHALL display the Persona_Greeting as an assistant Message.
2. THE Message_Log SHALL render each assistant Message with the Yang Soyu avatar image (`frontend/src/assets/images/yangsoyu.png`), the persona name label, a message bubble, and a source-note element.
3. THE Message_Log SHALL render each assistant Message bubble content as markdown using `react-markdown` with `remark-gfm`.
4. WHEN a new Message is appended to the Message_Log, THE Message_Log SHALL scroll to reveal the latest Message.
5. THE Message_Log SHALL render each user Message with the user-side styling defined in the design mockup.

### Requirement 3: 스트리밍 백엔드 연동

**User Story:** 사용자로서, 질문을 보내면 실제 백엔드로부터 토큰 단위로 흐르는 답변을 보고 싶다. 그래야 즉각적인 피드백을 받을 수 있다.

#### Acceptance Criteria

1. WHEN the user submits a non-empty question, THE Chat_Page SHALL send the question through the Chat_Stream_Hook and SHALL NOT use any static demo answer data.
2. WHEN a token delta is received from the stream, THE Chat_Page SHALL append the delta to the content of the current assistant Message.
3. WHILE a response is streaming, THE Chat_Page SHALL disable the Composer send action so that concurrent submissions are prevented.
4. IF the user submits an empty or whitespace-only question, THEN THE Chat_Page SHALL prevent the submission and maintain the current Message_Log state.
5. IF the stream returns an error event, THEN THE Chat_Page SHALL remove the empty pending assistant Message and display an error message in Korean.
6. IF the request fails with an ApiError whose status is 503, THEN THE Chat_Page SHALL display the Korean message indicating the AI response feature is not configured (OPENAI_API_KEY required).

### Requirement 4: Composer 입력 동작

**User Story:** 사용자로서, 자연스러운 입력 경험(자동 높이, Enter 전송, Shift+Enter 줄바꿈)을 원한다. 그래야 편하게 질문을 작성할 수 있다.

#### Acceptance Criteria

1. WHILE the user types in the Composer textarea, THE Composer SHALL adjust the textarea height to fit the content.
2. WHEN the user presses Enter without the Shift key in the Composer textarea, THE Chat_Page SHALL submit the current input as a question.
3. WHEN the user presses Enter with the Shift key in the Composer textarea, THE Composer SHALL insert a line break and SHALL NOT submit the input.
4. WHEN a question is submitted successfully, THE Composer SHALL clear the textarea content and reset the textarea height.
5. THE Composer SHALL display the guidance text "Enter 전송 · Shift+Enter 줄바꿈".

### Requirement 5: Guide Panel 카테고리 탭

**User Story:** 사용자로서, 데이터베이스 요소를 카테고리별로 탐색하고 싶다. 그래야 어떤 질문을 할 수 있는지 파악할 수 있다.

#### Acceptance Criteria

1. THE Guide_Panel SHALL display the kicker text "Ask the database", a title, and a description as defined in the design mockup.
2. THE Guide_Panel SHALL display four Category_Tabs: bibliographic (서지적요소), participatory (참여적요소), arrangement (배열적요소), and expressive (표현적요소).
3. THE Guide_Panel SHALL render each Category_Tab with the category-specific color token and SVG icon defined in the design mockup, preserving the mockup's original color values.
4. WHEN the user selects a Category_Tab, THE Guide_Panel SHALL display the Node_Group associated with that category and hide the other Node_Groups.
5. WHEN the user selects a Category_Tab, THE Guide_Panel SHALL set `aria-selected` to true on the selected Category_Tab and false on the other Category_Tabs.
6. THE Category_Tabs SHALL be operable by keyboard using button semantics.

### Requirement 6: 노드 선택 및 설명 표시

**User Story:** 사용자로서, 각 노드가 무엇을 의미하는지 설명을 보고 싶다. 그래야 원하는 데이터를 이해하고 질문에 활용할 수 있다.

#### Acceptance Criteria

1. THE Guide_Panel SHALL render each Node_Group with its Node_Buttons using the Korean node labels from the design mockup.
2. WHEN a Category_Tab is selected and no Node_Button has yet been chosen, THE Node_Description SHALL display a guidance text prompting the user to select a node (for example "노드를 선택하면 설명이 표시됩니다").
3. WHEN the user clicks a Node_Button, THE Node_Description SHALL display the selected node's title as a `strong` element and its description as a `p` element using the Korean text from the design mockup.
4. WHEN the user clicks a Node_Button, THE Node_Description SHALL set its left border color according to the selected node's category.
5. THE Node_Buttons SHALL be operable by keyboard using button semantics.

### Requirement 7: 예시 질문 및 새 대화

**User Story:** 사용자로서, 예시 질문으로 시작하거나 대화를 초기화하고 싶다. 그래야 쉽게 질문을 시작하거나 새로 시작할 수 있다.

#### Acceptance Criteria

1. THE Guide_Panel SHALL display six Example_Question buttons using the Korean question text from the design mockup.
2. WHEN the user clicks an Example_Question button, THE Composer SHALL fill the textarea with that question's text and SHALL NOT automatically submit the question.
3. WHEN the user clicks the "새 대화" button, THE Message_Log SHALL clear all Messages and then display only the Persona_Greeting.
4. THE Example_Question buttons and the "새 대화" button SHALL be operable by keyboard using button semantics.
