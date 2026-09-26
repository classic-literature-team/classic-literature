# Requirements Document

## Introduction

AI 질문(ChatPage)의 어시스턴트 답변 아래에 "왜 이런 답이 나왔지?" 토글을 두고, 누르면 답변이 만들어진 근거(trace)를 펼쳐 보여주는 기능이다. 근거는 정적 목업이 아니라 백엔드가 이번 질문을 처리하며 실제로 호출한 도구(`search_hanmun_novel_db`)의 호출 인자와 조회 결과에서 수집한 데이터로 채운다. 근거 패널은 다섯 항목(탐색 경로 / 조회한 노드(클래스) / 연결 관계 / 답변 근거 요약 / 관련 노드 테이블)으로 구성하며 시안의 Cypher 항목은 제외한다.

근거 데이터는 기존 SSE 스트리밍 계약(`delta`/`done`/`error`)을 유지한 채, 답변 델타 스트리밍이 끝난 뒤 `done` 직전에 `data: {"trace": {...}}` 이벤트를 한 번 흘려 전달한다. 한 질문에서 도구를 여러 번 호출하면 근거를 단일 trace로 병합한다. 도구를 한 번도 쓰지 않았거나 오류가 발생하면 trace를 전송하지 않고, 프론트는 근거 버튼/패널을 렌더하지 않는다. 색상은 프로젝트 Ghibli Meadow(하늘색) 토큰으로 이식하며 `.home-root` 스코프에 스타일을 추가한다. 접근성(시맨틱 버튼, `aria-expanded`/`aria-controls`/`aria-selected`, 키보드 접근)과 AGENTS.md 원칙(한국어 원문 보존)을 준수한다.

## Glossary

- **Trace_Collector**: 한 요청 동안 도구가 남기는 구조화 근거를 asyncio 태스크 단위로 격리 저장하는 `contextvars.ContextVar` 기반 요청 단위 수집기 (`app/agents/trace.py`).
- **Tool_Instrumentation**: 도구 `search_hanmun_novel_db`가 LLM용 텍스트를 반환하기 직전, 조회 과정에서 계산한 구조화 데이터를 Trace_Collector에 기록하는 계측 로직 (`app/agents/tools.py`).
- **Trace_Builder**: 수집된 여러 `ToolQueryRecord`를 병합 규칙에 따라 단일 trace 페이로드로 만드는 함수 `build_trace_payload` (`app/agents/trace.py`).
- **Chat_Stream_Route**: SSE 이벤트(`delta`/`trace`/`done`/`error`)를 방출하는 `chat_stream` 라우트 (`app/api/routes/chat.py`).
- **Chat_Stream_Parser**: 프론트의 SSE 파서 `useChatStream` (`frontend/src/hooks/useChat.ts`).
- **Answer_Trace_Panel**: 근거를 렌더하는 프론트 컴포넌트 (`frontend/src/components/chat/AnswerTracePanel.tsx`).
- **Answer_Trace**: SSE `trace` 이벤트 본문이자 프론트 상태의 근거 객체. 필드: `path`, `classes`, `relations`, `evidence`, `records`.
- **Tool_Query_Record**: 도구가 한 번 조회할 때마다 남기는 원본 기록(`table`, `node_class`, `filters`, `steps`, `total`, `shown_rows`, `relations`, `path_segments`).
- **Trace_Record_Group**: 클래스별 레코드 미리보기 표 데이터(`key`, `node_class`, `label`, `total`, `shown`, `columns`, `rows`).

## Requirements

### Requirement 1: 도구 조회 근거의 구조화 수집

**User Story:** 개발자로서, 도구가 조회하며 계산한 구조화 데이터를 원천에서 그대로 수집하고 싶다. 그래야 반환 텍스트를 파싱하지 않고도 정확한 근거 표를 만들 수 있다.

#### Acceptance Criteria

