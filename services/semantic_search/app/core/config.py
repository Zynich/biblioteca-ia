"""Configurações da aplicação (variáveis de ambiente / .env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    faiss_index_path: str = "index/articles.faiss"
    faiss_metadata_path: str = "index/articles_metadata.json"
    articles_dir: str = "data/articles"

    # ~500 caracteres cabem com folga nos 128 tokens que esse modelo processa por texto.
    chunk_size: int = 500
    chunk_overlap: int = 50


settings = Settings()
