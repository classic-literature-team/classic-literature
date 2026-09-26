# Implementation Plan: 답변 근거 패널 (answer-trace-panel)

## Overview

design.md의 컴포넌트 순서(백엔드 수집기 → 병합 빌더 → 도구 계측 → 라우트 배선 → 프론트 파서 → 메시지 부착 → 패널 컴포넌트 → 스타일)에 맞춰 점진적으로 구현한다. 각 작업은 이전 작업 위에 쌓이며, 마지막에 프론트/백엔드가 SSE `trace` 이벤트로 배선된다. 백엔드는 Python(FastAPI, SQLAlchemy, Agents SDK v0.22.0), 프론트는 TypeScript(React 19)로 구현한다.

테스트 스택 사실(작업 착수 시 확인 완료):
- 백엔드: `pytest` + `httpx` 존재, `hypothesis` 미설치 → property 테스트 도입 시 `requirements-dev.txt`에 추가 필요.
- 프론트: 테스트 러너(`vitest`)·`fast-check`·`@testing-library/react` 미설치 → 컴포넌트/파서 테스트를 위해 도구 도입 필요.

`*`로 표시된 서브태스크는 선택(테스트)이며 MVP에서 건너뛸 수 있다. 커밋 전 백엔드는 `ruff`, 프론트는 `npm run lint` / `npm run build`(tsc + vite) 통과를 기준으로 한다. 모든 표시 콘텐츠는 한국어 원문을 그대로 보존한다.

## Tasks

- [x] 1. 백엔드 근거 수집 기반 구축 (`app/agents/trace.py` 신규)
  - [x] 1.1 `ToolQueryRecord` 데이터클래스와 클래스 한국어 label 매핑 상수 정의
    - `@dataclass ToolQueryRecord`에 `table`, `node_class`, `filters`, `steps`, `total`, `shown_rows`, `relations`, `path_segments` 필드 정의
    - `CLASS_LABEL_KOR` 등 클래스명→한국어 label 매핑 상수(예: `AbstractWork`→"작품", `Book`→"이본", `Review`→"외평") 정의
    - `RELATION_KOR` 참조 위치를 확인해 관계 한국어 병기에 재사용할 수 있게 import 정리
    - _Requirements: 1.1, 3.10_

  - [x] 1.2 `TraceCollector`와 `current_collector()` (contextvars 기반) 구현
    - `contextvars.ContextVar`에 요청 단위 수집기를 바인딩하고 `reset()`/`record()`/`snapshot()` 구현
    - `snapshot()`은 기록 순서를 그대로 보존해 반환
    - `current_collector()`가 ContextVar에서 현재 수집기를 획득(없으면 새로 생성·바인딩)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x]* 1.3 TraceCollector 격리·순서 property 테스트
    - **Property 2: 동시 요청 근거 격리** — 동시 asyncio 태스크 각각의 스냅샷이 자기 기록만 포함
    - **Property 3: 스냅샷 순서 보존** — 기록 순서와 동일 순서로 반환
    - _Property: 2, 3_
    - _Requirements: 2.2, 2.3_

