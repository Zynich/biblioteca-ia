"""Fixtures compartilhadas. O modelo real é carregado uma única vez por sessão de testes
(e fica em cache no disco pelo Hugging Face); testes que não precisam dele usam um
embedder fake determinístico."""

import hashlib
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from app.core.config import settings
from app.documents import Article, load_articles
from app.embeddings import TransformersEmbedder
from app.indexing import build_index
from app.search import SemanticSearchService


class FakeEmbedder:
    """Embedder determinístico e instantâneo: vetor pseudoaleatório derivado do hash do
    texto, normalizado (norma 1) como o embedder real."""

    dimension = 16

    def embed(self, texts: list[str]) -> NDArray[np.float32]:
        vectors = []
        for text in texts:
            seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "little")
            vec = np.random.default_rng(seed).normal(size=self.dimension).astype(np.float32)
            vectors.append(vec / np.linalg.norm(vec))
        return np.vstack(vectors)


@pytest.fixture(scope="session")
def embedder() -> TransformersEmbedder:
    return TransformersEmbedder(settings.embedding_model)


@pytest.fixture(scope="session")
def articles() -> list[Article]:
    return load_articles(Path(__file__).parent.parent / "data" / "articles")


@pytest.fixture(scope="session")
def index_paths(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    base = tmp_path_factory.mktemp("index")
    return base / "articles.faiss", base / "articles.json"


@pytest.fixture(scope="session")
def built_service(
    embedder: TransformersEmbedder,
    articles: list[Article],
    index_paths: tuple[Path, Path],
) -> SemanticSearchService:
    """Índice real (modelo real + os 24 artigos) construído uma vez por sessão."""
    index_path, metadata_path = index_paths
    build_index(articles, embedder, index_path, metadata_path)
    return SemanticSearchService(embedder, index_path, metadata_path)


@pytest.fixture()
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()
