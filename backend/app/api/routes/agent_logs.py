from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AgentLog
from app.schemas.agent_log import AgentLogOut

router = APIRouter(prefix="/agent-logs", tags=["agent-logs"])


@router.get("", response_model=list[AgentLogOut])
def list_agent_logs(
    limit: int = Query(100, ge=1, le=500, description="최대 반환 개수"),
    db: Session = Depends(get_db),
) -> list[AgentLog]:
    """AI 채팅 로그를 최신순(created_at 내림차순)으로 반환한다."""
    stmt = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))
