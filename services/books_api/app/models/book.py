"""Modelo SQLAlchemy da tabela `books`."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class Book(Base):
    __tablename__ = "books"
    # Índices em title/author: são os dois campos usados na busca (GET /books),
    # e a busca é feita com frequência muito maior que a escrita.
    __table_args__ = (
        Index("ix_books_title", "title"),
        Index("ix_books_author", "author"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    published_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
