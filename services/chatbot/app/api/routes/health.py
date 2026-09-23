"""Health check consumido pelo HEALTHCHECK do Dockerfile e pelo docker-compose."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
