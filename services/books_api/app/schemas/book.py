"""Schemas Pydantic de entrada/saída — separados dos modelos SQLAlchemy de propósito,
para que a API nunca exponha (ou aceite) campos internos do banco por acidente."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookCreate(BaseModel):
    """Payload de entrada para cadastro de um livro (POST /books)."""

    title: str = Field(..., min_length=1, max_length=300, description="Título do livro")
    author: str = Field(..., min_length=1, max_length=200, description="Autor do livro")
    published_date: date = Field(..., description="Data de publicação (não pode ser no futuro)")
    summary: str = Field(..., min_length=1, max_length=5000, description="Resumo/sinopse do livro")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Fluent Python",
                "author": "Luciano Ramalho",
                "published_date": "2015-08-20",
                "summary": "Um guia aprofundado sobre recursos idiomáticos da linguagem Python.",
            }
        }
    )

    @field_validator("title", "author", "summary")
    @classmethod
    def not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("não pode ser vazio ou conter apenas espaços")
        return stripped

    @field_validator("published_date")
    @classmethod
    def not_in_the_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("data de publicação não pode ser no futuro")
        return value


class BookRead(BaseModel):
    """Payload de saída — inclui campos gerados pelo banco (id, created_at)."""

    id: int
    title: str
    author: str
    published_date: date
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookList(BaseModel):
    """Envelope paginado retornado por GET /books."""

    items: list[BookRead]
    total: int
    limit: int
    offset: int
