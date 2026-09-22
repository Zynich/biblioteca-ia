"""Camada de acesso a dados: só sabe falar SQLAlchemy, não conhece regra de negócio
nem HTTP. Isso permite testar a lógica de negócio (services/) com um repository fake,
e testar este repository isoladamente com um banco em memória."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.schemas.book import BookCreate


class BookRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: BookCreate) -> Book:
        book = Book(**data.model_dump())
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def get_by_id(self, book_id: int) -> Book | None:
        return self.db.get(Book, book_id)

    def search(
        self,
        title: str | None = None,
        author: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Book], int]:
        """Busca parcial e case-insensitive por título e/ou autor, paginada.

        Quando nenhum filtro é informado, lista todos os livros (também paginado).
        """
        stmt = select(Book)
        filters = []
        if title:
            filters.append(Book.title.ilike(f"%{title}%"))
        if author:
            filters.append(Book.author.ilike(f"%{author}%"))
        if filters:
            # Ambos os filtros, quando presentes juntos, casam por OR: permite buscar
            # "algo que bate com título OU autor" em uma única query de busca livre.
            stmt = stmt.where(or_(*filters))

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        stmt = stmt.order_by(Book.title).limit(limit).offset(offset)
        items = list(self.db.scalars(stmt).all())
        return items, total
