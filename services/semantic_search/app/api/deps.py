"""Dependencies compartilhadas entre rotas."""

from functools import lru_cache

from app.core.config import settings
from app.embeddings import TransformersEmbedder
from app.search import SemanticSearchService


@lru_cache(maxsize=1)
def get_search_service() -> SemanticSearchService:
    """Singleton: carregar o modelo de embeddings é caro, então acontece uma única vez
    (na primeira busca) e é reaproveitado. Sobrescrito nos testes."""
    return SemanticSearchService(
        TransformersEmbedder(settings.embedding_model),
        settings.faiss_index_path,
        settings.faiss_metadata_path,
    )
