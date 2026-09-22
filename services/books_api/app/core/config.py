"""Configurações da aplicação, carregadas de variáveis de ambiente (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOOKS_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/books.db"


# Instância única, importada pelo resto da aplicação (evita reler o .env repetidamente).
settings = Settings()
