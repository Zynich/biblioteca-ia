"""Seleção do provedor de LLM (LLM_PROVIDER). Só constrói os clientes — nenhum teste faz
chamada de rede."""

import httpx
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.api.deps import get_chain_provider
from app.chain import MissingAPIKeyError, _default_llm, build_chain
from app.core.config import settings
from app.main import app
from tests.test_chat import RaisingFakeChatModel


def use_provider(monkeypatch: pytest.MonkeyPatch, provider: str, **overrides: object) -> None:
    monkeypatch.setattr(settings, "llm_provider", provider)
    for name, value in overrides.items():
        monkeypatch.setattr(settings, name, value)


def test_default_provider_is_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    use_provider(monkeypatch, "openai", openai_api_key="sk-teste", openai_model="gpt-4")

    llm = _default_llm()

    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4"


def test_openai_without_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    use_provider(monkeypatch, "openai", openai_api_key=None)

    with pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"):
        _default_llm()


def test_gemini_uses_configured_model(monkeypatch: pytest.MonkeyPatch) -> None:
    use_provider(monkeypatch, "gemini", google_api_key="chave-teste", gemini_model="gemini-x")

    llm = _default_llm()

    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model == "gemini-x"


def test_gemini_without_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    use_provider(monkeypatch, "gemini", google_api_key=None)

    with pytest.raises(MissingAPIKeyError, match="GOOGLE_API_KEY"):
        _default_llm()


def test_ollama_needs_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    use_provider(
        monkeypatch,
        "ollama",
        ollama_model="qwen2.5:3b",
        ollama_base_url="http://ollama:11434",
        openai_api_key=None,
        google_api_key=None,
    )

    llm = _default_llm()

    assert isinstance(llm, ChatOllama)
    assert llm.model == "qwen2.5:3b"
    assert llm.base_url == "http://ollama:11434"


def test_provider_setting_rejects_unknown_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "skynet")

    with pytest.raises(ValueError):
        type(settings)()


def test_build_chain_uses_selected_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    use_provider(monkeypatch, "ollama")

    assert build_chain() is not None


def test_api_returns_500_naming_the_missing_gemini_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_provider(monkeypatch, "gemini", google_api_key=None)

    response = client.post("/api/v1/chat", json={"session_id": "s", "message": "oi"})

    assert response.status_code == 500
    assert "GOOGLE_API_KEY" in response.json()["detail"]


def test_httpx_timeout_returns_504(client: TestClient) -> None:
    llm: BaseChatModel = RaisingFakeChatModel(error=httpx.ReadTimeout("lento demais"))
    chain = build_chain(llm=llm)
    app.dependency_overrides[get_chain_provider] = lambda: lambda: chain

    response = client.post("/api/v1/chat", json={"session_id": "s", "message": "oi"})

    assert response.status_code == 504
