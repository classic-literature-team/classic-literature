from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from app.agents.tools import search_reviews_by_work
from app.core.config import settings

# OpenAI 호환 엔드포인트(구글 Gemini 등)를 쓰므로,
# OpenAI 전용 트레이싱은 비활성화한다.
set_tracing_disabled(True)


def _build_model() -> OpenAIChatCompletionsModel:
    """설정(.env)의 키/base_url/모델로 LLM 모델을 구성한다.

    Gemini의 OpenAI 호환 엔드포인트를 base_url로 사용하며,
    이 경우 Chat Completions API 방식으로 호출해야 한다.
    """
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )
    return OpenAIChatCompletionsModel(
        model=settings.openai_model,
        openai_client=client,
    )


def build_literature_agent() -> Agent:
    """고전 문학 안내용 에이전트를 생성한다.

    현재 도구:
    - search_reviews_by_work: 작품명으로 외평(문인들의 독서 흔적)을 조회
    """
    return Agent(
        name="Literature Guide",
        instructions=(
            "당신은 한국 고전소설 안내자입니다. 사용자의 질문에 친절하고 정확하게 "
            "한국어로 답하세요.\n"
            "특정 작품에 대한 당시 문인들의 독서 흔적·반응·비평(외평, Review)을 "
            "물으면 search_reviews_by_work 툴을 사용하세요. 여러 작품을 함께 물으면 "
            "작품명들을 한 번에 넘기세요.\n"
            "툴 결과를 바탕으로 어떤 문인이 어떤 흔적을 남겼는지 요약해 설명하고, "
            "원문/번역이 있으면 한자 원문만 제공하세요. 결과가 없으면 없다고 답하세요."
            "답변의 근거가 되는 핵심 속성값들을 중심으로 일목요연한 표를 제공하세요"
        ),
        model=_build_model(),
        tools=[search_reviews_by_work],
    )


async def run_literature_agent(message: str) -> str:
    """에이전트를 한 턴 실행하고 최종 출력을 반환한다."""
    agent = build_literature_agent()
    result = await Runner.run(agent, message)
    return result.final_output


__all__ = ["build_literature_agent", "run_literature_agent"]
