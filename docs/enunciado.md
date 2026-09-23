# Enunciado e matriz de conformidade

> Projeto **prático, feito para estudo**. Este arquivo existe para que quem for fazer o
> mesmo desafio, ou validar esta resolução, consiga conferir cada requisito do enunciado
> contra o que foi implementado — e reproduzir a verificação com um comando.

## 1. Enunciado (transcrito como recebido)

**DESENVOLVEDOR BACKEND COM FOCO EM IA**

Instruções:
Responda todas as questões abaixo.
Utilize o Python para implementar suas soluções quando necessário.
Certifique-se de comentar seu código para explicar sua lógica.

### Questão 1: Desenvolvimento de API com Django/Flask/FastAPI

Desenvolva uma API simples que permite aos usuários cadastrar e consultar livros em uma
biblioteca virtual. A API deve incluir as seguintes funcionalidades:

1. Cadastro de livros com os campos: título, autor, data de publicação e resumo.
2. Consulta de livros por título ou autor.
3. Implemente a API utilizando um dos frameworks: Django, Flask ou FastAPI.

Certifique-se de:

- Criar endpoints claros e bem documentados.
- Utilizar um banco de dados SQLite para armazenamento.
- Implementar testes unitários para os endpoints criados.

Dicas:

- Para Django, considere utilizar o Django Rest Framework (DRF).
- Para Flask, considere utilizar Flask-RESTful.
- Para FastAPI, utilize os recursos nativos do framework para criação de APIs.

### Questão 2: Implementação de Chatbot com IA Generativa (Langchain, Langsmith, LLMs)

Você precisa desenvolver um chatbot que utilize um modelo de linguagem (LLM) como o GPT-4
da OpenAI para responder perguntas dos usuários sobre programação em Python. O chatbot
deve:

1. Receber perguntas dos usuários via input de texto.
2. Utilizar o Langchain para gerenciar o fluxo de conversação e integrar com o LLM.
3. Responder às perguntas utilizando o modelo da OpenAI.

Implemente um exemplo simples onde o usuário possa perguntar algo como "Como criar uma
lista em Python?" e o chatbot responda com uma explicação detalhada.

Dicas:

- Utilize o Langchain para facilitar a integração e gerenciamento das respostas do LLM.
- Certifique-se de configurar corretamente a API da OpenAI.
- Forneça exemplos de perguntas e respostas para demonstrar o funcionamento do chatbot.

### Questão 3: Trabalhando com Vector Stores e Embeddings

Você deve criar um sistema de busca semântica de documentos utilizando embeddings e vector
stores. Para isso, siga as etapas abaixo:

1. Utilize um conjunto de documentos de texto (pode ser um conjunto de artigos ou posts de
   um blog).
2. Gere embeddings para esses documentos utilizando um modelo de embeddings.
3. Armazene esses embeddings em uma vector store como FAISS ou Milvus.
4. Implemente uma função de busca que, dado um texto de consulta, retorne os documentos
   mais relevantes com base na similaridade semântica.

Dicas:

- Utilize bibliotecas como transformers para gerar embeddings.
- Documente o processo de criação dos embeddings e armazenamento na vector store.
- Demonstre a busca semântica com exemplos de consultas e resultados relevantes.

> Transcrição fiel do texto recebido, com apenas as palavras coladas ("consultarlivros",
> "portítulo", "Implementartestes", "chatbotresponda", "consulta,retorne") separadas.

## 2. Matriz de conformidade

Legenda: ✅ atendido e verificado · ⚠️ atendido com ressalva (ver coluna "Como verificar" e a
seção 3).

Pré-requisito dos comandos: `cp .env.example .env` e `make up` (ou os `docker compose ...`
equivalentes que o [Makefile](../Makefile) executa).

### Geral

