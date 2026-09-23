# biblioteca-ia

> **Projeto prático feito para estudo.** É uma resolução de um teste técnico de
> *Desenvolvedor Backend com foco em IA*, montada como monorepo para praticar engenharia de
> software (Docker Compose, testes, lint, CI, documentação de decisões) além de resolver os
> exercícios. Não é um produto nem um serviço de produção.
>
> O enunciado completo está em [docs/enunciado.md](docs/enunciado.md), junto com uma
> **matriz de conformidade** que liga cada requisito ao código e a um comando de verificação —
> para quem for fazer o mesmo desafio ou validar esta resolução.

## O que tem aqui

| Questão | Tema | Serviço | Porta | Documentação |
|---|---|---|---|---|
| 1 | API de livros (cadastro e consulta por título/autor) | [`books_api`](services/books_api) | 8001 | [README](services/books_api/README.md) |
| 2 | Chatbot de Python (LangChain + OpenAI + LangSmith) | [`chatbot`](services/chatbot) | 8002 | [README](services/chatbot/README.md) · [exemplos](docs/chatbot_examples.md) |
| 3 | Busca semântica (embeddings + FAISS) | [`semantic_search`](services/semantic_search) | 8003 | [README](services/semantic_search/README.md) · [pipeline](docs/semantic_search.md) |

```
                       docker compose
      ┌──────────────────────┼──────────────────────┐
 books_api                chatbot             semantic_search
 FastAPI + SQLAlchemy     FastAPI + LangChain  FastAPI + transformers + FAISS
 :8001                    :8002                :8003
   │                        │                    │
 volume books_data      OpenAI + LangSmith    volumes search_index, hf_cache
 (SQLite)               (serviços externos)   (índice FAISS e modelo baixado)
```

Cada serviço é independente (dependências, imagem e testes próprios) e segue as mesmas
camadas: `api/routes` → `services` → `repositories` (Q1) / módulos de domínio (Q2, Q3).

## Pré-requisitos

- Docker com Docker Compose v2
- `make` (opcional: cada alvo do [Makefile](Makefile) é só um `docker compose ...`)
- Para o chatbot (Q2), **um** destes: `OPENAI_API_KEY` (padrão do enunciado), `GOOGLE_API_KEY` do
  Gemini (gratuita, só conta Google) **ou** nenhuma chave, usando o LLM local via Ollama
  (`make up-local`, ~2 GB de modelo). Q1, Q3 e todos os testes funcionam sem chave.
- ~3 GB livres para as imagens e ~500 MB para o modelo de embeddings (baixado no `make ingest`)

## Como rodar

```bash
cp .env.example .env     # preencha OPENAI_API_KEY se quiser usar o chatbot de verdade
make up                  # constrói e sobe os 3 serviços
make ingest              # Q3: gera os embeddings e o índice FAISS (1ª vez baixa o modelo)
```

| Serviço | Swagger |
|---|---|
| Livros | http://localhost:8001/docs |
| Chatbot | http://localhost:8002/docs |
| Busca semântica | http://localhost:8003/docs |

Sem `make`, os equivalentes são `docker compose up -d --build` e
`docker compose run --rm semantic_search python -m app.ingest`.

### Experimente

```bash
# Q1 — cadastrar e consultar
curl -X POST localhost:8001/api/v1/books -H 'Content-Type: application/json' \
  -d '{"title":"Fluent Python","author":"Luciano Ramalho","published_date":"2015-08-20","summary":"Guia de Python idiomático."}'
curl "localhost:8001/api/v1/books?title=fluent"

# Q2 — chatbot (escolha o provedor em LLM_PROVIDER no .env e reinicie com `make up`)
#   sem chave nenhuma: LLM_PROVIDER=ollama, `make up-local`, `make pull-model`
curl -X POST localhost:8002/api/v1/chat -H 'Content-Type: application/json' \
  -d '{"session_id":"demo","message":"Como criar uma lista em Python?"}'
make chat                # ou, pelo terminal, em modo interativo (input de texto)

# Q3 — busca semântica (depois do make ingest)
curl "localhost:8003/api/v1/search?q=como%20fazer%20bolo&k=3"
```

## Testes e qualidade

```bash
make test     # pytest dos 3 serviços, dentro dos containers
make lint     # ruff + mypy (strict) dos 3 serviços
make fmt      # formata com ruff
```

| Serviço | Testes | Cobertura | Observação |
|---|---|---|---|
| `books_api` | 11 | 98% | SQLite em memória por teste |
| `chatbot` | 24 | 97% | LLM fake: **nenhum teste chama a OpenAI** |
| `semantic_search` | 49 | 99% | Usa o modelo real (baixado uma vez e reaproveitado do cache) |

A pipeline de CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) roda lint, tipagem e
testes de cada serviço.

## Estado e limitações (leia antes de validar)

- **As respostas do chatbot em [docs/chatbot_examples.md](docs/chatbot_examples.md) são reais, mas
  não são do GPT**: sem chave da OpenAI, foram geradas pelo provedor local `ollama` (Qwen 3B),
  que às vezes erra detalhes técnicos (apontados no arquivo). O caminho com OpenAI e Gemini não
  foi exercitado com chave real, e o LangSmith também não.
- A busca semântica tem limitações mostradas com dados reais em
  [docs/semantic_search.md](docs/semantic_search.md) (consultas de uma palavra, assuntos fora
  do corpus).
- Demais divergências em relação ao enunciado (GPT-4 configurável, API de memória
  deprecated): [docs/enunciado.md](docs/enunciado.md#3-ressalvas-e-divergências-leia-antes-de-validar).

## Decisões técnicas

[docs/decisions.md](docs/decisions.md) reúne as escolhas, os trade-offs (SQLite vs Postgres,
FAISS vs Milvus, memória em RAM vs Redis, uma imagem por serviço) e os "próximos passos" que
faltariam para produção (autenticação, rate limiting, Postgres, Redis, observabilidade).

## Estrutura

```
biblioteca-ia/
├── docker-compose.yml   Makefile   .env.example   (Ollama opcional: profile local-llm)
├── .github/workflows/ci.yml
├── docs/                enunciado.md · decisions.md · chatbot_examples.md · semantic_search.md
└── services/
    ├── books_api/       Q1
    ├── chatbot/         Q2
    └── semantic_search/ Q3
```
