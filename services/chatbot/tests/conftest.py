"""Fixtures compartilhadas. Nenhum teste chama a API da OpenAI de verdade — a
dependency `get_chain` é sobrescrita com chains construídas sobre um LLM fake."""

import os
from collections.abc import Generator

# Isola os testes do ambiente de quem executa `pytest`: o teste de "chave ausente" depende
# de não haver chave, e um .env com LLM_PROVIDER=ollama/gemini (que o load_dotenv() de
# app.core.config encontra subindo as pastas, e o `make test` herda no container) mudaria o
# provedor. Definir (em vez de remover) as variáveis funciona porque load_dotenv não
# sobrescreve variáveis que já existem.
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GOOGLE_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.chain import get_chatbot_chain, reset_history_store  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_state() -> Generator[None, None, None]:
    """Evita que histórico de conversa ou o singleton de chain vazem entre testes."""
    reset_history_store()
    get_chatbot_chain.cache_clear()
    yield
    reset_history_store()
    get_chatbot_chain.cache_clear()
    app.dependency_overrides.clear()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
