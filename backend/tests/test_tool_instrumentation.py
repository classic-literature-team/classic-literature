"""Task 3.2 — 도구 계측 단위 테스트 (모드별 기록 여부).

``search_hanmun_novel_db`` 가 조회 모드별로 근거 수집기(TraceCollector)에
기록하는지/안 하는지와, LLM 에 반환하는 텍스트가 계측과 무관하게 불변인지를
검증한다.

@function_tool 언랩 방식
------------------------
``@function_tool(strict_mode=False)`` 는 원본 함수를 ``agents.tool.FunctionTool``
인스턴스로 감싼다. 이 인스턴스는 원본 함수를 직접 노출하지 않지만, SDK 가 실제
도구를 실행할 때 쓰는 진입점 ``on_invoke_tool(ctx, input_json)`` 를 공개한다.
- ``ctx`` 는 ``agents.tool_context.ToolContext`` 인스턴스(실행 문맥)다.
- ``input_json`` 은 도구 인자를 담은 JSON 문자열이며, SDK 가 이를 파싱해 원본
  함수를 호출한다.
따라서 원본 함수 로직(내부 ``_traverse``/``_serialize_row``/``current_collector``
호출 포함)을 그대로 태우려면 ``on_invoke_tool`` 을 호출하면 된다. 이는 SDK 가
런타임에 밟는 경로와 동일하므로, 언랩된 원본 함수를 억지로 꺼내는 것보다
견고하고 계약에 충실하다.

DB 목(mock)
-----------
``tools.py`` 는 ``with SessionLocal() as db:`` 패턴을 쓴다. monkeypatch 로
``app.agents.tools.SessionLocal`` 을 컨텍스트매니저 목으로 교체하고, 목 db 의
``scalar``/``scalars`` 반환을 케이스별로 제어한다. 행/엣지는 실제 모델
(``app.models`` 의 ``Book``/``Edge``)의 최소 인스턴스로 만든다(세션 없이 생성 가능).
"""

from __future__ import annotations

import asyncio
import json

import pytest
from agents.tool_context import ToolContext

import app.agents.tools as tools_mod
from app.agents.tools import search_hanmun_novel_db
from app.agents.trace import current_collector
from app.models import Book, Edge

# ---------------------------------------------------------------------------
# DB 목: SessionLocal() 컨텍스트매니저와 db 세션 흉내
# ---------------------------------------------------------------------------


class _MockScalars:
    """``db.scalars(...)`` 결과 흉내: ``list()``/``__iter__``/``.all()`` 지원."""

    def __init__(self, values: list) -> None:
        self._values = list(values)

    def all(self) -> list:
        return list(self._values)

    def __iter__(self):
        return iter(self._values)


class _MockDB:
    """``scalar``/``scalars``/``execute`` 만 흉내내는 최소 목 세션.

    - ``scalar`` 는 고정 ``total`` 을 반환한다(단일 조회의 전체 건수).
    - ``scalars`` 는 호출 순서대로 ``scalars_queue`` 의 다음 목록을 반환한다.
      단일 조회 경로에서는 [행들] → [엣지들] 순으로 호출되고, 경로 탐색에서는
      [출발노드들] → [엣지들] 순으로 호출된다. 큐가 비면 빈 결과를 준다.
    - ``execute`` 는 ``schema_only`` 전체 안내 경로에서만 쓰이며 ``.all()`` 지원.
    """

    def __init__(
        self, *, total: int = 0, scalars_queue: list[list] | None = None
    ) -> None:
        self._total = total
        self._queue = list(scalars_queue or [])

    def scalar(self, stmt) -> int:  # noqa: ANN001 - 목: stmt 무시
        return self._total

    def scalars(self, stmt) -> _MockScalars:  # noqa: ANN001
        if self._queue:
            return _MockScalars(self._queue.pop(0))
        return _MockScalars([])

    def execute(self, stmt):  # noqa: ANN001
        class _Result:
            def all(self_inner) -> list:  # noqa: N805
                return []

        return _Result()