- [x] 2. trace 페이로드 병합 빌더 (`app/agents/trace.py`)
  - [x] 2.1 `build_trace_payload(records)` 병합 규칙 구현
    - 클래스/관계 합집합(첫 등장 순서 유지·중복 제거), 클래스별 레코드 `id` 중복 제거, `total`은 조회들의 최댓값, `columns`는 등장 순서 유지 합집합
    - `path`: 경로 단계 존재 시 병합 경로의 한국어 라벨, 없으면 조회 클래스 label 나열
    - `evidence`: 클래스별 조회 건수 요약 문장 생성(예: "이본(Book) 142건 중 30건 확인")
    - 빈 입력이면 `None` 반환, 출력은 design.md의 JSON 스키마(`path`/`classes`/`relations`/`evidence`/`records`) 준수
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

  - [x]* 2.2 병합 빌더 단위/예제 테스트
    - 단일 호출·다중 호출 병합, 경로 재구성, 빈 입력→`None`, evidence 문장 형식을 예제로 검증
    - _Requirements: 3.6, 3.8, 3.9_

  - [x]* 2.3 병합 빌더 property 테스트 (클래스/관계 합집합·순서)
    - **Property 4: 클래스 합집합(순서 유지·중복 제거)**
    - **Property 5: 관계 합집합(순서 유지·중복 제거)**
    - _Property: 4, 5_
    - _Requirements: 3.1, 3.2_

  - [x]* 2.4 병합 빌더 property 테스트 (레코드 병합 불변식)
    - **Property 6: 클래스별 레코드 id 중복 제거**
    - **Property 7: 클래스별 total 최댓값**
    - **Property 8: columns 합집합과 row 키 포함 관계**
    - _Property: 6, 7, 8_
    - _Requirements: 3.3, 3.4, 3.5_

  - [x]* 2.5 병합 빌더 property 테스트 (경로/evidence 대응)
    - **Property 9: 경로 부재 시 클래스 라벨 나열**
    - **Property 10: 클래스별 evidence 대응**
    - _Property: 9, 10_
    - _Requirements: 3.7, 3.8_

- [x] 3. 도구 계측 (`app/agents/tools.py` 수정)
  - [x] 3.1 `search_hanmun_novel_db`에 수집기 기록 로직 삽입
    - 단일 조회 모드: 텍스트 반환 직전 `total`/`rows`(→`shown_rows`)/`rel_map`(→`relations`)를 `current_collector().record(...)`로 기록, `node_class = KEY_TO_CLASS[table]`
    - 경로 탐색 모드: 찾은 경로를 `path_segments`로, 등장 클래스/관계를 기록
    - `schema_only`·오류·무결과는 기록하지 않음, LLM 반환 텍스트는 불변 유지
    - 행 직렬화: 비어있지 않은 컬럼만, 장문 컬럼(`LONG_COLS`) 120자 축약, 클래스당 표시 행은 `limit`(기본 30) 준수
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x]* 3.2 도구 계측 단위 테스트 (모드별 기록 여부)
    - 단일 조회/경로 탐색/무결과/오류/`schema_only` 각각에서 수집기 기록 여부·내용, 반환 텍스트 불변을 검증(SessionLocal은 목 또는 테스트 DB)
    - _Requirements: 1.2, 1.3, 1.4, 1.5_

  - [x]* 3.3 행 직렬화 property 테스트
    - **Property 1: 행 직렬화 무결성** — 비어있지 않은 컬럼만 포함, 장문 컬럼 120자 이하
    - _Property: 1_
    - _Requirements: 1.6_

- [x] 4. 스트리밍 배선 (`literature_agent.py` 확인 + `app/api/routes/chat.py` 수정)
  - [x] 4.1 chat_stream 라우트에 reset/trace 이벤트 배선
    - `event_source` 시작에서 `current_collector().reset()`
    - delta 스트리밍 정상 종료 후 `done` 직전에 `build_trace_payload(snapshot())` 결과를 `trace` 이벤트로 1회 방출(`None`이면 생략)
    - 예외 시 `error` 이벤트만 방출하고 trace 미전송, 기존 `delta`/`done`/`error` 형식·순서 계약 유지
    - `stream_literature_agent`는 델타만 yield하는 기존 시그니처 유지 확인(도구 이벤트 별도 처리 불필요)
    - _Requirements: 2.1, 4.1, 4.2, 4.3, 4.4_

  - [x]* 4.2 라우트 이벤트 순서 통합 테스트 (에이전트/수집기 목)
    - 에이전트·수집기를 목으로 대체해 `delta…→trace→done` 순서, trace `None`일 때 생략, `error` 시 trace 미전송을 검증
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5. 백엔드 property 테스트 도구 도입 (기존 스택 확인 반영)
  - [x] 5.1 `hypothesis`를 `backend/requirements-dev.txt`에 추가
    - `hypothesis` 의존성 추가 후 1.3/2.3/2.4/2.5/3.3의 property 테스트가 pytest로 실행 가능하도록 설정
    - property 테스트 최소 100 iteration, 각 테스트에 `Feature: answer-trace-panel, Property N` 태그 주석 표기
    - _Requirements: 1.6, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.7, 3.8_

