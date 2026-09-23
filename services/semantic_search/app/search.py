"""Serviço de busca semântica: embedding da consulta -> vector store -> documentos."""

import threading
from dataclasses import dataclass
from pathlib import Path

from app.embeddings import TextEmbedder
from app.vector_store import FaissVectorStore, VectorStore

# Busca mais chunks do que documentos pedidos: vários chunks do mesmo artigo podem
# ocupar o topo, e queremos devolver k documentos distintos.
CHUNK_OVERFETCH = 5


class IndexNotReadyError(Exception):
    def __init__(self) -> None:
        super().__init__("Índice de busca não encontrado. Execute a ingestão (make ingest).")


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    title: str
    score: float
    snippet: str


class SemanticSearchService:
    def __init__(
        self,
        embedder: TextEmbedder,
        index_path: str | Path,
        metadata_path: str | Path,
    ) -> None:
        self.embedder = embedder
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self._store: VectorStore | None = None
        self._loaded_signature: tuple[float, float] | None = None
        self._lock = threading.Lock()

    def _signature(self) -> tuple[float, float] | None:
        try:
            return self.index_path.stat().st_mtime, self.metadata_path.stat().st_mtime
        except FileNotFoundError:
            return None

    def _current_store(self) -> VectorStore:
        """Recarrega o índice se os arquivos mudaram em disco. A ingestão roda em outro
        container (docker compose run) e grava no volume compartilhado; sem isso, a API já
        em execução nunca enxergaria o índice novo até ser reiniciada."""
        signature = self._signature()
        if signature is None:
            raise IndexNotReadyError
        with self._lock:
            if self._store is None or signature != self._loaded_signature:
                self._store = FaissVectorStore.load(self.index_path, self.metadata_path)
                self._loaded_signature = signature
            return self._store

    def is_ready(self) -> bool:
        return self._signature() is not None

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        store = self._current_store()
        query_vector = self.embedder.embed([query])[0]
        hits = store.search(query_vector, k * CHUNK_OVERFETCH)

        # Mantém apenas o melhor chunk de cada documento (hits já vêm por score decrescente).
        best: dict[str, SearchResult] = {}
        for hit in hits:
            if hit.record.doc_id not in best:
                best[hit.record.doc_id] = SearchResult(
                    doc_id=hit.record.doc_id,
                    title=hit.record.title,
                    score=hit.score,
                    snippet=hit.record.text,
                )
        return list(best.values())[:k]
