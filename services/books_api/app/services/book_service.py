"""Regra de negócio da Questão 1. Hoje é fina (a maior parte da validação já acontece
no schema Pydantic), mas isolar essa camada evita que regras futuras (ex.: checar
duplicidade, disparar evento de "livro cadastrado") acabem espalhadas pela rota."""

from app.models.book import Book
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate

MAX_PAGE_SIZE = 100


class BookNotFoundError(Exception):
    def __init__(self, book_id: int) -> None:
        self.book_id = book_id
        super().__init__(f"Livro {book_id} não encontrado")


class BookService:
    def __init__(self, repository: BookRepository) -> None:
        self.repository = repository

    def create_book(self, data: BookCreate) -> Book:
        return self.repository.create(data)

    def get_book(self, book_id: int) -> Book:
        book = self.repository.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError(book_id)
        return book

    def search_books(
        self,
        title: str | None,
        author: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Book], int]:
        # Nunca confia cegamente no limit vindo da rota: protege o banco de uma
        # página gigante mesmo que a validação do schema seja contornada.
        safe_limit = min(max(limit, 1), MAX_PAGE_SIZE)
        safe_offset = max(offset, 0)
        return self.repository.search(title, author, safe_limit, safe_offset)