| Requisito | Status | Onde | Como verificar |
|---|---|---|---|
| Usar Python | ✅ | Os 3 serviços (Python 3.12) | — |
| Comentar o código explicando a lógica | ✅ | Docstrings/comentários no "porquê" das decisões; `app/embeddings.py` comenta cada etapa do pipeline | Ler `services/semantic_search/app/embeddings.py` |

### Questão 1 — `services/books_api`

| Requisito | Status | Onde | Como verificar |
|---|---|---|---|
| Cadastro com título, autor, data de publicação e resumo | ✅ | [`schemas/book.py`](../services/books_api/app/schemas/book.py) (`BookCreate`) · `POST /api/v1/books` | `curl -X POST localhost:8001/api/v1/books -H 'Content-Type: application/json' -d '{"title":"Fluent Python","author":"Luciano Ramalho","published_date":"2015-08-20","summary":"Guia de Python idiomático."}'` |
| Consulta por título ou autor | ✅ | [`repositories/book_repository.py`](../services/books_api/app/repositories/book_repository.py) · `GET /api/v1/books?title=&author=` (parcial, case-insensitive, paginado) | `curl "localhost:8001/api/v1/books?title=fluent"` e `?author=ramalho` |
| Usar Django, Flask **ou** FastAPI | ✅ | FastAPI | — |
| Endpoints claros e bem documentados | ✅ | `summary`/`description` em cada rota, exemplo no schema | Abrir http://localhost:8001/docs |
| Banco SQLite | ✅ | [`core/config.py`](../services/books_api/app/core/config.py), volume `books_data` | Os dados sobrevivem a `docker compose down` / `up` |
| Testes unitários dos endpoints | ✅ | [`tests/test_books.py`](../services/books_api/tests/test_books.py) — 11 testes, 98% de cobertura | `docker compose run --rm books_api pytest --cov=app` |
| Dica FastAPI: recursos nativos | ✅ | `APIRouter`, `Depends`, `Query`, `response_model`, Pydantic | — |

### Questão 2 — `services/chatbot`

| Requisito | Status | Onde | Como verificar |
|---|---|---|---|
| Receber perguntas via input de texto | ✅ | CLI com `input()` em [`app/cli.py`](../services/chatbot/app/cli.py) (+ API `POST /api/v1/chat`) | `make chat` |
| Usar LangChain para gerenciar a conversa e integrar com o LLM | ✅ | [`app/chain.py`](../services/chatbot/app/chain.py): `prompt \| llm \| StrOutputParser` (LCEL) + memória por `session_id` | Ler `chain.py` |
| Responder com o modelo da OpenAI | ⚠️ | `LLM_PROVIDER=openai` (padrão, `ChatOpenAI`, modelo em `OPENAI_MODEL`); também `gemini` (plano gratuito) e `ollama` (local, sem chave) | O caminho OpenAI/Gemini **não foi exercitado** (sem chave); o Ollama foi, de ponta a ponta (seção 3) |
| Exemplo "Como criar uma lista em Python?" com explicação detalhada | ✅ | [`docs/chatbot_examples.md`](chatbot_examples.md) — resposta real, gerada pela aplicação | `make up-local` · `make pull-model` · `make chat` (com `LLM_PROVIDER=ollama`). Gerada por um modelo local (Qwen 3B), **não** pelo GPT (seção 3) |
| Configurar corretamente a API da OpenAI | ✅ | [`.env.example`](../.env.example), `core/config.py`; sem chave → erro `500` explícito, sem crash | `curl -X POST localhost:8002/api/v1/chat -H 'Content-Type: application/json' -d '{"session_id":"s","message":"oi"}'` sem chave → `500` com mensagem clara |
| LangSmith (título da questão) | ⚠️ | Ativado só por variáveis `LANGSMITH_*` no `.env` | Não validado com chave real (seção 3) |
| Exemplos de perguntas e respostas | ✅ | [`docs/chatbot_examples.md`](chatbot_examples.md) — 5 conversas reais (básica, conceitual, follow-up com memória, fora do escopo, avançada), com as imprecisões do modelo apontadas | Idem |
| Testes | ✅ | 24 testes com LLM fake (não chamam nenhum provedor), 97% de cobertura | `docker compose run --rm chatbot pytest --cov=app` |

