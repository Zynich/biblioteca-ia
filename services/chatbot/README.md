# chatbot — Questão 2

Chatbot especialista em Python via LangChain (LCEL) + OpenAI, com memória de conversa
por sessão e rastreamento opcional via LangSmith.

## Rodando isoladamente (sem o compose raiz)

```bash
cd services/chatbot
uv sync
export OPENAI_API_KEY=sk-...          # obrigatório
export OPENAI_MODEL=gpt-4o-mini       # opcional, esse é o default
uv run uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## Interfaces

### CLI (atende literalmente "receber perguntas via input de texto")

```bash
make chat
# ou, dentro de services/chatbot:
uv run python -m app.cli
```

### API

| Método | Rota                | Descrição                                    |
|--------|----------------------|-------------------------------------------------|
| POST   | `/api/v1/chat`        | Pergunta + resposta completa (JSON)             |
| POST   | `/api/v1/chat/stream` | Mesma coisa, mas em streaming (Server-Sent Events) |
| GET    | `/health`             | Health check                                    |

```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Como criar uma lista em Python?"}'
```

Follow-up na mesma conversa (reaproveita o histórico por `session_id`):

```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "E como eu ordeno essa lista?"}'
```

Streaming (SSE):

```bash
curl -N -X POST http://localhost:8002/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Explique list comprehension"}'
```

## Escopo do chatbot

O prompt de sistema ([app/chain.py](app/chain.py)) restringe as respostas a dúvidas de
Python: sempre responde em português, sempre com explicação + exemplo de código, e
recusa educadamente perguntas fora do escopo (ver exemplos em
[docs/chatbot_examples.md](../../docs/chatbot_examples.md)).

## Memória de conversa

Histórico em RAM, indexado por `session_id`, via `RunnableWithMessageHistory`. Essa
classe está deprecated no LangChain atual (recomendam LangGraph + checkpointer), mas
foi mantida conscientemente pelo escopo do teste — ver
[docs/decisions.md](../../docs/decisions.md) para o racional completo. Em produção,
trocaria a memória em RAM por Redis (sobrevive a reinícios, funciona com múltiplas
instâncias).

## LangSmith (observabilidade)

Configure no `.env`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=biblioteca-ia-chatbot
```

Com isso ativo, toda chamada à chain aparece rastreada em https://smith.langchain.com —
sem nenhum código adicional (o LangChain lê essas variáveis diretamente do ambiente).

## Testes

```bash
uv run pytest --cov=app --cov-report=term-missing
```

**Nenhum teste chama a API da OpenAI de verdade.** Erros e sucesso são simulados com
`FakeListChatModel`/fakes customizados do `langchain_core`. Cobre: resposta a partir do
LLM fake, payload inválido (422), memória por sessão (a segunda mensagem carrega mais
contexto que a primeira), sessões diferentes não compartilham histórico, chave da
OpenAI ausente (500), erro genérico do provedor (502), timeout (504), streaming (SSE,
sucesso e erro) e a interface CLI (incluindo Ctrl+C e linhas em branco). 95% de
cobertura.
