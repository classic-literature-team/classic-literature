"""Task 3.3 — 행 직렬화 무결성 property 테스트.

_serialize_row 는 실제 SQLAlchemy row 를 받으므로, __table__.columns 인터페이스만
흉내내는 MockRow 로 검증한다. DB 접속 없이 순수하게 직렬화 규칙만 확인한다.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from app.agents.tools import _serialize_row
from tests._helpers import LONG_COLUMNS, PLAIN_COLUMNS, MockRow

# 값 후보: 비어있지 않은 문자열, 공백/빈 문자열, None, 숫자.
_VALUES = st.one_of(
    st.text(min_size=0, max_size=200),
    st.none(),
    st.integers(),
    st.just("   "),
    st.just(""),
)

_ALL_COLUMNS = PLAIN_COLUMNS + LONG_COLUMNS


@st.composite
def _mock_rows(draw):
    names = draw(
        st.lists(st.sampled_from(_ALL_COLUMNS), min_size=0, max_size=6, unique=True)
    )
    values = {name: draw(_VALUES) for name in names}
    return MockRow(values)


# Feature: answer-trace-panel, Property 1
@settings(max_examples=200)
@given(_mock_rows())
def test_property_1_row_serialization_integrity(row: MockRow) -> None:
    """Property 1: 비어있지 않은 컬럼만 포함, 값은 자르지 않고 전문 그대로 담는다.

    Validates: Requirements 1.6
    """
    result = _serialize_row(row)

    # 결과의 모든 값은 문자열이다.
    assert all(isinstance(v, str) for v in result.values())

    for col in row.__table__.columns:
        name = col.name
        raw = getattr(row, name)
        empty = raw is None or str(raw).strip() == ""
        if empty:
            # 비어있는 컬럼은 결과에서 제외되어야 한다.
            assert name not in result
        else:
            # 비어있지 않은 컬럼은 컬럼 종류(장문/일반)와 무관하게
            # 항상 str(raw) 전문이 그대로 담긴다(자르지 않음).
            assert name in result
            assert result[name] == str(raw)

    # 결과에 담긴 키는 모두 실제 컬럼에서 온 것이다(임의 키 유입 없음).
    column_names = {c.name for c in row.__table__.columns}
    assert set(result.keys()) <= column_names


# Feature: answer-trace-panel, Property 1
@settings(max_examples=100)
@given(
    long_col=st.sampled_from(LONG_COLUMNS),
    body=st.text(alphabet="가나다라마바사abc", min_size=121, max_size=400),
)
def test_property_1_long_columns_not_truncated(long_col: str, body: str) -> None:
    """Property 1(집중): 장문 컬럼도 자르지 않고 전문 그대로 유지한다.

    121자 이상의 긴 본문을 넣어도 값이 전문과 동일하며 "…(생략)" 축약이 없다.

    Validates: Requirements 1.6
    """
    row = MockRow({long_col: body})
    result = _serialize_row(row)
    value = result[long_col]
    # 장문 컬럼도 전문을 그대로 담는다(축약 없음).
    assert value == body
    assert not value.endswith("…(생략)")