- [x] 6. 프론트 SSE 파서 확장 (`frontend/src/hooks/useChat.ts`)
  - [x] 6.1 Answer_Trace 타입과 `onTrace` 콜백 추가
    - `TraceClass`/`TraceRelation`/`TraceRecordGroup`/`AnswerTrace` 타입 정의
    - 파서 payload에 `trace?: AnswerTrace` 인식, 스키마 검증 후 `onTrace?.(trace)` 호출(스키마 불일치는 무시)
    - 기존 `delta`/`done`/`error` 처리 동작 변경 없이 유지
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x]* 6.2 파서 견고성 property 테스트
    - **Property 11: 파서 견고성(trace 무관 본문 처리)** — 유효/스키마 불일치 trace를 섞어도 최종 답변 텍스트·done/error 결과가 trace 없을 때와 동일
    - _Property: 11_
    - _Requirements: 5.3_

  - [x]* 6.3 파서 단위 테스트 (기존 계약 회귀 방지)
    - `trace` 포함 SSE 바이트 스트림에서 `onTrace`가 올바른 객체로 호출되는지, 스키마 불일치 시 미호출인지, 기존 `delta`/`done`/`error` 동작 유지 검증
    - _Requirements: 5.1, 5.2, 5.4_

- [x] 7. 근거를 어시스턴트 메시지에 부착 (`ChatPage.tsx`)
  - [x] 7.1 `Message.trace` 필드와 onTrace 부착 로직
    - `Message` 타입에 `trace?: AnswerTrace` 추가
    - `onTrace` 콜백에서 해당 응답의 마지막 assistant 메시지에 `trace` 부착
    - _Requirements: 6.1_

- [x] 8. AnswerTracePanel 컴포넌트 (`frontend/src/components/chat/AnswerTracePanel.tsx` 신규)
  - [x] 8.1 토글 버튼과 패널 골격
    - Props `{ trace: AnswerTrace }`, `trace` 없으면 미렌더
    - "왜 이런 답이 나왔지?" `<button>` 토글, `aria-expanded`/`aria-controls`로 패널 연결, 키보드 접근
    - 패널 헤더(kicker "Answer trace" + "답변 생성 경로"), Cypher 항목 없음
    - _Requirements: 6.2, 7.1, 7.2, 7.4, 9.1, 9.2_

  - [x] 8.2 다섯 항목 렌더 (경로/노드/관계/evidence/테이블)
    - 탐색 경로(path 칩), 조회한 노드(label + node_class 병기 칩), 연결 관계(원문 name + korean 병기 칩), 답변 근거 요약(evidence 리스트) 렌더
    - 관련 노드 테이블: 클래스별 `<button>` 탭(`aria-selected`)으로 전환, "전체 N건 중 M건 미리보기" 표기, columns/rows 표를 텍스트 전용으로 렌더(마크다운/HTML 미해석)
    - 탭도 키보드로 조작 가능하게 구현, 한국어 원문 콘텐츠 보존
    - _Requirements: 7.3, 7.5, 7.6, 8.1, 8.2, 8.3, 8.4, 9.3, 9.4, 10.3_

  - [x]* 8.3 컴포넌트 렌더/토글/탭 단위 테스트
    - trace 유무에 따른 렌더/미렌더, 토글 클릭 시 `aria-expanded` 변화, 탭 전환, "전체 N건 중 M건" 표기 검증
    - _Requirements: 6.2, 7.1, 8.3_

  - [x]* 8.4 컴포넌트 property 테스트 (칩·탭·건수·렌더)
    - **Property 12: 근거 버튼 존재 ⇔ trace 존재**
    - **Property 13: 노드 칩의 label·node_class 병기**
    - **Property 14: 관계 칩의 원문명·한국어 병기**
    - **Property 15: 클래스별 탭 대응**
    - **Property 16: 미리보기 건수 표기 정확성**
    - **Property 17: 셀 값 렌더 무결성**
    - _Property: 12, 13, 14, 15, 16, 17_
    - _Requirements: 6.2, 7.1, 7.5, 7.6, 8.1, 8.3, 8.4, 10.3_

  - [x]* 8.5 접근성 상태 property 테스트
    - **Property 18: 토글 aria 상태 일치** — `aria-expanded`가 펼침 상태와 항상 일치, `aria-controls`가 패널 id 지시
    - **Property 19: 선택 탭 aria-selected 배타성** — 선택 탭만 true, 나머지 false
    - _Property: 18, 19_
    - _Requirements: 9.2, 9.3_

