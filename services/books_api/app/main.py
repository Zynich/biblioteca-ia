"""Ponto de entrada da API de biblioteca virtual (Questão 1)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import books, health
from app.db.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Sem Alembic rodando automaticamente aqui: `create_all` é suficiente para o
    # escopo do teste. As migrations (alembic/) documentam o schema para evolução
    # futura, mas não são aplicadas no startup para não mascarar migrations pendentes.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Biblioteca Virtual API",
    description="Cadastro e consulta de livros — Questão 1 do teste técnico.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(books.router)
