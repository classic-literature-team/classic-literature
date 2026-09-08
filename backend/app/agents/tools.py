"""에이전트가 사용하는 tool calling 함수 모음.

각 함수는 @function_tool 데코레이터로 감싸며, docstring이 LLM에게
"이 툴을 언제/어떻게 쓸지" 알려주는 설명서 역할을 한다.
"""

from agents import function_tool
from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models import Review


@function_tool
def search_reviews_by_work(work_names: list[str]) -> str:
    """작품명(국문)으로 외평(Review)을 조회한다.

    외평은 이본에 남아 있는 당시 문인들의 독서 흔적(감상·해석·논평,
    서발·독법·범례·부기 등)이다. 사용자가 특정 작품에 대한 문인들의
    반응·독서 흔적·비평을 알고 싶어할 때 사용한다.

    Args:
        work_names: 조회할 작품명(국문) 목록. 예: ["상사동전객기", "운영전"].
            work_kor 컬럼에 해당 문자열이 포함된 외평을 찾는다.

    Returns:
       찾은 외평들을 사람이 읽기 좋은 텍스트로 정리해 반환한다
    """

    if not work_names:
        return "조회할 작품명이 지정되지 않았습니다."

    with SessionLocal() as db:
        # work_kor 에 작품명 중 하나라도 포함되면 매칭 (부분 일치)
        conditions = [Review.work_kor.ilike(f"%{name}%") for name in work_names]
        stmt = select(Review).where(or_(*conditions)).order_by(Review.work_kor)
        reviews = list(db.scalars(stmt))

    if not reviews:
        joined = ", ".join(work_names)
        return f"'{joined}'에 해당하는 외평(독서 흔적)을 찾지 못했습니다."

    lines: list[str] = [f"총 {len(reviews)}건의 외평을 찾았습니다.\n"]
    for i, r in enumerate(reviews, start=1):
        parts = [f"[{i}] 작품: {r.work_kor or '?'}"]
        if r.reviewer:
            parts.append(f"문인(비평자): {r.reviewer}")
        if r.criticism_type:
            parts.append(f"비평 유형: {r.criticism_type}")
        if r.paratext_title:
            parts.append(f"제목: {r.paratext_title}")
        if r.target_book:
            parts.append(f"수록 이본: {r.target_book}")
        if r.location:
            parts.append(f"위치: {r.location}")
        if r.original_text:
            parts.append(f"원문: {r.original_text}")
        if r.translation:
            parts.append(f"번역: {r.translation}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)
