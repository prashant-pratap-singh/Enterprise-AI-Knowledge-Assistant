"""Health and readiness check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Liveness probe returning application running status."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version="0.1.0",
    )


@router.get("/health/ready", response_model=ReadinessResponse, status_code=status.HTTP_200_OK)
async def readiness_check() -> ReadinessResponse:
    """Readiness probe checking readiness for traffic."""
    # In Phase 1, basic services readiness
    checks: Dict[str, Any] = {
        "api": "ready",
        "chroma_mode": settings.CHROMA_MODE,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "storage_backend": settings.STORAGE_BACKEND,
    }
    return ReadinessResponse(status="ready", checks=checks)
