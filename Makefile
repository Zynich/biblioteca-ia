.PHONY: up up-local pull-model down build logs test lint fmt ingest chat

up: ## Sobe os 3 serviços em background
	docker compose up -d --build

up-local: ## Sobe os serviços + Ollama (LLM local, sem chave de API)
	docker compose --profile local-llm up -d --build

pull-model: ## Baixa o modelo do Ollama (OLLAMA_MODEL do .env; default qwen2.5:3b)
	docker compose --profile local-llm exec ollama ollama pull $${OLLAMA_MODEL:-$$(grep -E '^OLLAMA_MODEL=' .env | cut -d= -f2)}

down: ## Derruba os serviços e remove os containers
	docker compose --profile local-llm down

build: ## Rebuild das imagens sem subir
	docker compose build

logs: ## Segue os logs de todos os serviços
	docker compose logs -f

test: ## Roda os testes de cada serviço (dentro dos containers)
	docker compose run --rm books_api pytest
	docker compose run --rm chatbot pytest
	docker compose run --rm semantic_search pytest

lint: ## Roda ruff + mypy em cada serviço
	docker compose run --rm books_api sh -c "ruff check . && mypy app"
	docker compose run --rm chatbot sh -c "ruff check . && mypy app"
	docker compose run --rm semantic_search sh -c "ruff check . && mypy app"

fmt: ## Formata o código com ruff
	docker compose run --rm books_api ruff format .
	docker compose run --rm chatbot ruff format .
	docker compose run --rm semantic_search ruff format .

ingest: ## Gera embeddings e constrói o índice FAISS (Questão 3)
	docker compose run --rm semantic_search python -m app.ingest

chat: ## Abre o chatbot em modo CLI (Questão 2)
	docker compose run --rm chatbot python -m app.cli
