from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book
from app.schemas.book import BookCreate, BookRead

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)) -> list[Book]:
    return list(db.scalars(select(Book).order_by(Book.id)))


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)) -> Book:
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return book
