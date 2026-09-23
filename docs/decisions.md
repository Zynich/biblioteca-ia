# Decisões técnicas e trade-offs

## Estrutura geral
- **Monorepo com 1 serviço por questão** (`services/books_api`, `services/chatbot`,
  `services/semantic_search`), cada um com seu próprio `pyproject.toml`/Dockerfile.
  Isola dependências pesadas (torch, faiss) da API de livros, que fica enxuta.
- **FastAPI nas três questões**: tipagem nativa via Pydantic, validação automática de
  payload e geração de OpenAPI/Swagger (`/docs`) sem esforço extra — atende ao
  requisito de "endpoints claros e bem documentados" das três questões.
- **uv** como gerenciador de dependências: lockfile reprodutível e build de imagem mais
  rápido que pip puro.
- **ruff + mypy + pytest + pre-commit**: padrão de mercado para lint, tipagem estática e
  testes, com hooks rodando antes de cada commit.
- **pydantic-settings + .env**: configuração 12-factor, nenhuma chave sensível commitada
  (`.env` está no `.gitignore`; `.env.example` documenta as variáveis esperadas).

## Questão 1 — API de livros
- **SQLite** em vez de Postgres: suficiente para o escopo do teste e evita subir um
  serviço de banco adicional. Em produção, trocaria por Postgres (ver "Próximos
  passos").
- **SQLAlchemy 2.0 + Alembic**: ORM tipado e migrations versionadas desde o início.
- Camadas separadas (`repositories/` para acesso a dados, `services/` para regra de
  negócio, `api/routes/` para HTTP) em vez de query direta na rota — facilita testes
  unitários isolados do banco.
- **Dockerfile com dev-dependencies também no runtime**: para que `make test`/`make
  lint` funcionem via `docker compose run` sem um estágio extra, a imagem final inclui
  pytest/ruff/mypy. Em produção real, o runtime seria construído sem dev-dependencies
  (`uv sync --no-dev`) e os testes rodariam a partir de um estágio `test` isolado — uma
  simplificação consciente para o escopo deste teste.

## Questão 2 — Chatbot
- **LangChain (LCEL) + LangSmith**: LCEL para compor `prompt | llm | parser` de forma
  declarativa; LangSmith para observabilidade/rastreio das chamadas ao LLM.
- **Modelo configurável via `OPENAI_MODEL`**: o enunciado cita GPT-4, mas os nomes de
  modelo da OpenAI mudam com frequência — mantendo isso como env var, o código não fica
  amarrado a um nome específico.
- **Memória em RAM (`RunnableWithMessageHistory`)**: suficiente para demonstrar o
  histórico por `session_id` no teste. Em produção, usaria Redis para persistir entre
  reinícios e múltiplas instâncias.
- **`RunnableWithMessageHistory` está deprecated desde o LangChain 0.3** (o time do
  LangChain recomenda migrar para LangGraph com um `checkpointer` para gerenciar
  memória). Decisão consciente de manter mesmo assim: a classe continua funcional
  (não tem previsão de remoção antes da v2.0), e o caso de uso aqui é um chatbot
  simples de pergunta-resposta com histórico por sessão — não um agente com múltiplas
  ferramentas ou grafo de estados. Adotar LangGraph só para isso trocaria uma
  dependência simples e já testada por uma nova peça de infraestrutura
  desproporcional ao problema. Se o chatbot evoluir para um agente (ferramentas,
  múltiplos passos, roteamento condicional), migrar para LangGraph com
  `MemorySaver`/`PostgresSaver` como checkpointer é o caminho natural.
- **Testes com `FakeListChatModel`**: os testes não fazem chamadas reais à OpenAI (sem
  custo, sem flakiness, sem exigir chave válida no CI).

## Questão 3 — Busca semântica
- **FAISS (`IndexFlatIP`) em vez de Milvus**: não exige um serviço externo; adequado ao
  volume de dados do teste (20-30 documentos). A interface `VectorStore` (protocolo)
  isola essa escolha — trocar por Milvus seria implementar uma nova classe.
- **Modelo multilíngue** (`paraphrase-multilingual-MiniLM-L12-v2`): os documentos de
  exemplo estão em português.
- **Embeddings com `transformers` puro** (tokenizer + modelo + mean pooling +
  normalização L2) em vez de `sentence-transformers` diretamente: demonstra
  entendimento do que a biblioteca faz por baixo dos panos.
- **Torch CPU-only** na imagem Docker (`--index-url https://download.pytorch.org/whl/cpu`):
  reduz o tamanho da imagem em vários GB, já que não há GPU disponível no ambiente de
  execução do teste.

## Próximos passos (fora do escopo do teste)
- Autenticação/autorização (JWT ou API key) nos três serviços.
- Rate limiting nos endpoints públicos.
- Trocar SQLite por Postgres na `books_api` (multi-processo, concorrência real).
- Trocar memória em RAM por Redis no chatbot (múltiplas instâncias, persistência).
- Migrar a memória de conversa do chatbot de `RunnableWithMessageHistory` (deprecated)
  para LangGraph + checkpointer, especialmente se o chatbot ganhar ferramentas/agente.
- Observabilidade: métricas (Prometheus) e tracing distribuído além do LangSmith.
- Deploy: imagens publicadas em registry + orquestração (Kubernetes/ECS) em vez de
  apenas Docker Compose local.
