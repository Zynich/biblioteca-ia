"""Testes dos endpoints de livros: cadastro, validação, busca e detalhe."""

from datetime import date, timedelta

from fastapi.testclient import TestClient

VALID_BOOK = {
    "title": "Fluent Python",
    "author": "Luciano Ramalho",
    "published_date": "2015-08-20",
    "summary": "Um guia aprofundado sobre recursos idiomáticos da linguagem Python.",
}


def create_book(client: TestClient, **overrides: object) -> dict:
    payload = {**VALID_BOOK, **overrides}
    response = client.post("/api/v1/books", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_book_success(client: TestClient) -> None:
    body = create_book(client)

    assert body["id"] is not None
    assert body["title"] == VALID_BOOK["title"]
    assert body["author"] == VALID_BOOK["author"]
    assert body["published_date"] == VALID_BOOK["published_date"]
    assert body["summary"] == VALID_BOOK["summary"]
    assert "created_at" in body


def test_create_book_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/books", json={"title": "", "author": "X"})

    assert response.status_code == 422


def test_create_book_blank_title_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/books", json={**VALID_BOOK, "title": "   "})

    assert response.status_code == 422


def test_create_book_future_date_returns_422(client: TestClient) -> None:
    future_date = (date.today() + timedelta(days=1)).isoformat()

    response = client.post("/api/v1/books", json={**VALID_BOOK, "published_date": future_date})

    assert response.status_code == 422


def test_search_by_title_partial_case_insensitive(client: TestClient) -> None:
    create_book(client, title="Fluent Python")
    create_book(client, title="Clean Code", author="Robert C. Martin")

    response = client.get("/api/v1/books", params={"title": "flu"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Fluent Python"


def test_search_by_author(client: TestClient) -> None:
    create_book(client, title="Fluent Python", author="Luciano Ramalho")
    create_book(client, title="Effective Python", author="Brett Slatkin")

    response = client.get("/api/v1/books", params={"author": "ramalho"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["author"] == "Luciano Ramalho"


def test_search_without_results(client: TestClient) -> None:
    create_book(client)

    response = client.get("/api/v1/books", params={"title": "não existe nenhum livro assim"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_search_pagination(client: TestClient) -> None:
    for i in range(5):
        create_book(client, title=f"Livro {i}", author="Autor Comum")

    first_page = client.get("/api/v1/books", params={"author": "Comum", "limit": 2, "offset": 0})
    second_page = client.get("/api/v1/books", params={"author": "Comum", "limit": 2, "offset": 2})

    assert first_page.json()["total"] == 5
    assert len(first_page.json()["items"]) == 2
    assert len(second_page.json()["items"]) == 2
    first_ids = {item["id"] for item in first_page.json()["items"]}
    second_ids = {item["id"] for item in second_page.json()["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_get_book_by_id(client: TestClient) -> None:
    created = create_book(client)

    response = client.get(f"/api/v1/books/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_book_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/books/999999")

    assert response.status_code == 404


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
