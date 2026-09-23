"""Constrói o índice vetorial a partir dos artigos: chunking -> embeddings -> FAISS."""

from pathlib import Path

from app.chunking import chunk_text
from app.documents import Article
from app.embeddings import TextEmbedder
from app.vector_store import ChunkRecord, FaissVectorStore


def build_index(
    articles: list[Article],
    embedder: TextEmbedder,
    index_path: str | Path,
    metadata_path: str | Path,
    chunk_size: int = 500,
    overlap: int = 50,
) -> FaissVectorStore:
    records: list[ChunkRecord] = []
    for article in articles:
        # O título entra no texto embutido: ajuda a busca em chunks que, isolados, não
        # mencionam o assunto do artigo.
        for piece in chunk_text(article.content, chunk_size, overlap):
            records.append(ChunkRecord(doc_id=article.id, title=article.title, text=piece))

    if not records:
        raise ValueError("nenhum chunk gerado: sem documentos para indexar")

    vectors = embedder.embed([f"{r.title}. {r.text}" for r in records])

    store = FaissVectorStore(embedder.dimension, index_path, metadata_path)
    store.add(vectors, records)
    store.save()
    return store
