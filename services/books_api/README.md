# books_api — Questão 1

API de biblioteca virtual: cadastro e consulta de livros. FastAPI + SQLAlchemy 2.0 +
SQLite, com camadas separadas (`api/routes` → `services` → `repositories`).

## Rodando isoladamente (sem o compose raiz)

```bash
cd services/books_api
uv sync
uv run uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## Endpoints

| Método | Rota                                   | Descrição                              |
|--------|-----------------------------------------|------------------------------------------|
| POST   | `/api/v1/books`                          | Cadastra um livro                        |
| GET    | `/api/v1/books?title=&author=&limit=&offset=` | Busca parcial (case-insensitive), paginada |
| GET    | `/api/v1/books/{id}`                     | Detalhe de um livro                      |
| GET    | `/health`                                | Health check                             |

## Exemplos de `curl`

Cadastrar um livro:

```bash
curl -X POST http://localhost:8001/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fluent Python",
    "author": "Luciano Ramalho",
    "published_date": "2015-08-20",
    "summary": "Um guia aprofundado sobre recursos idiomáticos da linguagem Python."
  }'
```

Buscar por título (parcial, case-insensitive):

```bash
curl "http://localhost:8001/api/v1/books?title=fluent"
```

Buscar por autor:

```bash
curl "http://localhost:8001/api/v1/books?author=ramalho"
```

Buscar por título OU autor, paginado:

```bash
curl "http://localhost:8001/api/v1/books?title=python&limit=10&offset=0"
```

Detalhe de um livro:

```bash
curl http://localhost:8001/api/v1/books/1
```

## Testes

```bash
uv run pytest --cov=app --cov-report=term-missing
```

Cobre: criação com sucesso, payload inválido (422), título/autor em branco, data de
publicação no futuro, busca por título parcial case-insensitive, busca por autor,
busca sem resultados, paginação, detalhe por id e 404 para id inexistente.

## Migrations (Alembic)

O schema é criado automaticamente no startup (`Base.metadata.create_all`) para
simplificar a execução via Docker Compose. As migrations em `migrations/` documentam
a evolução do schema e seriam o caminho usado em produção:

```bash
uv run alembic upgrade head
```
