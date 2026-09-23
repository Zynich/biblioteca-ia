"""Busca semântica ponta a ponta: modelo real + os 24 artigos de exemplo."""

import os
from pathlib import Path

import pytest

from app.documents import Article
from app.embeddings import TextEmbedder, TransformersEmbedder
from app.indexing import build_index
from app.search import IndexNotReadyError, SemanticSearchService


@pytest.mark.parametrize(
    ("query", "expected_doc"),
    [
        ("como fazer bolo", "culinaria-01"),
        ("como criar uma lista em python", "python-01"),
        ("onde investir meu dinheiro com segurança", "financas-02"),
        ("dicas para correr mais rápido", "esportes-01"),
        ("dormir melhor", "saude-01"),
        ("o que visitar em Portugal", "viagem-01"),
        ("how to bake a cake", "culinaria-01"),
    ],
)
def test_top1_result_is_the_relevant_article(
    built_service: SemanticSearchService, query: str, expected_doc: str
) -> None:
    results = built_service.search(query, k=3)

    assert results[0].doc_id == expected_doc


def test_results_are_distinct_documents_sorted_by_score(
    built_service: SemanticSearchService,
) -> None:
    results = built_service.search("receita de comida", k=5)

    ids = [r.doc_id for r in results]
    assert len(ids) == len(set(ids)) == 5
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_k_limits_number_of_results(built_service: SemanticSearchService) -> None:
    assert len(built_service.search("python", k=2)) == 2


def test_persisted_index_gives_same_results_after_reload(
    built_service: SemanticSearchService, embedder: TransformersEmbedder
) -> None:
    before = built_service.search("como fazer bolo", k=3)

    # Novo serviço, sem estado em memória: só o que está em disco.
    reloaded = SemanticSearchService(
        embedder, built_service.index_path, built_service.metadata_path
    )
    after = reloaded.search("como fazer bolo", k=3)

    assert [r.doc_id for r in after] == [r.doc_id for r in before]
    assert [r.score for r in after] == pytest.approx([r.score for r in before], abs=0.01)


def test_search_without_index_raises(tmp_path: Path, fake_embedder: TextEmbedder) -> None:
    service = SemanticSearchService(fake_embedder, tmp_path / "x.faiss", tmp_path / "x.json")

    assert not service.is_ready()
    with pytest.raises(IndexNotReadyError):
        service.search("qualquer coisa")


def test_service_picks_up_index_rebuilt_by_another_process(
    tmp_path: Path, fake_embedder: TextEmbedder
) -> None:
    index_path, metadata_path = tmp_path / "i.faiss", tmp_path / "m.json"
    first = [Article("a", "Primeiro", "conteúdo do primeiro artigo")]
    second = [Article("b", "Segundo", "conteúdo do segundo artigo")]
    build_index(first, fake_embedder, index_path, metadata_path)
    service = SemanticSearchService(fake_embedder, index_path, metadata_path)
    assert [r.doc_id for r in service.search("x", k=5)] == ["a"]

    # Simula `make ingest` rodando em outro container e regravando o índice no volume.
    build_index(second, fake_embedder, index_path, metadata_path)
    stat = index_path.stat()
    os.utime(index_path, (stat.st_atime, stat.st_mtime + 5))

    assert [r.doc_id for r in service.search("x", k=5)] == ["b"]
