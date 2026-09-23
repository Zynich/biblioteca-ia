"""Abstração de vector store + implementação com FAISS.

`VectorStore` é um Protocol: o serviço de busca depende dele, não do FAISS. Trocar por
Milvus (ou pgvector) é escrever uma nova classe com os mesmos métodos.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import faiss
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ChunkRecord:
    """Metadados de um chunk: a posição no índice FAISS é a posição na lista de records."""

    doc_id: str
    title: str
    text: str


@dataclass(frozen=True)
class SearchHit:
    record: ChunkRecord
    score: float


class VectorStore(Protocol):
    def add(self, vectors: NDArray[np.float32], records: list[ChunkRecord]) -> None: ...

    def search(self, query_vector: NDArray[np.float32], k: int) -> list[SearchHit]: ...

    def save(self) -> None: ...

    def __len__(self) -> int: ...


class FaissVectorStore:
    """IndexFlatIP (busca exata por produto interno). Com vetores normalizados (norma 1),
    o produto interno é igual à similaridade de cosseno. Para poucos milhares de vetores,
    busca exata é rápida e evita a perda de precisão de índices aproximados (HNSW/IVF)."""

    def __init__(self, dimension: int, index_path: str | Path, metadata_path: str | Path) -> None:
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self._index: faiss.Index = faiss.IndexFlatIP(dimension)
        self._records: list[ChunkRecord] = []

    def add(self, vectors: NDArray[np.float32], records: list[ChunkRecord]) -> None:
        if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
            raise ValueError(
                f"vetores devem ter shape (n, {self.dimension}), recebido {vectors.shape}"
            )
        if len(vectors) != len(records):
            raise ValueError("número de vetores e de records deve ser igual")
        self._index.add(np.ascontiguousarray(vectors, dtype=np.float32))
        self._records.extend(records)

    def search(self, query_vector: NDArray[np.float32], k: int) -> list[SearchHit]:
        if len(self._records) == 0:
            return []
        k = min(k, len(self._records))
        query = np.ascontiguousarray(query_vector.reshape(1, -1), dtype=np.float32)
        scores, positions = self._index.search(query, k)
        return [
            SearchHit(record=self._records[pos], score=float(score))
            for score, pos in zip(scores[0], positions[0], strict=True)
            if pos != -1  # FAISS usa -1 quando há menos resultados que k
        ]

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path))
        payload = {"dimension": self.dimension, "records": [asdict(r) for r in self._records]}
        self.metadata_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, index_path: str | Path, metadata_path: str | Path) -> "FaissVectorStore":
        index_path, metadata_path = Path(index_path), Path(metadata_path)
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        index = faiss.read_index(str(index_path))
        records = [ChunkRecord(**r) for r in payload["records"]]
        if index.ntotal != len(records):
            raise ValueError("índice FAISS e metadados estão inconsistentes")
        store = cls(payload["dimension"], index_path, metadata_path)
        store._index = index
        store._records = records
        return store

    def __len__(self) -> int:
        return len(self._records)