1. WHEN Tool_Instrumentation 이 단일 조회 모드로 실행되어 결과를 반환하기 직전이면, THE Tool_Instrumentation SHALL 조회한 클래스, 적용된 filters, 전체 건수(total), 표시 레코드 행(shown_rows), 등장한 관계명을 담은 Tool_Query_Record 를 Trace_Collector 에 기록한다.
2. WHEN Tool_Instrumentation 이 경로 탐색 모드로 실행되어 경로를 찾으면, THE Tool_Instrumentation SHALL 경로 단계 라벨(path_segments)과 경로에 등장한 클래스 및 관계명을 담은 Tool_Query_Record 를 Trace_Collector 에 기록한다.
3. WHERE 도구 실행이 스키마 안내 모드(schema_only)이면, THE Tool_Instrumentation SHALL Trace_Collector 에 근거를 기록하지 않는다.
4. IF 도구 실행이 오류를 반환하거나 조회 결과가 없으면, THEN THE Tool_Instrumentation SHALL 해당 조회에 대한 레코드 근거를 Trace_Collector 에 기록하지 않는다.
5. THE Tool_Instrumentation SHALL 도구가 LLM 에 반환하는 텍스트 값을 변경하지 않는다.
6. WHEN Tool_Instrumentation 이 레코드 행을 직렬화하면, THE Tool_Instrumentation SHALL 각 레코드의 비어있지 않은 컬럼만 담고 장문 컬럼(LONG_COLS)을 120자로 축약한다.

### Requirement 2: 요청 단위 근거 격리

**User Story:** 시스템 운영자로서, 동시에 처리되는 여러 요청의 근거가 서로 섞이지 않기를 원한다. 그래야 각 사용자가 자기 질문의 정확한 근거만 보게 된다.

#### Acceptance Criteria

1. WHEN Chat_Stream_Route 가 새 스트리밍 요청을 시작하면, THE Chat_Stream_Route SHALL 현재 요청의 Trace_Collector 를 reset 하여 비운 상태에서 시작한다.
2. WHILE 여러 요청이 동시에 스트리밍 중이면, THE Trace_Collector SHALL 각 asyncio 태스크의 기록을 다른 요청과 격리하여 저장한다.
3. THE Trace_Collector SHALL 한 요청에서 기록된 모든 Tool_Query_Record 의 스냅샷을 기록된 순서대로 반환한다.

### Requirement 3: 다중 도구 호출의 단일 trace 병합

**User Story:** 사용자로서, 한 질문에 여러 번 조회가 일어나도 근거를 하나로 정리해서 보고 싶다. 그래야 여러 조각으로 흩어진 근거 대신 통합된 그림을 얻는다.

#### Acceptance Criteria

1. WHEN Trace_Builder 가 하나 이상의 Tool_Query_Record 를 받으면, THE Trace_Builder SHALL 등장한 클래스를 첫 등장 순서를 유지한 합집합으로 병합하고 중복을 제거한다.
2. WHEN Trace_Builder 가 하나 이상의 Tool_Query_Record 를 받으면, THE Trace_Builder SHALL 등장한 관계명을 첫 등장 순서를 유지한 합집합으로 병합하고 중복을 제거한다.
3. WHEN Trace_Builder 가 같은 클래스의 레코드를 여러 기록에서 받으면, THE Trace_Builder SHALL 해당 클래스의 레코드를 id 기준으로 중복 제거하여 하나의 Trace_Record_Group 으로 누적한다.
4. WHEN Trace_Builder 가 같은 클래스를 조회한 여러 기록의 total 을 병합하면, THE Trace_Builder SHALL 그 클래스의 total 을 해당 조회들의 total 중 최댓값으로 설정한다.
5. WHEN Trace_Builder 가 한 클래스의 Trace_Record_Group 을 만들면, THE Trace_Builder SHALL columns 를 그 클래스 레코드들에 등장한 컬럼의 등장 순서를 유지한 합집합으로 설정한다.
6. WHEN 병합된 기록에 경로 탐색 단계가 존재하면, THE Trace_Builder SHALL path 를 병합된 경로 단계의 한국어 라벨 목록으로 설정한다.
7. IF 병합된 기록에 경로 탐색 단계가 없으면, THEN THE Trace_Builder SHALL path 를 조회한 클래스의 한국어 라벨 나열로 설정한다.
8. WHEN Trace_Builder 가 근거 요약을 생성하면, THE Trace_Builder SHALL 각 클래스에 대해 조회 건수 요약 문장을 evidence 목록에 포함한다.
9. IF Trace_Builder 가 받은 Tool_Query_Record 목록이 비어 있으면, THEN THE Trace_Builder SHALL None 을 반환한다.
10. THE Trace_Builder SHALL 각 클래스의 한국어 label 을 클래스명 매핑표에 따라 부여한다.

