"""Task 4.2 — 라우트 이벤트 순서 통합 테스트 (에이전트/수집기 목).

``chat_stream`` 라우트의 SSE 이벤트 방출을 검증한다. 실제 LLM 은 쓰지 않고
``app.api.routes.chat.stream_literature_agent`` 를 가짜 async generator 로
monkeypatch 하며, 근거 수집기(TraceCollector)는 그 가짜 제너레이터가 실제
``current_collector()`` 에 ``ToolQueryRecord`` 를 넣어(또는 넣지 않아) 제어한다.

검증 케이스:
- (a) 도구 사용: delta 들 → trace → done (trace 는 정확히 1회)
- (b) 도구 미사용: delta 들 → done (trace 없음)
- (c) 스트리밍 중 예외: delta 들 → error (trace 없음)

OPENAI_API_KEY 우회
------------------
라우트는 ``settings.openai_api_key`` 가 falsy 면 503 을 던진다. 실제 키 없이
스트림 경로를 태우기 위해 ``app.api.routes.chat.settings.openai_api_key`` 를
monkeypatch 로 truthy 하게 설정한다.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

import app.api.routes.chat as chat_mod
from app.agents.trace import ToolQueryRecord, current_collector
from app.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """OPENAI_API_KEY 체크(503)를 우회한 테스트 클라이언트."""
    monkeypatch.setattr(chat_mod.settings, "openai_api_key", "test-key")
    return TestClient(create_app())


def _parse_sse(body: str) -> list[dict]:
    """SSE 응답 본문에서 ``data:`` 프레임의 JSON 페이로드 목록을 파싱한다.

    각 이벤트는 ``data: {...}\\n\\n`` 형식이므로, ``data:`` 로 시작하는 줄만
    골라 JSON 으로 로드한다. 이벤트 순서는 방출 순서 그대로 보존된다.
    """
    events: list[dict] = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        events.append(json.loads(line[len("data:") :].strip()))
    return events


def _sample_record() -> ToolQueryRecord:
    """도구 사용 케이스에서 수집기에 넣을 최소 근거 기록."""
    return ToolQueryRecord(
        table="book",
        node_class="Book",
        filters={"title_name_kor": "운영전"},
        steps=None,
        total=142,
        shown_rows=[{"id": "book_1", "title_name_kor": "운영전"}],
        relations=["contains"],
    )


# ---------------------------------------------------------------------------
# (a) 도구 사용 → delta… → trace → done
# ---------------------------------------------------------------------------


def test_tool_used_emits_delta_then_trace_then_done(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """도구 사용 시 delta 들 뒤에 trace 1회, 그다음 done 이 방출된다.

    Validates: Requirements 4.1(trace 1회, done 직전), 4.4(형식·순서 유지)
    """

    async def fake_stream(message: str) -> AsyncIterator[str]:
        # 라우트가 reset 한 현재 수집기에 근거를 남겨 도구 사용을 흉내낸다.
        current_collector().record(_sample_record())
        for piece in ["안", "녕", "하냐"]:
            yield piece

    monkeypatch.setattr(chat_mod, "stream_literature_agent", fake_stream)

    resp = client.post("/api/chat/stream", json={"message": "운영전 이본?"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    kinds = [next(iter(e)) for e in events]  # 각 이벤트의 유일 키

    # 순서 계약: delta 들 → trace → done.
    assert kinds == ["delta", "delta", "delta", "trace", "done"]

    # delta 내용이 순서대로 보존된다.
    deltas = [e["delta"] for e in events if "delta" in e]
    assert deltas == ["안", "녕", "하냐"]

    # trace 는 정확히 1회이며, 병합된 페이로드 스키마를 갖는다.
    assert kinds.count("trace") == 1
    trace = next(e["trace"] for e in events if "trace" in e)
    assert [c["node_class"] for c in trace["classes"]] == ["Book"]
    assert trace["relations"] == [
        {"name": "contains", "korean": "보유한다"}
    ]
    assert trace["records"][0]["total"] == 142

    # done 은 마지막 이벤트이며 형식은 {"done": true} 그대로.
    assert events[-1] == {"done": True}


# ---------------------------------------------------------------------------
# (b) 도구 미사용 → delta… → done (trace 생략)
# ---------------------------------------------------------------------------


def test_no_tool_used_omits_trace(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """도구 미사용(수집기 비어 있음) 시 trace 를 생략하고 done 만 방출한다.

    Validates: Requirements 4.2(trace None 이면 생략)
    """

    async def fake_stream(message: str) -> AsyncIterator[str]:
        # 수집기에 아무것도 기록하지 않는다 → build_trace_payload 가 None.
        for piece in ["잡", "소리"]:
            yield piece

    monkeypatch.setattr(chat_mod, "stream_literature_agent", fake_stream)

    resp = client.post("/api/chat/stream", json={"message": "오늘 날씨?"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    kinds = [next(iter(e)) for e in events]

    assert kinds == ["delta", "delta", "done"]
    assert "trace" not in kinds
    assert events[-1] == {"done": True}


# ---------------------------------------------------------------------------
# (c) 스트리밍 중 예외 → error (trace 없음)
# ---------------------------------------------------------------------------


def test_exception_emits_error_without_trace(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """스트리밍 중 예외가 나면 error 만 방출하고 trace 는 방출하지 않는다.

    수집기에 근거가 남아 있어도(예외 전에 도구를 썼더라도) 예외 경로에서는
    trace 를 보내지 않아야 한다(부분 근거 혼란 방지).

    Validates: Requirements 4.3(예외 시 error, trace 미전송)
    """

    async def fake_stream(message: str) -> AsyncIterator[str]:
        # 예외 전에 도구를 썼더라도 trace 가 나가면 안 됨을 강조하기 위해 기록.
        current_collector().record(_sample_record())
        yield "시"
        yield "작"
        raise RuntimeError("모델 오류")

    monkeypatch.setattr(chat_mod, "stream_literature_agent", fake_stream)

    resp = client.post("/api/chat/stream", json={"message": "운영전?"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    kinds = [next(iter(e)) for e in events]

    # delta 들 뒤에 error 1회로 종료. trace/done 은 없다.
    assert kinds == ["delta", "delta", "error"]
    assert "trace" not in kinds
    assert "done" not in kinds

    error_event = next(e for e in events if "error" in e)
    assert error_event["error"] == "모델 오류"
