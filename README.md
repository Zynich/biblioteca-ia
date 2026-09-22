# biblioteca-ia

Teste técnico — Desenvolvedor Backend com foco em IA — implementado como monorepo de
3 serviços independentes (um por questão), orquestrados via Docker Compose.

## Arquitetura

```
                         docker-compose
        ┌──────────────────────┼──────────────────────┐
        │                      │                       │
   books_api               chatbot              semantic_search
  (FastAPI + SQLAlchemy)  (FastAPI + LangChain)  (FastAPI + FAISS)
   :8001 -> :8000           :8002 -> :8000          :8003 -> :8000
        │                      │                       │
   volume: books_data      OpenAI API +          volumes: search_index,
   (SQLite)                LangSmith (externos)  hf_cache (modelo HF)
```

| Serviço            | Questão | Pasta                          | Porta local |
|---------------------|---------|----------------------------------|-------------|
| `books_api`          | 1       | `services/books_api`             | 8001        |
| `chatbot`             | 2       | `services/chatbot`               | 8002        |
| `semantic_search`     | 3       | `services/semantic_search`       | 8003        |

Cada serviço segue a mesma organização interna (camadas `api/routes`, `services`,
`repositories`/`core`, `schemas`, testes em `tests/`) — ver [docs/decisions.md](docs/decisions.md)
para o racional de cada escolha técnica.

## Pré-requisitos

- Docker e Docker Compose
- Uma chave de API da OpenAI (apenas para a Questão 2 — `chatbot`)

## Como rodar

```bash
cp .env.example .env
# edite .env e preencha OPENAI_API_KEY (necessário só para o chatbot)
make up
make ingest   # gera o índice FAISS da Questão 3 (necessário antes de usar /search)
```

Swaggers de cada serviço:

- Questão 1 — livros: http://localhost:8001/docs
- Questão 2 — chatbot: http://localhost:8002/docs
- Questão 3 — busca semântica: http://localhost:8003/docs

## Testes

```bash
make test
```

Cada serviço roda `pytest` isoladamente dentro do seu container (sem depender dos
outros serviços nem de chaves de API reais — o chatbot usa um LLM fake nos testes).

## Lint / formatação

```bash
make lint
make fmt
```

## Questão 1 — API de livros

Ver [services/books_api/README.md](services/books_api/README.md) para detalhes e exemplos de `curl`.

## Questão 2 — Chatbot

Ver [services/chatbot/README.md](services/chatbot/README.md) e [docs/chatbot_examples.md](docs/chatbot_examples.md).

## Questão 3 — Busca semântica

Ver [services/semantic_search/README.md](services/semantic_search/README.md) e [docs/semantic_search.md](docs/semantic_search.md).

## Decisões técnicas e trade-offs

Ver [docs/decisions.md](docs/decisions.md).

## Próximos passos

Ver seção final de [docs/decisions.md](docs/decisions.md) (autenticação, rate limiting,
Postgres, Redis, observabilidade).