- [x] 9. 프론트 테스트 도구 도입 (기존 스택 확인 반영)
  - [x] 9.1 vitest + testing-library + fast-check 설정
    - `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `fast-check`를 devDependencies에 추가하고 `test` 스크립트(`vitest --run`)·vite test 설정 구성
    - 6.2/6.3/8.3/8.4/8.5 테스트가 실행 가능하도록 배선, property 테스트 최소 100 iteration + `Feature: answer-trace-panel, Property N` 태그 주석
    - _Requirements: 5.1, 5.3, 6.2, 7.1, 8.1, 8.3, 9.2, 9.3, 10.3_

- [x] 10. 스타일 이식 (`frontend/src/styles/chat.css`)
  - [x] 10.1 answer-audit 스타일을 `.home-root` 스코프로 이식
    - 시안 answer-audit 스타일을 Ghibli Meadow 토큰(`--green-*`, `--sky`, `--border`, `--shadow`, `--font-title`)으로 매핑
    - `.home-root` 스코프 안에 정의, `prefers-reduced-motion` 대응, 반응형(≤620px에서 근거 칸 축소·탭 가로 스크롤)
    - _Requirements: 10.1, 10.2_

- [x] 11. 최종 배선 및 회귀 확인 체크포인트
  - delta→trace→done 전 구간이 실제로 배선되었는지 확인하고, 기존 스트리밍(delta/done/error)·ChatPage/useChatStream 경로에 회귀가 없는지 점검
  - 백엔드 `ruff` 통과, 프론트 `npm run lint` / `npm run build`(tsc + vite) 통과 확인
  - 모든 테스트 통과 확인, 문제가 있으면 사용자에게 질문한다.

## Notes

- `*` 표시 서브태스크는 선택(테스트)이며 MVP에서 건너뛸 수 있다. 상위(에픽) 작업에는 `*`를 붙이지 않는다.
- 각 작업은 requirements.md 조항을 `_Requirements: X.Y_`로, 각 property 검증 서브태스크는 대응 property 번호를 `_Property: N_`으로 참조한다.
- design.md의 19개 Correctness Property는 property 서브태스크(1.3, 2.3, 2.4, 2.5, 3.3, 6.2, 8.4, 8.5)로 모두 배치되었다.
- 파서·컴포넌트의 기존 계약 회귀 방지 작업(6.3, 4.2, 11)으로 기존 delta/done/error·ChatPage/useChatStream 구조를 보호한다.
- property 테스트는 최소 100 iteration으로 구성하고 각 테스트에 대응 property를 태그로 표기한다.
- 배포·수동 검증·사용자 테스트 등 비코딩 작업은 포함하지 않는다.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "3.1"] },
    { "id": 2, "tasks": ["2.1", "1.3", "3.2", "3.3"] },
    { "id": 3, "tasks": ["4.1", "2.2", "2.3", "2.4", "2.5"] },
    { "id": 4, "tasks": ["5.1", "6.1", "4.2"] },
    { "id": 5, "tasks": ["7.1", "6.2", "6.3"] },
    { "id": 6, "tasks": ["8.1"] },
    { "id": 7, "tasks": ["8.2"] },
    { "id": 8, "tasks": ["10.1", "8.3", "8.4", "8.5"] },
    { "id": 9, "tasks": ["9.1"] }
  ]
}
```
