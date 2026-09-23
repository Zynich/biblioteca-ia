"""Fixtures compartilhadas. Nenhum teste chama a API da OpenAI de verdade — a
dependency `get_chain` é sobrescrita com chains construídas sobre um LLM fake."""

import os
from collections.abc import Generator

# Garante que os testes rodem sem uma chave real, independentemente do ambiente de
# quem executa `pytest` — o teste de "chave ausente" depende disso.
os.environ.pop("OPENAI_API_KEY", None)

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