### Questão 3 — `services/semantic_search`

| Requisito | Status | Onde | Como verificar |
|---|---|---|---|
| Conjunto de documentos de texto | ✅ | [`data/articles/articles.json`](../services/semantic_search/data/articles/articles.json) — 24 artigos em português, 6 temas | — |
| Gerar embeddings com um modelo de embeddings | ✅ | [`app/embeddings.py`](../services/semantic_search/app/embeddings.py) — `transformers` puro (tokenizer + modelo + mean pooling + normalização L2), modelo `paraphrase-multilingual-MiniLM-L12-v2` | `make ingest` |
| Armazenar em vector store (FAISS ou Milvus) | ✅ | [`app/vector_store.py`](../services/semantic_search/app/vector_store.py) — `FaissVectorStore` (`IndexFlatIP`) atrás do `Protocol` `VectorStore`; índice persistido em volume | `make ingest` cria `articles.faiss` + metadados |
| Função de busca por similaridade semântica | ✅ | [`app/search.py`](../services/semantic_search/app/search.py) · `GET /api/v1/search?q=&k=` | `curl "localhost:8003/api/v1/search?q=como%20fazer%20bolo&k=3"` → artigo de culinária em 1º |
| Dica: usar `transformers` | ✅ | Idem embeddings | — |
| Documentar criação dos embeddings e armazenamento | ✅ | [`docs/semantic_search.md`](semantic_search.md) | — |
| Demonstrar com consultas e resultados | ✅ | Tabela com resultados reais **e** casos em que a busca falha, em `docs/semantic_search.md` | Reproduzir as consultas da tabela |
| Testes | ✅ | 49 testes com o modelo real, 99% de cobertura | `docker compose run --rm semantic_search pytest --cov=app` |

## 3. Ressalvas e divergências (leia antes de validar)

1. **As respostas do chatbot não são do GPT.** Sem chave da OpenAI, os exemplos em
   [`chatbot_examples.md`](chatbot_examples.md) foram gerados **de verdade** pela aplicação, mas com o
   provedor local `ollama` e o modelo `qwen2.5:3b` (pequeno, em CPU) — transcritos sem edição,
   com as imprecisões técnicas do modelo apontadas no arquivo. O que **não foi exercitado** é
   o caminho com OpenAI e com Gemini (só o que não depende de chave foi testado: construção do
   cliente, seleção do provedor, erro `500` claro se faltar a chave). LangSmith idem.
   Quem tiver uma chave (a do Gemini é gratuita) pode regenerar os exemplos.
2. **GPT-4.** O enunciado cita GPT-4 como exemplo de LLM. O provedor é escolhido em
   `LLM_PROVIDER` e o modelo em `OPENAI_MODEL` (default `gpt-4o-mini`), porque nomes de modelo
   mudam com frequência;
   para usar GPT-4 basta trocar a variável, sem alterar código (não exercitado, pelo mesmo
   motivo do item 1).
3. **Memória do chatbot usa API deprecated** (`RunnableWithMessageHistory`). Escolha
   consciente e justificada em [`decisions.md`](decisions.md).
4. **Limitações da busca semântica** são mostradas, não escondidas: consultas de uma palavra
   ("bolo") e assuntos fora do corpus retornam resultados fracos (score baixo). Detalhes em
   [`semantic_search.md`](semantic_search.md).
5. **Além do pedido:** monorepo com Docker Compose, CI, migrations Alembic, camadas
   repository/service, lint/tipagem estrita. O enunciado não exige nada disso; foi feito por
   ser objetivo do estudo praticar engenharia além de "fazer funcionar".
