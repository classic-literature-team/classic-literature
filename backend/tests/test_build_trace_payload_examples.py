"""Task 2.2 — build_trace_payload 단위/예제 테스트.

design.md 의 JSON 스키마 예시(작품→이본→외평)에 부합하는 예제로 병합 동작,
경로 재구성, 빈 입력→None, evidence 문장 형식을 검증한다. DB 접속 없이 순수 함수만 사용.
"""

from __future__ import annotations

from app.agents.trace import ToolQueryRecord, build_trace_payload


def test_empty_records_returns_none() -> None:
    """빈 입력이면 None 을 반환한다(Requirement 3.9)."""
    assert build_trace_payload([]) is None


def test_single_record_all_shown_evidence_format() -> None:
    """전체 건수와 표시 건수가 같으면 evidence 는 'N건 확인' 형식이다(3.8)."""
    rec = ToolQueryRecord(
        table="abstract_work",
        node_class="AbstractWork",
        filters={"work_kor": "운영전"},
        steps=None,
        total=2,
        shown_rows=[
            {"id": "aw_1", "work_kor": "운영전"},
            {"id": "aw_2", "work_kor": "상사동전객기"},
        ],
        relations=["spreadsInto"],
    )
    payload = build_trace_payload([rec])
    assert payload is not None
    assert payload["evidence"] == ["작품(AbstractWork) 2건 확인"]
    assert payload["classes"] == [
        {"key": "abstract_work", "node_class": "AbstractWork", "label": "작품"}
    ]
    assert payload["relations"] == [
        {"name": "spreadsInto", "korean": "이본으로 확산된다"}
    ]
    # 경로 부재 → 클래스 label 나열.
    assert payload["path"] == ["작품"]
    group = payload["records"][0]
    assert group["total"] == 2
    assert group["shown"] == 2
    assert group["columns"] == ["id", "work_kor"]


def test_single_record_partial_shown_evidence_format() -> None:
    """전체 건수 > 표시 건수면 evidence 는 'N건 중 M건 확인' 형식이다(3.8)."""
    rec = ToolQueryRecord(
        table="book",
        node_class="Book",
        filters={},
        steps=None,
        total=142,
        shown_rows=[{"id": f"book_{i}"} for i in range(30)],
        relations=[],
    )
    payload = build_trace_payload([rec])
    assert payload is not None
    assert payload["evidence"] == ["이본(Book) 142건 중 30건 확인"]
    assert payload["records"][0]["shown"] == 30
    assert payload["records"][0]["total"] == 142


def test_multi_record_merge_matches_design_schema() -> None:
    """작품→이본→외평 다중 호출 병합이 design.md 스키마와 부합한다(3.1~3.8)."""
    r_work = ToolQueryRecord(
        table="abstract_work",
        node_class="AbstractWork",
        filters={},
        steps=None,
        total=2,
        shown_rows=[
            {"id": "aw_1", "work_kor": "운영전"},
            {"id": "aw_2", "work_kor": "상사동전객기"},
        ],
        relations=["spreadsInto"],
    )
    r_book = ToolQueryRecord(
        table="book",
        node_class="Book",
        filters={},
        steps=None,
        total=142,
        shown_rows=[
            {
                "id": "book_1",
                "title_name_kor": "운영전",
                "institution_kor": "장서각",
            }
        ],
        relations=["contains"],
    )
    r_review = ToolQueryRecord(
        table="review",
        node_class="Review",
        filters={},
        steps=None,
        total=46,
        shown_rows=[{"id": "rv_1", "criticism_type": "Foreword"}],
        relations=["contains"],
    )
    payload = build_trace_payload([r_work, r_book, r_review])
    assert payload is not None

    # classes: 첫 등장 순서 유지.
    assert [c["node_class"] for c in payload["classes"]] == [
        "AbstractWork",
        "Book",
        "Review",
    ]
    assert [c["label"] for c in payload["classes"]] == ["작품", "이본", "외평"]

    # relations: 첫 등장 순서 유지·중복 제거(spreadsInto, contains).
    assert payload["relations"] == [
        {"name": "spreadsInto", "korean": "이본으로 확산된다"},
        {"name": "contains", "korean": "보유한다"},
    ]

    # evidence: 클래스별 문장.
    assert payload["evidence"] == [
        "작품(AbstractWork) 2건 확인",
        "이본(Book) 142건 중 1건 확인",
        "외평(Review) 46건 중 1건 확인",
    ]

    # path: 경로 부재 → 클래스 label 나열.
    assert payload["path"] == ["작품", "이본", "외평"]


def test_multi_record_same_class_dedup_and_max_total() -> None:
    """같은 클래스를 여러 번 조회하면 id 중복 제거 + total 최댓값(3.3, 3.4)."""
    r1 = ToolQueryRecord(
        table="book",
        node_class="Book",
        filters={},
        steps=None,
        total=100,
        shown_rows=[{"id": "b1", "title_name_kor": "가"}, {"id": "b2"}],
        relations=[],
    )
    r2 = ToolQueryRecord(
        table="book",
        node_class="Book",
        filters={},
        steps=None,
        total=142,
        shown_rows=[{"id": "b2"}, {"id": "b3", "institution_kor": "장서각"}],
        relations=[],
    )
    payload = build_trace_payload([r1, r2])
    assert payload is not None
    group = payload["records"][0]
    ids = [row["id"] for row in group["rows"]]
    assert ids == ["b1", "b2", "b3"]  # b2 중복 제거, 등장 순서 유지
    assert group["total"] == 142  # 최댓값
    # columns 등장 순서 유지 합집합.
    assert group["columns"] == ["id", "title_name_kor", "institution_kor"]


def test_path_reconstruction_from_segments() -> None:
    """경로 탐색 단계가 있으면 path 는 병합된 경로 라벨 목록이다(3.6)."""
    rec = ToolQueryRecord(
        table="abstract_work",
        node_class="AbstractWork",
        filters={},
        steps=["spreadsInto:book", "contains:review"],
        total=1,
        shown_rows=[],
        relations=["spreadsInto", "contains"],
        path_segments=[
            "AbstractWork: 운영전 -[spreadsInto/확산]→ Book: 운영전",
        ],
    )
    payload = build_trace_payload([rec])
    assert payload is not None
    assert payload["path"] == [
        "AbstractWork: 운영전 -[spreadsInto/확산]→ Book: 운영전",
    ]
