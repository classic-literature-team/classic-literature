from pydantic import BaseModel, ConfigDict


class BookRead(BaseModel):
    """book 테이블 조회용 스키마 (주요 필드만)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None = None
    designation: str | None = None
    title_name_kor: str | None = None
    title_name_chi: str | None = None
    institution_kor: str | None = None
    date_statement: str | None = None
