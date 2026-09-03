from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성: 요청 단위 DB 세션을 제공하고 종료 시 닫는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
