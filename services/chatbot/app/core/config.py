"""Configurações da aplicação. Também garante que as variáveis do .env cheguem ao
processo via os.environ — o LangChain lê LANGSMITH_TRACING/LANGSMITH_API_KEY/
LANGSMITH_PROJECT diretamente do ambiente, sem precisar de nenhum código extra
nosso, então isso é o suficiente para ativar o tracing."""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    langsmith_tracing: bool = False
    langsmith_project: str = "biblioteca-ia-chatbot"


settings = Settings()
