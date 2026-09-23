# syntax=docker/dockerfile:1

# ---- Stage 1: builder — instala dependências com uv em um venv isolado ----
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml ./
RUN uv sync --no-install-project

COPY app ./app
COPY tests ./tests
RUN uv sync

# ---- Stage 2: runtime — imagem final, usuário não-root ----
# Mantém dev-dependencies no runtime pelo mesmo motivo documentado em
# services/books_api/Dockerfile e docs/decisions.md.
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/tests ./tests
COPY pyproject.toml ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
