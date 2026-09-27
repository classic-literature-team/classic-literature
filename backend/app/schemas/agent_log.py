from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentLogOut(BaseModel):
    """AI 채팅 로그 한 건의 응답 표현."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    created_at: datetime
    like_count: int
