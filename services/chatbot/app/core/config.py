"""Configurações da aplicação. Também garante que as variáveis do .env cheguem ao
processo via os.environ — o LangChain lê LANGSMITH_TRACING/LANGSMITH_API_KEY/
LANGSMITH_PROJECT diretamente do ambiente, sem precisar de nenhum código extra
nosso, então isso é o suficiente para ativar o tracing."""

from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # openai é o padrão do enunciado; gemini (plano gratuito) e ollama (local, sem chave)
    # permitem rodar o chatbot de verdade sem uma conta paga.
    llm_provider: Literal["openai", "gemini", "ollama"] = "openai"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    google_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:3b"

    langsmith_tracing: bool = False
    langsmith_project: str = "biblioteca-ia-chatbot"


settings = Settings()