### Requirement 4: trace 를 SSE 이벤트로 전송

**User Story:** 프론트엔드 개발자로서, 기존 스트리밍 계약을 깨지 않고 근거를 받고 싶다. 그래야 답변 표시 로직을 그대로 두고 근거만 추가로 처리할 수 있다.

#### Acceptance Criteria

1. WHEN 답변 델타 스트리밍이 정상 종료되고 병합된 trace 가 존재하면, THE Chat_Stream_Route SHALL `done` 이벤트 직전에 `data: {"trace": {...}}` 이벤트를 정확히 한 번 방출한다.
2. IF 병합된 trace 가 None 이면, THEN THE Chat_Stream_Route SHALL trace 이벤트를 생략하고 `done` 이벤트만 방출한다.
3. IF 스트리밍 중 예외가 발생하면, THEN THE Chat_Stream_Route SHALL `error` 이벤트를 방출하고 trace 이벤트를 방출하지 않는다.
4. THE Chat_Stream_Route SHALL 기존 `delta`, `done`, `error` 이벤트의 형식과 순서 계약을 유지한다.

### Requirement 5: 프론트 SSE 파서의 trace 인식

**User Story:** 프론트엔드 개발자로서, SSE 파서가 trace 이벤트를 인식해 콜백으로 넘겨주기를 원한다. 그래야 근거를 메시지에 부착할 수 있다.

#### Acceptance Criteria

1. WHEN Chat_Stream_Parser 가 `trace` 필드를 가진 SSE 이벤트를 수신하면, THE Chat_Stream_Parser SHALL 파싱한 Answer_Trace 객체로 onTrace 콜백을 호출한다.
2. IF 수신한 `trace` 이벤트 본문이 예상 스키마와 다르면, THEN THE Chat_Stream_Parser SHALL 해당 이벤트를 무시하고 onTrace 콜백을 호출하지 않는다.
3. WHILE `trace` 이벤트 처리가 실패하는 상황이면, THE Chat_Stream_Parser SHALL 답변 본문의 `delta`/`done`/`error` 처리를 정상 진행한다.
4. THE Chat_Stream_Parser SHALL 기존 `delta`, `done`, `error` 이벤트 처리 동작을 변경 없이 유지한다.

### Requirement 6: 근거를 어시스턴트 메시지에 부착

**User Story:** 사용자로서, 근거가 자기 답변에 정확히 연결되기를 원한다. 그래야 어떤 답변의 근거인지 혼동하지 않는다.

#### Acceptance Criteria

1. WHEN Chat_Stream_Parser 가 onTrace 를 호출하면, THE ChatPage SHALL 해당 응답의 마지막 assistant 메시지에 Answer_Trace 를 부착한다.
2. WHERE 어떤 assistant 메시지에 Answer_Trace 가 부착되지 않았으면, THE Answer_Trace_Panel SHALL 그 메시지에 대해 근거 버튼과 패널을 렌더하지 않는다.

### Requirement 7: 근거 패널 렌더링과 다섯 항목

**User Story:** 사용자로서, 답변 근거를 다섯 항목으로 정리된 형태로 보고 싶다. 그래야 어떤 데이터를 근거로 답이 나왔는지 이해할 수 있다.

#### Acceptance Criteria

