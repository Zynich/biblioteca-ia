# syntax=docker/dockerfile:1

# ---- Stage 1: builder — instala dependências com uv em um venv isolado ----
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# O uv.lock já fixa o torch da build CPU-only (índice pytorch-cpu definido no
# pyproject.toml): evita baixar as libs CUDA e reduz a imagem em vários GB.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY app ./app
COPY tests ./tests
RUN uv sync --frozen

# ---- Stage 2: runtime — usuário não-root ----
# Mantém dev-dependencies no runtime pelo mesmo motivo documentado em
# services/books_api/Dockerfile e docs/decisions.md.
FROM python:3.12-slim AS runtime

# libgomp1: runtime do OpenMP exigido pelo faiss-cpu (não vem na imagem slim).
RUN apt-get update && apt-get install -y --no-install-recommends curl libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --chown=appuser:appuser --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser --from=builder /app/app ./app
COPY --chown=appuser:appuser --from=builder /app/tests ./tests
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser data ./data

# HF_HOME fora de /root: o container roda como appuser. O diretório existe (e pertence ao
# appuser) na imagem para que o volume nomeado hf_cache herde essas permissões.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface

RUN mkdir -p /app/index /app/.cache/huggingface \
    && chown -R appuser:appuser /app/index /app/.cache && chown appuser:appuser /app

USER appuser

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
