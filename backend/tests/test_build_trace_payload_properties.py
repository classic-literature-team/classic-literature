"""Task 2.3 / 2.4 / 2.5 — build_trace_payload 병합 불변식 property 테스트.

Property 4, 5 (합집합 순서·중복 제거), Property 6, 7, 8 (레코드 병합 불변식),
Property 9, 10 (경로 부재·evidence 대응)을 검증한다. DB 접속 없이 순수 함수만 사용.
"""

from __future__ import annotations

from hypothesis import given, settings

from app.agents.trace import CLASS_LABEL_KOR, ToolQueryRecord, build_trace_payload
from tests._helpers import records_strategy


def _first_seen(seq: list[str]) -> list[str]:
    """등장 순서를 유지하며 중복을 제거한 목록."""
    out: list[str] = []
    for item in seq:
        if item not in out:
            out.append(item)
    return out


# --- Task 2.3: Property 4, 5 -------------------------------------------------


# Feature: answer-trace-panel, Property 4
@settings(max_examples=100)
@given(records_strategy())
def test_property_4_classes_ordered_union(records: list[ToolQueryRecord]) -> None:
    """Property 4: classes 는 등장 클래스의 첫 등장 순서 유지·중복 제거 합집합.

    Validates: Requirements 3.1
    """
    payload = build_trace_payload(records)
    assert payload is not None
    got = [c["node_class"] for c in payload["classes"]]
    expected = _first_seen([r.node_class for r in records])
    assert got == expected
    # 중복 없음.
    assert len(got) == len(set(got))


# Feature: answer-trace-panel, Property 5
@settings(max_examples=100)
@given(records_strategy())
def test_property_5_relations_ordered_union(records: list[ToolQueryRecord]) -> None:
    """Property 5: relations 는 등장 관계명의 첫 등장 순서 유지·중복 제거 합집합.

    Validates: Requirements 3.2
    """
    payload = build_trace_payload(records)
    assert payload is not None
    got = [r["name"] for r in payload["relations"]]
    flat: list[str] = []
    for rec in records:
        flat.extend(rec.relations)
    expected = _first_seen(flat)
    assert got == expected
    assert len(got) == len(set(got))


# --- Task 2.4: Property 6, 7, 8 ---------------------------------------------


# Feature: answer-trace-panel, Property 6
@settings(max_examples=100)
@given(records_strategy())
def test_property_6_row_ids_unique(records: list[ToolQueryRecord]) -> None:
    """Property 6: 각 Trace_Record_Group 의 rows 에서 id 값은 유일하다.

    Validates: Requirements 3.3
    """
    payload = build_trace_payload(records)
    assert payload is not None
    for group in payload["records"]:
        ids = [row["id"] for row in group["rows"] if "id" in row]
        assert len(ids) == len(set(ids))


# Feature: answer-trace-panel, Property 7
@settings(max_examples=100)
@given(records_strategy())
def test_property_7_total_is_max(records: list[ToolQueryRecord]) -> None:
    """Property 7: 클래스별 total 은 그 클래스 조회들의 total 최댓값이다.

    Validates: Requirements 3.4
    """
    payload = build_trace_payload(records)
    assert payload is not None
    expected_max: dict[str, int] = {}
    for rec in records:
        prev = expected_max.get(rec.node_class)
        if prev is None:
            expected_max[rec.node_class] = rec.total
        else:
            expected_max[rec.node_class] = max(prev, rec.total)
    for group in payload["records"]:
        assert group["total"] == expected_max[group["node_class"]]


# Feature: answer-trace-panel, Property 8
@settings(max_examples=100)
@given(records_strategy())
def test_property_8_columns_union_and_row_keys_subset(
    records: list[ToolQueryRecord],
) -> None:
    """Property 8: columns 는 등장 순서 유지 합집합, 각 row 키는 columns 의 부분집합.

    Validates: Requirements 3.5
    """
    payload = build_trace_payload(records)
    assert payload is not None

    # 기대 columns 는 id 중복 제거를 거쳐 살아남은 rows 기준의 등장 순서 합집합이다.
    # builder 는 id 로 dedup 한 뒤 남은 행의 컬럼만 columns 에 넣는다. 아래에서 그
    # dedup 규칙(id 있으면 id 기준, 없으면 완전 동일 dict 기준)을 그대로 재현한다.
    expected_columns: dict[str, list[str]] = {}
    seen_ids: dict[str, set] = {}
    seen_sig: dict[str, set] = {}
    for rec in records:
        seq = expected_columns.setdefault(rec.node_class, [])
        ids = seen_ids.setdefault(rec.node_class, set())
        sigs = seen_sig.setdefault(rec.node_class, set())
        for row in rec.shown_rows:
            row_id = row.get("id")
            if row_id is not None:
                if row_id in ids:
                    continue
                ids.add(row_id)
            else:
                signature = tuple(sorted(row.items()))
                if signature in sigs:
                    continue
                sigs.add(signature)
            for col in row.keys():
                if col not in seq:
                    seq.append(col)

    for group in payload["records"]:
        node_class = group["node_class"]
        columns = group["columns"]
        assert columns == expected_columns[node_class]
        # 병합 후 각 row 의 키는 columns 의 부분집합이다.
        cols_set = set(columns)
        for row in group["rows"]:
            assert set(row.keys()) <= cols_set
        # shown == rows 길이.
        assert group["shown"] == len(group["rows"])


# --- Task 2.5: Property 9, 10 -----------------------------------------------


# Feature: answer-trace-panel, Property 9
@settings(max_examples=100)
@given(records_strategy(single_only=True))
def test_property_9_path_falls_back_to_class_labels(
    records: list[ToolQueryRecord],
) -> None:
    """Property 9: 경로 단계가 없으면 path 는 병합 classes 의 한국어 label 나열.

    Validates: Requirements 3.7
    """
    payload = build_trace_payload(records)
    assert payload is not None
    expected = [c["label"] for c in payload["classes"]]
    assert payload["path"] == expected
    # label 은 매핑표를 따른다.
    for c in payload["classes"]:
        assert c["label"] == CLASS_LABEL_KOR[c["node_class"]]


# Feature: answer-trace-panel, Property 10
@settings(max_examples=100)
@given(records_strategy())
def test_property_10_evidence_per_class(records: list[ToolQueryRecord]) -> None:
    """Property 10: 각 클래스마다 대응하는 조회 건수 요약 문장이 evidence 에 존재.

    Validates: Requirements 3.8
    """
    payload = build_trace_payload(records)
    assert payload is not None
    evidence = payload["evidence"]
    # evidence 개수는 클래스 개수와 같다.
    assert len(evidence) == len(payload["classes"])
    for group in payload["records"]:
        label = group["label"]
        node_class = group["node_class"]
        total = group["total"]
        shown = group["shown"]
        if total == shown:
            sentence = f"{label}({node_class}) {total}건 확인"
        else:
            sentence = f"{label}({node_class}) {total}건 중 {shown}건 확인"
        assert sentence in evidence
