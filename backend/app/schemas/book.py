from pydantic import BaseModel, ConfigDict


class BookBase(BaseModel):
    title: str
    author: str
    year: int | None = None


class BookCreate(BookBase):
    pass


class BookRead(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
