from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.agents.literature_agent import run_literature_agent
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY가 설정되지 않았습니다.",
        )

    reply = await run_literature_agent(payload.message)
    return ChatResponse(reply=reply)
