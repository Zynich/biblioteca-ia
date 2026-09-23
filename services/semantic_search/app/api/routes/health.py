"""Health check consumido pelo HEALTHCHECK do Dockerfile e pelo docker-compose."""

from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health() -> dict[str, str | bool]:
    # Não carrega o modelo: o healthcheck precisa ser barato. `index_ready` indica se a
    # ingestão já foi executada.
    index_ready = Path(settings.faiss_index_path).exists()
    return {"status": "ok", "index_ready": index_ready}
