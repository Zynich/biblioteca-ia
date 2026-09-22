"""Endpoints de cadastro e consulta de livros (Questão 1)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_book_service
from app.schemas.book import BookCreate, BookList, BookRead
from app.services.book_service import BookNotFoundError, BookService

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo livro",
    description="Cria um livro com título, autor, data de publicação e resumo.",
)
def create_book(
    payload: BookCreate,
    service: BookService = Depends(get_book_service),
) -> BookRead:
    book = service.create_book(payload)
    return BookRead.model_validate(book)


@router.get(
    "",
    response_model=BookList,
    summary="Consulta livros por título e/ou autor",
    description=(
        "Busca parcial e case-insensitive. Quando `title` e `author` são informados "
        "juntos, retorna livros que casam com qualquer um dos dois (OR). Sem filtros, "
        "lista todos os livros paginados."
    ),
)
def search_books(
    title: str | None = Query(None, description="Filtro parcial por título"),
    author: str | None = Query(None, description="Filtro parcial por autor"),
    limit: int = Query(20, ge=1, le=100, description="Quantidade máxima de itens por página"),
    offset: int = Query(0, ge=0, description="Quantidade de itens a pular (paginação)"),
    service: BookService = Depends(get_book_service),
) -> BookList:
    items, total = service.search_books(title, author, limit, offset)
    return BookList(
        items=[BookRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Detalhe de um livro",
    responses={404: {"description": "Livro não encontrado"}},
)
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
) -> BookRead:
    try:
        book = service.get_book(book_id)
    except BookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BookRead.model_validate(book)
