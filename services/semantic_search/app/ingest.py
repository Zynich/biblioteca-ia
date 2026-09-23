"""Script de ingestão: lê os artigos, gera embeddings e persiste o índice FAISS.

Uso: `python -m app.ingest` (ou `make ingest`). Retorna exit code 0 em sucesso e 1 em falha,
para poder ser usado em automação/CI.
"""

import sys

from app.core.config import settings
from app.documents import load_articles
from app.embeddings import TextEmbedder, TransformersEmbedder
from app.indexing import build_index


def run(embedder: TextEmbedder | None = None) -> int:
    try:
        articles = load_articles(settings.articles_dir)
        if not articles:
            print(f"Nenhum artigo encontrado em {settings.articles_dir}", file=sys.stderr)
            return 1

        print(f"{len(articles)} artigos lidos. Carregando modelo {settings.embedding_model}...")
        embedder = embedder or TransformersEmbedder(settings.embedding_model)
        store = build_index(
            articles,
            embedder,
            settings.faiss_index_path,
            settings.faiss_metadata_path,
            settings.chunk_size,
            settings.chunk_overlap,
        )
    except (OSError, ValueError) as exc:
        print(f"Falha na ingestão: {exc}", file=sys.stderr)
        return 1

    print(f"Índice salvo em {settings.faiss_index_path} ({len(store)} chunks).")
    return 0


if __name__ == "__main__":
    sys.exit(run())
