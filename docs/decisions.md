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
- **Torch CPU-only** via índice explícito do uv (`[[tool.uv.index]]` apontando para
  `https://download.pytorch.org/whl/cpu`, equivalente ao `--index-url` do pip): a build
  padrão do PyPI traz bibliotecas CUDA e infla a imagem em vários GB; não há GPU no ambiente
  do teste. O `uv.lock` fixa isso e os Dockerfiles usam `uv sync --frozen`.
- **Chunking 500/50 com título no embedding**: ~500 caracteres cabem nos 128 tokens do
  modelo; a sobreposição evita perder contexto na fronteira e o título é concatenado ao chunk
  para que trechos do meio do artigo mantenham o assunto. A busca devolve **documentos**
  (melhor chunk de cada um), buscando 5x mais chunks que `k` para preencher `k` documentos
  distintos.
- **Recarga automática do índice**: a ingestão roda em outro container (`docker compose run`)
  e grava no volume compartilhado; a API compara o `mtime` dos arquivos a cada busca e
  recarrega se mudaram. Sem isso, `make up` seguido de `make ingest` deixaria a API em 503
  até reiniciar. Alternativa descartada: endpoint `/reload` (exigiria passo manual).
- **Inferência determinística** (`mkldnn` off, 1 thread): no ambiente de desenvolvimento a
  inferência CPU do torch variava entre chamadas idênticas (detalhes e medições em
  [semantic_search.md](semantic_search.md)). Testes de embedding comparam por cosseno, não
  por igualdade exata.
- **Testes com o modelo real** (fixture de sessão, cache do HF) em vez de mocks: o requisito
  "`como fazer bolo` retorna o artigo de culinária" só é verificável com embeddings de
  verdade. Testes de ingestão/API que não dependem de semântica usam um embedder fake
  determinístico e rápido.
- **`HF_HOME` em `/app/.cache`** e não `/root/.cache`: o container roda como usuário
  não-root; o diretório é criado na imagem com o dono correto para o volume `hf_cache`
  herdar as permissões.

## Docker (todos os serviços)
- **`COPY --chown`** no estágio final em vez de `chown -R /app`: o `chown -R` regrava o
  venv inteiro em uma nova layer (a imagem do `semantic_search` passou de 3,7 GB para 2,0 GB).
- **`uv.lock` + `uv sync --frozen`** nas imagens: build reproduzível com as mesmas versões
  do desenvolvimento. `.dockerignore` em cada serviço evita enviar `.venv`/caches (~1 GB
  no caso do torch) ao build context.
- **`libgomp1`** instalado no runtime do `semantic_search`: `faiss-cpu` precisa do runtime
  OpenMP, que não vem na imagem `slim`.

## Próximos passos (fora do escopo do teste)
- Autenticação/autorização (JWT ou API key) nos três serviços.
- Rate limiting nos endpoints públicos.
- Trocar SQLite por Postgres na `books_api` (multi-processo, concorrência real).
- `min_score` na busca semântica e re-ranking com cross-encoder para consultas curtas.
- Trocar memória em RAM por Redis no chatbot (múltiplas instâncias, persistência).
- Migrar a memória de conversa do chatbot de `RunnableWithMessageHistory` (deprecated)
  para LangGraph + checkpointer, especialmente se o chatbot ganhar ferramentas/agente.
- Observabilidade: métricas (Prometheus) e tracing distribuído além do LangSmith.
- Deploy: imagens publicadas em registry + orquestração (Kubernetes/ECS) em vez de
  apenas Docker Compose local.