1. WHERE assistant 메시지에 Answer_Trace 가 부착되어 있으면, THE Answer_Trace_Panel SHALL "왜 이런 답이 나왔지?" 토글 버튼을 어시스턴트 답변 아래에 렌더한다.
2. WHEN 사용자가 토글 버튼을 활성화하면, THE Answer_Trace_Panel SHALL 근거 패널을 펼쳐 표시한다.
3. WHEN 근거 패널이 펼쳐지면, THE Answer_Trace_Panel SHALL 탐색 경로(path), 조회한 노드(classes), 연결 관계(relations), 답변 근거 요약(evidence), 관련 노드 테이블(records) 다섯 항목을 표시한다.
4. THE Answer_Trace_Panel SHALL Cypher 쿼리 항목을 표시하지 않는다.
5. WHEN Answer_Trace_Panel 이 조회한 노드를 표시하면, THE Answer_Trace_Panel SHALL 각 클래스의 한국어 label 과 node_class 를 함께 표기한다.
6. WHEN Answer_Trace_Panel 이 연결 관계를 표시하면, THE Answer_Trace_Panel SHALL 각 관계의 원문 관계명과 한국어 병기(korean)를 함께 표기한다.

### Requirement 8: 관련 노드 테이블(탭 전환과 건수 표기)

**User Story:** 사용자로서, 조회된 실제 레코드를 클래스별로 미리 보고 싶다. 그래야 근거가 되는 데이터를 직접 확인할 수 있다.

#### Acceptance Criteria

1. WHEN 관련 노드 테이블이 표시되면, THE Answer_Trace_Panel SHALL 각 Trace_Record_Group 을 클래스별 탭으로 제공한다.
2. WHEN 사용자가 특정 클래스 탭을 선택하면, THE Answer_Trace_Panel SHALL 그 클래스의 columns 를 헤더로, rows 를 행으로 하는 표를 표시한다.
3. WHEN 관련 노드 테이블의 한 클래스 탭이 표시되면, THE Answer_Trace_Panel SHALL "전체 N건 중 M건 미리보기" 형식으로 total(N)과 shown(M)을 표기한다.
4. WHEN Answer_Trace_Panel 이 표의 셀 값을 표시하면, THE Answer_Trace_Panel SHALL 값을 텍스트로만 렌더하고 마크다운 또는 HTML 로 해석하지 않는다.

### Requirement 9: 접근성

**User Story:** 보조기술 사용자로서, 근거 토글과 탭을 키보드로 조작하고 상태를 인지하고 싶다. 그래야 마우스 없이도 근거를 탐색할 수 있다.

#### Acceptance Criteria

1. THE Answer_Trace_Panel SHALL 토글 버튼과 탭을 `<button>` 시맨틱 요소로 렌더한다.
2. THE Answer_Trace_Panel SHALL 토글 버튼에 패널의 펼침 상태를 나타내는 `aria-expanded` 와 패널을 가리키는 `aria-controls` 속성을 부여한다.
3. THE Answer_Trace_Panel SHALL 선택된 탭에 `aria-selected` 속성을 부여한다.
4. THE Answer_Trace_Panel SHALL 토글 버튼과 탭을 키보드로 조작 가능하게 한다.

### Requirement 10: 색상 토큰 이식과 원문 보존

**User Story:** 개발자로서, 근거 패널이 프로젝트 디자인 체계와 일관되기를 원한다. 그래야 시안의 다른 색이 튀지 않고 통합된다.

#### Acceptance Criteria

1. THE Answer_Trace_Panel 스타일 SHALL 프로젝트 Ghibli Meadow 디자인 토큰(`--green-*`, `--sky`, `--border`, `--shadow`, `--font-title`)을 사용한다.
2. THE Answer_Trace_Panel 스타일 SHALL `.home-root` 스코프 안에 정의한다.
3. THE Answer_Trace_Panel SHALL 한국어 원문 콘텐츠를 원문 그대로 보존하여 표시한다.
