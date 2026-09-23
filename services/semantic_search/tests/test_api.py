from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_search_service
from app.core.config import settings
from app.main import app
from app.search import SemanticSearchService


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_service(service: SemanticSearchService) -> None:
    app.dependency_overrides[get_search_service] = lambda: service


def test_search_returns_relevant_documents(
    client: TestClient, built_service: SemanticSearchService
) -> None:
    use_service(built_service)

    response = client.get("/api/v1/search", params={"q": "como fazer bolo", "k": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "como fazer bolo"
    assert len(body["results"]) == 3
    assert body["results"][0]["doc_id"] == "culinaria-01"
    assert set(body["results"][0]) == {"doc_id", "title", "score", "snippet"}


def test_default_k_is_5(client: TestClient, built_service: SemanticSearchService) -> None:
    use_service(built_service)

    response = client.get("/api/v1/search", params={"q": "python"})

    assert len(response.json()["results"]) == 5


@pytest.mark.parametrize(
    "params", [{}, {"q": ""}, {"q": "   "}, {"q": "x", "k": 0}, {"q": "x", "k": 21}]
)
def test_invalid_parameters_return_422(
    client: TestClient, built_service: SemanticSearchService, params: dict[str, object]
) -> None:
    use_service(built_service)

    assert client.get("/api/v1/search", params=params).status_code == 422


def test_search_without_index_returns_503(
    client: TestClient, tmp_path: Path, fake_embedder
) -> None:
    use_service(SemanticSearchService(fake_embedder, tmp_path / "x.faiss", tmp_path / "x.json"))

    response = client.get("/api/v1/search", params={"q": "qualquer"})

    assert response.status_code == 503
    assert "ingestão" in response.json()["detail"]


def test_health_reports_index_readiness(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index = tmp_path / "a.faiss"
    monkeypatch.setattr(settings, "faiss_index_path", str(index))

    assert client.get("/health").json() == {"status": "ok", "index_ready": False}

    index.write_bytes(b"x")
    assert client.get("/health").json() == {"status": "ok", "index_ready": True}
