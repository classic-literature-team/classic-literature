"""Task 1.3 — TraceCollector 격리·순서 property 테스트.

Property 2(동시 요청 근거 격리)와 Property 3(스냅샷 순서 보존)을 검증한다.
DB 접속 없이 contextvars/asyncio 만 사용한다.
"""

from __future__ import annotations

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st

from app.agents.trace import ToolQueryRecord, current_collector
from tests._helpers import records_strategy


def _tag(record: ToolQueryRecord) -> str:
    """기록을 태스크별로 식별하기 위해 filters 에 심은 태그를 읽는다."""
    return record.filters.get("_task", "")


async def _task_body(task_id: int, count: int) -> tuple[int, list[str]]:
    """한 asyncio 태스크가 자기 문맥의 수집기에 count 개 기록을 남기고 스냅샷을 읽는다.

    각 기록의 filters 에 "_task" 태그로 자기 task_id 를 심어, 스냅샷에 다른
    태스크의 기록이 섞였는지 검사할 수 있게 한다.
    """
    collector = current_collector()
    collector.reset()
    # 다른 태스크에 스케줄링을 양보해 동시 실행 상황을 실제로 만든다.
    await asyncio.sleep(0)
    expected_order: list[str] = []
    for seq in range(count):
        marker = f"t{task_id}-r{seq}"
        collector.record(
            ToolQueryRecord(
                table="book",
                node_class="Book",
                filters={"_task": f"t{task_id}", "_marker": marker},
                steps=None,
                total=seq,
                shown_rows=[],
            )
        )
        expected_order.append(marker)
        await asyncio.sleep(0)
    snapshot = collector.snapshot()
    markers = [r.filters["_marker"] for r in snapshot]
    tags = {_tag(r) for r in snapshot}
    # 격리: 스냅샷에는 오직 자기 태그만 있어야 한다(다른 태스크 기록 유입 없음).
    # count==0 이면 스냅샷이 비어 tags 도 공집합이며, 이 역시 격리를 만족한다.
    assert tags <= {f"t{task_id}"}, f"격리 위반: {tags}"
    assert markers == expected_order
    return task_id, markers


async def _run_concurrent(counts: list[int]) -> None:
    async def wrapper(idx: int, cnt: int):
        # 각 태스크를 독립 문맥(copy_context)에서 돌려 ContextVar 격리를 보장한다.
        return await _task_body(idx, cnt)

    results = await asyncio.gather(
        *(wrapper(i, c) for i, c in enumerate(counts))
    )
    for task_id, markers in results:
        # 각 태스크의 스냅샷은 오직 자기 마커만 담아야 한다.
        assert all(m.startswith(f"t{task_id}-") for m in markers)


# Feature: answer-trace-panel, Property 2
@settings(max_examples=100, deadline=None)
@given(st.lists(st.integers(min_value=0, max_value=5), min_size=2, max_size=6))
def test_property_2_concurrent_isolation(counts: list[int]) -> None:
    """Property 2: 동시 asyncio 태스크 각각의 스냅샷은 자기 기록만 포함한다.

    Validates: Requirements 2.2
    """
    asyncio.run(_run_concurrent(counts))


# Feature: answer-trace-panel, Property 3
@settings(max_examples=100)
@given(records_strategy(min_size=0, max_size=8))
def test_property_3_snapshot_preserves_order(records: list[ToolQueryRecord]) -> None:
    """Property 3: snapshot() 은 기록 순서와 동일한 순서로 같은 항목을 반환한다.

    Validates: Requirements 2.3
    """

    async def body() -> list[ToolQueryRecord]:
        collector = current_collector()
        collector.reset()
        for rec in records:
            collector.record(rec)
        return collector.snapshot()

    snapshot = asyncio.run(body())
    # 동일 객체가 기록 순서 그대로 담겨 있어야 한다.
    assert snapshot == records
    assert [id(r) for r in snapshot] == [id(r) for r in records]
