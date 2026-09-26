"""테스트 공용 헬퍼: ToolQueryRecord 생성용 hypothesis 전략과 목(mock) row.

trace/도구 계측 property 테스트가 공유하는 데이터 생성기를 한곳에 모은다.
node_class 는 CLASS_TO_KEY 의 유효 클래스명에서만 뽑고, table 은 그에 대응하는
키(CLASS_TO_KEY[node_class])로 맞춰 유효 데이터를 생성한다.
"""

from __future__ import annotations

from hypothesis import strategies as st

from app.agents.tools import CLASS_TO_KEY, LONG_COLS, RELATION_KOR
from app.agents.trace import ToolQueryRecord

# 유효 클래스명 목록(Edge 표기). table 은 이 값에 대응하는 키로 둔다.
VALID_CLASSES = sorted(CLASS_TO_KEY.keys())
# 유효 관계명 목록(RELATION_KOR 키). 병기 검증에 재사용한다.
VALID_RELATIONS = sorted(RELATION_KOR.keys())
# 장문 컬럼 목록(축약 규칙 검증에 재사용).
LONG_COLUMNS = sorted(LONG_COLS)

# 일반 컬럼명(장문 아닌 컬럼) 표본. 실제 스키마 컬럼명 중 대표값.
PLAIN_COLUMNS = [
    "id",
    "name",
    "title_name_kor",
    "institution_kor",
    "work_kor",
    "criticism_type",
]


@st.composite
def rows_strategy(draw, *, with_id: bool = True):
    """레코드 행(컬럼→값 문자열 dict) 목록 전략.

    with_id=True 면 각 행에 "id" 키를 포함시킨다(id 기준 중복 제거 검증용).
    값은 항상 비어있지 않은 문자열로 둔다(직렬화 후 dict 규칙과 일치).
    """
    n = draw(st.integers(min_value=0, max_value=4))
    rows: list[dict[str, str]] = []
    for i in range(n):
        row: dict[str, str] = {}
        if with_id:
            # id 는 소수의 값 풀에서 뽑아 중복이 발생하도록 유도한다.
            row["id"] = draw(st.sampled_from(["a", "b", "c", "d", f"row{i}"]))
        cols = draw(
            st.lists(
                st.sampled_from([c for c in PLAIN_COLUMNS if c != "id"]),
                min_size=0,
                max_size=3,
                unique=True,
            )
        )
        for col in cols:
            # 값 후보를 작은 풀에서 뽑아 생성 비용을 낮춘다(비어있지 않은 문자열).
            row[col] = draw(st.sampled_from(["x", "가", "v1", "운영전", "0"]))
        rows.append(row)
    return rows


@st.composite
def record_strategy(draw, *, single_only: bool = False):
    """ToolQueryRecord 하나를 생성하는 전략.

    single_only=True 면 path_segments 를 항상 비워 단일 조회 기록만 만든다
    (경로 부재 property 검증용).
    """
    node_class = draw(st.sampled_from(VALID_CLASSES))
    table = CLASS_TO_KEY[node_class]
    total = draw(st.integers(min_value=0, max_value=500))
    rows = draw(rows_strategy())
    relations = draw(
        st.lists(st.sampled_from(VALID_RELATIONS), min_size=0, max_size=4)
    )
    if single_only:
        steps = None
        path_segments: list[str] = []
    else:
        make_path = draw(st.booleans())
        if make_path:
            seg_pool = ["작품→이본", "이본→외평", "Book: 운영전", "-[contains]→ Scene"]
            path_segments = draw(
                st.lists(st.sampled_from(seg_pool), min_size=1, max_size=3)
            )
            steps = draw(
                st.lists(
                    st.sampled_from(["contains:book", "spreadsInto:book"]),
                    min_size=1,
                    max_size=3,
                )
            )
        else:
            path_segments = []
            steps = None
    return ToolQueryRecord(
        table=table,
        node_class=node_class,
        filters={},
        steps=steps,
        total=total,
        shown_rows=rows,
        relations=relations,
        path_segments=path_segments,
    )


def records_strategy(
    *, single_only: bool = False, min_size: int = 1, max_size: int = 6
):
    """ToolQueryRecord 목록 전략."""
    return st.lists(
        record_strategy(single_only=single_only),
        min_size=min_size,
        max_size=max_size,
    )


class _MockColumn:
    """SQLAlchemy Column 의 ``.name`` 만 흉내내는 최소 목."""

    def __init__(self, name: str) -> None:
        self.name = name


class _MockTable:
    """``__table__.columns`` 순회를 흉내내는 최소 목."""

    def __init__(self, column_names: list[str]) -> None:
        self.columns = [_MockColumn(n) for n in column_names]


class MockRow:
    """``_serialize_row`` 가 기대하는 인터페이스(``__table__.columns`` + getattr)만
    제공하는 목 row.

    values 는 {컬럼명: 값} 매핑이며, 컬럼 순서는 삽입 순서를 따른다. 값은 임의
    타입일 수 있고(None 포함) _serialize_row 규칙대로 걸러진다.
    """

    def __init__(self, values: dict[str, object]) -> None:
        self._values = values
        self.__table__ = _MockTable(list(values.keys()))
        for name, value in values.items():
            setattr(self, name, value)
