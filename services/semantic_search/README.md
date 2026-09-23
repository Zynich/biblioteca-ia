# semantic_search — Questão 3

Busca semântica de documentos: embeddings (`transformers` puro) + FAISS + FastAPI.
Explicação detalhada do pipeline, exemplos reais e limitações em
[docs/semantic_search.md](../../docs/semantic_search.md).

## Uso (via Docker Compose, na raiz do repositório)

```bash
cp .env.example .env
make up        # sobe a API (porta 8003)
make ingest    # gera embeddings dos 24 artigos e persiste o índice FAISS
```

Enquanto a ingestão não roda, `GET /api/v1/search` responde `503` e `/health` mostra
`"index_ready": false`. Depois do `make ingest` **não é preciso reiniciar a API**: ela
detecta que o índice mudou em disco e o recarrega.

```bash
curl "http://localhost:8003/api/v1/search?q=como%20fazer%20bolo&k=3"
```

```json
{
  "query": "como fazer bolo",
  "results": [
    {"doc_id": "culinaria-01", "title": "Receita de bolo de cenoura com cobertura de chocolate", "score": 0.744, "snippet": "..."},
    {"doc_id": "culinaria-02", "title": "Como fazer pão caseiro sem sova", "score": 0.563, "snippet": "..."}
  ]
}
```

Swagger: http://localhost:8003/docs

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/search?q=&k=5` | Top-`k` documentos (1 ≤ k ≤ 20) por similaridade de cosseno |
| GET | `/health` | Status + se o índice já existe |

## Rodando localmente (sem Docker)

```bash
cd services/semantic_search
uv sync
uv run python -m app.ingest         # exit code 0 = ok, 1 = falha
uv run uvicorn app.main:app --reload
```

O primeiro uso baixa o modelo (~470 MB) do Hugging Face; no Docker ele fica no volume `hf_cache`.

## Testes

```bash
uv run pytest --cov=app --cov-report=term-missing
```

49 testes, ~99% de cobertura. Usam o **modelo real** (baixado uma vez e reaproveitado do
cache do HF) e o dataset real: dimensão 384, norma ≈ 1, padding não altera o vetor,
`"como fazer bolo"` → artigo de culinária no top-1 (e outras 6 consultas), persistência
(salvar → recarregar → mesmo resultado), recarga do índice quando outro processo o
regrava, chunking (sobreposição, palavras não cortadas), vector store, ingestão (exit codes)
e API (422/503).