class _MockSession:
    """``with SessionLocal() as db:`` 의 컨텍스트매니저를 흉내낸다."""

    def __init__(self, db: _MockDB) -> None:
        self._db = db

    def __enter__(self) -> _MockDB:
        return self._db

    def __exit__(self, *exc) -> bool:
        return False


def _patch_session(monkeypatch: pytest.MonkeyPatch, db: _MockDB) -> None:
    """app.agents.tools.SessionLocal 을 목 세션 팩토리로 교체한다."""
    monkeypatch.setattr(tools_mod, "SessionLocal", lambda: _MockSession(db))


def _invoke(**kwargs) -> tuple[str, list]:
    """FunctionTool 을 SDK 진입점(on_invoke_tool)으로 실행한다.

    reset → 도구 실행 → snapshot 을 모두 하나의 ``asyncio.run`` 안에서 처리해,
    수집기 바인딩이 그 실행의 격리된 contextvars 문맥 안에서만 일어나게 한다.
    이렇게 하면 pytest 메인 스레드의 루트 문맥에 수집기가 남지 않아, 같은
    세션에서 실행되는 다른 테스트(예: 동시성 격리 property 테스트)의 지연
    바인딩 전제를 오염시키지 않는다.

    kwargs 는 도구 인자(table/filters/steps/...)이며 JSON 으로 직렬화해 넘긴다.

    Returns:
        (반환 텍스트, 수집기 스냅샷) 튜플.
    """
    ctx = ToolContext(
        context=None,
        tool_name="search_hanmun_novel_db",
        tool_call_id="test_call",
        tool_arguments="{}",
    )
    payload = json.dumps(kwargs, ensure_ascii=False)

    async def _run() -> tuple[str, list]:
        collector = current_collector()
        collector.reset()
        out = await search_hanmun_novel_db.on_invoke_tool(ctx, payload)
        return out, collector.snapshot()

    return asyncio.run(_run())


# ---------------------------------------------------------------------------
# (1) 단일 조회 성공 → record 1건, node_class 정확, 반환 텍스트 불변
# ---------------------------------------------------------------------------


def test_single_query_records_one_with_correct_node_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """단일 조회 성공 시 record 1건이 남고 node_class/총건수/관계가 정확하다.

    Validates: Requirements 1.2(단일 조회 계측), 1.5(반환 텍스트 불변)
    """
    book = Book(
        id="book_1",
        name="운영전",
        title_name_kor="운영전",
        institution_kor="장서각",
    )
    edge = Edge(
        source_class="Book",
        source_id="book_1",
        source_name="운영전",
        target_class="Scene",
        target_id="sc_1",
        target_name="장면1",
        relation="contains",
    )
    # scalars 호출 순서: [행들] → [엣지들]
    db = _MockDB(total=142, scalars_queue=[[book], [edge]])
    _patch_session(monkeypatch, db)

    out, snapshot = _invoke(table="book", filters={})

    # 반환 텍스트(LLM 계약)는 계측과 무관하게 기존 형식 그대로다.
    assert out.startswith("전체 142건 중 1건 표시.")
    assert "id: book_1" in out
    assert "→ [contains/보유한다] Scene: 장면1" in out

    assert len(snapshot) == 1
    rec = snapshot[0]
    assert rec.node_class == "Book"  # KEY_TO_CLASS["book"]
    assert rec.table == "book"
    assert rec.total == 142
    assert rec.steps is None
    assert rec.relations == ["contains"]
    # shown_rows: 비어있지 않은 컬럼만 담긴 직렬화 결과.
    assert rec.shown_rows == [
        {
            "id": "book_1",
            "name": "운영전",
            "title_name_kor": "운영전",
            "institution_kor": "장서각",
        }
    ]


# ---------------------------------------------------------------------------
# (2) 무결과 → record 0건, 반환 텍스트 불변
# ---------------------------------------------------------------------------


