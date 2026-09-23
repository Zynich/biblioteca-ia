"""Endpoint de busca semântica — Questão 3."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import get_search_service
from app.search import IndexNotReadyError, SemanticSearchService

router = APIRouter(prefix="/api/v1", tags=["search"])


class SearchResultRead(BaseModel):
    doc_id: str
    title: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultRead]


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Busca semântica de documentos",
    description=(
        "Gera o embedding da consulta e retorna os `k` documentos mais similares "
        "(similaridade de cosseno, de -1 a 1; quanto maior, mais relevante)."
    ),
    responses={503: {"description": "Índice ainda não foi gerado (execute a ingestão)"}},
)
def search(
    q: str = Query(
        ..., min_length=1, max_length=500, pattern=r"\S", description="Texto da consulta"
    ),
    k: int = Query(5, ge=1, le=20, description="Quantidade de documentos a retornar"),
    service: SemanticSearchService = Depends(get_search_service),
) -> SearchResponse:
    query = q.strip()
    try:
        results = service.search(query, k)
    except IndexNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return SearchResponse(
        query=query,
        results=[
            SearchResultRead(doc_id=r.doc_id, title=r.title, score=r.score, snippet=r.snippet)
            for r in results
        ],
    )
