"""Dependencies compartilhadas entre rotas."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.book_repository import BookRepository
from app.services.book_service import BookService


def get_book_service(db: Session = Depends(get_db)) -> Generator[BookService, None, None]:
    yield BookService(BookRepository(db))