def test_no_result_records_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """조회 결과가 없으면 근거를 기록하지 않는다.

    Validates: Requirements 1.4(무결과 미기록), 1.5(반환 텍스트 불변)
    """
    db = _MockDB(total=0, scalars_queue=[[]])  # 행 없음
    _patch_session(monkeypatch, db)

    out, snapshot = _invoke(table="book", filters={"title_name_kor": "없는작품"})

    assert out == "조건에 맞는 데이터를 찾지 못했습니다."
    assert snapshot == []


# ---------------------------------------------------------------------------
# (3) schema_only → record 0건
# ---------------------------------------------------------------------------


def test_schema_only_records_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """스키마 안내 모드(schema_only)는 근거를 기록하지 않는다.

    Validates: Requirements 1.3(schema_only 미기록), 1.5(반환 텍스트 불변)
    """
    # _describe_table 은 각 컬럼마다 db.scalars(...).all() 을 호출한다.
    db = _MockDB(scalars_queue=[])  # 큐가 비면 매번 빈 결과 → 컬럼명만 나열
    _patch_session(monkeypatch, db)

    out, snapshot = _invoke(table="book", filters={}, schema_only=True)

    # 스키마 안내 텍스트(조회 아님)이며, 근거는 남기지 않는다.
    assert out.startswith("[book] 컬럼 목록")
    assert snapshot == []


# ---------------------------------------------------------------------------
# (4) 오류(ValueError: 존재하지 않는 filters 컬럼) → record 0건
# ---------------------------------------------------------------------------


def test_error_invalid_filter_column_records_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """오류(존재하지 않는 filters 컬럼)로 조회가 실패하면 근거를 기록하지 않는다.

    ``_apply_filters`` 는 모델에 없는 컬럼이면 ValueError 를 던지고, 도구는 이를
    붙잡아 오류 메시지 텍스트를 반환한다. 이때 record 는 남지 않아야 한다.

    Validates: Requirements 1.4(오류 미기록), 1.5(반환 텍스트 불변)
    """
    db = _MockDB(total=0, scalars_queue=[])
    _patch_session(monkeypatch, db)

    out, snapshot = _invoke(table="book", filters={"nonexistent_col": "x"})

    # 오류 메시지 텍스트가 반환된다(예외로 전파되지 않는다).
    assert "'nonexistent_col' 컬럼이 없습니다." in out
    assert snapshot == []


# ---------------------------------------------------------------------------
# (5) 경로 탐색 성공 → record 1건(steps/relations/path_segments 기록)
# ---------------------------------------------------------------------------


def test_path_traversal_records_segments_and_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """경로 탐색 모드는 path_segments 와 등장 관계명을 기록한다.

    Validates: Requirements 1.2(경로 탐색 계측), 1.5(반환 텍스트 불변)
    """
    book = Book(id="book_1", name="운영전")
    edge = Edge(
        source_class="Book",
        source_id="book_1",
        source_name="운영전",
        target_class="Scene",
        target_id="sc_1",
        target_name="장면1",
        relation="contains",
    )
    # scalars 호출 순서: [출발노드들] → [엣지들]
    db = _MockDB(scalars_queue=[[book], [edge]])
    _patch_session(monkeypatch, db)

    out, snapshot = _invoke(table="book", filters={}, steps=["contains:scene"])

    # 반환 텍스트(경로 탐색 형식)는 기존 그대로다.
    assert out.startswith("총 1개 경로를 찾았습니다.")
    assert "Book: 운영전 -[contains/보유한다]→ Scene: 장면1" in out

    assert len(snapshot) == 1
    rec = snapshot[0]
    assert rec.node_class == "Book"
    assert rec.steps == ["contains:scene"]
    assert rec.relations == ["contains"]
    assert rec.path_segments == [
        "Book: 운영전 -[contains/보유한다]→ Scene: 장면1"
    ]
    # 경로 탐색은 레코드 표가 없다(shown_rows 는 비어 있다).
    assert rec.shown_rows == []
