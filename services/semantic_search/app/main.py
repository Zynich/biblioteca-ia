"""Ponto de entrada da busca semântica (Questão 3)."""

from fastapi import FastAPI

from app.api.routes import health, search

app = FastAPI(
    title="Busca Semântica",
    description="Busca semântica de documentos com embeddings + FAISS — Questão 3.",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(search.router)
