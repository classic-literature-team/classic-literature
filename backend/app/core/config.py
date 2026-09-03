from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정. .env 파일과 환경변수에서 로드된다."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 앱
    app_name: str = "Classic Literature API"
    debug: bool = False
    api_prefix: str = "/api"

    # 데이터베이스
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/classic_literature",
        description="SQLAlchemy 데이터베이스 URL",
    )

    # CORS (콤마로 구분된 origin 목록)
    cors_origins: str = "http://localhost:5173"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
