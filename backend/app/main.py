"""Main FastAPI application entry point for Enterprise AI Knowledge Assistant."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import EnterpriseRAGException
from app.api.v1 import api_router
from app.api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    # Setup structured logging
    setup_logging(log_level=settings.LOG_LEVEL, json_logs=(settings.ENVIRONMENT == "production"))
    logger.info(
        f"Starting {settings.APP_NAME} in [{settings.ENVIRONMENT}] mode "
        f"with ChromaDB mode: {settings.CHROMA_MODE}"
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Full-stack enterprise RAG application with multi-agent orchestration using LangGraph.",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for domain exceptions
@app.exception_handler(EnterpriseRAGException)
async def enterprise_rag_exception_handler(
    request: Request, exc: EnterpriseRAGException
) -> JSONResponse:
    logger.error(f"Application error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.message, "details": exc.details},
    )


# Include API v1 routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level health checks for container orchestrators (Cloud Run / K8s)
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "0.1.0",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
        "api_v1": settings.API_V1_STR,
    }
