"""Testes do endpoint de chat: resposta via LLM fake, memória por sessão, e
tratamento de erros (chave ausente, erro genérico do LLM, timeout)."""

from fastapi.testclient import TestClient
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

from app.api.deps import get_chain_provider
from app.chain import build_chain
from app.main import app


class RecordingFakeChatModel(BaseChatModel):
    """Fake chat model que grava as mensagens recebidas em cada chamada — usado para
    provar que o histórico de conversa (memória) está sendo enviado ao LLM."""

    calls: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(
        self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs
    ) -> ChatResult:
        self.calls.append(list(messages))
        content = f"resposta simulada {len(self.calls)}"
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "recording-fake"


class RaisingFakeChatModel(BaseChatModel):
    """Fake chat model que sempre lança uma exceção — simula erro no provedor do LLM."""

    error: Exception

    model_config = {"arbitrary_types_allowed": True}

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        raise self.error

    @property
    def _llm_type(self) -> str:
        return "raising-fake"


def override_chain(llm: BaseChatModel) -> None:
    chain = build_chain(llm=llm)
    app.dependency_overrides[get_chain_provider] = lambda: lambda: chain


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_answer_from_fake_llm(client: TestClient) -> None:
    override_chain(FakeListChatModel(responses=["Uma lista em Python é criada com colchetes []."]))

    response = client.post(
        "/api/v1/chat",
        json={"session_id": "s1", "message": "Como criar uma lista em Python?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "s1"
    assert "lista" in body["answer"].lower()


def test_chat_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"session_id": "s1"})

    assert response.status_code == 422


def test_chat_keeps_history_per_session(client: TestClient) -> None:
    fake = RecordingFakeChatModel()
    override_chain(fake)

    client.post("/api/v1/chat", json={"session_id": "s1", "message": "pergunta 1"})
    client.post("/api/v1/chat", json={"session_id": "s1", "message": "pergunta 2"})

    assert len(fake.calls) == 2
    # A segunda chamada deve carregar mais mensagens que a primeira: histórico (human +
    # AI da primeira rodada) + a nova pergunta — prova de que a memória por sessão funciona.
    assert len(fake.calls[1]) > len(fake.calls[0])


def test_chat_different_sessions_do_not_share_history(client: TestClient) -> None:
    fake = RecordingFakeChatModel()
    override_chain(fake)

    client.post("/api/v1/chat", json={"session_id": "s1", "message": "pergunta 1"})
    client.post("/api/v1/chat", json={"session_id": "s2", "message": "pergunta 1"})

    assert len(fake.calls) == 2
    assert len(fake.calls[0]) == len(fake.calls[1])


def test_chat_missing_api_key_returns_500(client: TestClient) -> None:
    # Não sobrescreve a dependency: usa a chain real (build_chain -> ChatOpenAI), que
    # deve falhar de forma controlada porque OPENAI_API_KEY não está setada no teste.
    response = client.post(
        "/api/v1/chat",
        json={"session_id": "s1", "message": "Como criar uma lista em Python?"},
    )

    assert response.status_code == 500
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_chat_llm_generic_error_returns_502(client: TestClient) -> None:
    override_chain(RaisingFakeChatModel(error=RuntimeError("falha simulada do provedor")))

    response = client.post("/api/v1/chat", json={"session_id": "s1", "message": "oi"})

    assert response.status_code == 502


def test_chat_llm_timeout_returns_504(client: TestClient) -> None:
    override_chain(RaisingFakeChatModel(error=TimeoutError("timeout simulado")))

    response = client.post("/api/v1/chat", json={"session_id": "s1", "message": "oi"})

    assert response.status_code == 504


def test_chat_stream_returns_sse(client: TestClient) -> None:
    override_chain(FakeListChatModel(responses=["resposta em streaming"]))

    response = client.post(
        "/api/v1/chat/stream",
        json={"session_id": "s1", "message": "Como criar uma lista em Python?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data:" in response.text


def test_chat_stream_missing_api_key_returns_500(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={"session_id": "s1", "message": "Como criar uma lista em Python?"},
    )

    assert response.status_code == 500
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_chat_stream_llm_error_emits_sse_error_event(client: TestClient) -> None:
    override_chain(RaisingFakeChatModel(error=RuntimeError("falha simulada do provedor")))

    response = client.post("/api/v1/chat/stream", json={"session_id": "s1", "message": "oi"})

    assert response.status_code == 200
    assert "event: error" in response.text
