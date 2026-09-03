from agents import Agent, Runner, function_tool

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.book import Book


@function_tool
def search_books(query: str) -> str:
    """제목이나 저자에 검색어가 포함된 책을 DB에서 찾아 목록을 반환한다.

    Args:
        query: 제목 또는 저자에 대한 검색어.
    """
    with SessionLocal() as db:
        books = db.query(Book).all()
        matched = [
            b
            for b in books
            if query.lower() in b.title.lower() or query.lower() in b.author.lower()
        ]

    if not matched:
        return f"'{query}'에 해당하는 책을 찾지 못했습니다."

    lines = [f"- {b.title} ({b.author}, {b.year or '연도 미상'})" for b in matched]
    return "\n".join(lines)


def build_literature_agent() -> Agent:
    """고전 문학 안내용 에이전트를 생성한다. search_books 툴을 호출할 수 있다."""
    return Agent(
        name="Literature Guide",
        instructions=(
            "당신은 고전 문학 안내자입니다. 사용자의 질문에 친절하고 간결하게 "
            "답하세요. 특정 책이나 저자를 찾아야 할 때는 search_books 툴을 사용하세요."
        ),
        model=settings.openai_model,
        tools=[search_books],
    )


async def run_literature_agent(message: str) -> str:
    """에이전트를 한 턴 실행하고 최종 출력을 반환한다."""
    agent = build_literature_agent()
    result = await Runner.run(agent, message)
    return result.final_output


__all__ = ["build_literature_agent", "run_literature_agent", "search_books"]
