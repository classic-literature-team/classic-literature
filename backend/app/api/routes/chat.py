import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.literature_agent import (
    run_literature_agent,
    stream_literature_agent,
)
from app.agents.trace import build_trace_payload, current_collector
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


@router.post("/stream")
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    """답변을 SSE(Server-Sent Events)로 스트리밍한다.

    에이전트가 토큰을 생성하는 대로 `data: {\"delta\": ...}` 이벤트를
    흘려보내고, 마지막에 `data: {\"done\": true}`로 종료를 알린다.
    오류가 나면 `data: {\"error\": ...}`를 보낸다. 프론트는 이 조각들을
    순서대로 이어 붙여 답변을 완성한다.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY가 설정되지 않았습니다.",
        )

    async def event_source() -> AsyncIterator[str]:
        # Req 2.1: 새 스트리밍 요청 시작 시 현재 요청의 수집기를 비운다.
        collector = current_collector()
        collector.reset()
        try:
            async for delta in stream_literature_agent(payload.message):
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        except Exception as err:  # noqa: BLE001
            # Req 4.3: 예외 시 error 이벤트만 방출하고 trace는 보내지 않는다.
            yield f"data: {json.dumps({'error': str(err)}, ensure_ascii=False)}\n\n"
        else:
            # Req 4.1/4.2: 델타가 정상 종료되면 done 직전에 trace를 1회 방출한다.
            # 병합 결과가 None(도구 미사용)이면 trace를 생략하고 done만 보낸다.
            trace = build_trace_payload(collector.snapshot())
            if trace is not None:
                yield f"data: {json.dumps({'trace': trace}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
