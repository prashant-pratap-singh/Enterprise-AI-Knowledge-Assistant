"""Application configuration management using Pydantic Settings."""

import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "Enterprise AI Knowledge Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "default-insecure-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database (PostgreSQL)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "enterprise_knowledge"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/enterprise_knowledge"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_knowledge"

    # Vector Database (ChromaDB)
    CHROMA_MODE: str = "local"  # "local" or "http"
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # AI & Embedding Providers
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_FLASH_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_PROVIDER: str = "google"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_DIMENSIONS: int = 768

    # Storage
    STORAGE_BACKEND: str = "local"  # "local" or "gcs"
    LOCAL_STORAGE_DIR: str = "./storage/documents"
    GCS_BUCKET_NAME: str = ""

    # Ingestion & Chunking
    MAX_UPLOAD_SIZE_MB: int = 25
    DEFAULT_CHUNK_SIZE_TOKENS: int = 1000
    DEFAULT_CHUNK_OVERLAP_TOKENS: int = 150
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
    ]

    # Retrieval & LangGraph Orchestration
    RETRIEVAL_TOP_K: int = 8
    HYBRID_SEARCH_ALPHA: float = 0.6  # Weight for vector search vs lexical FTS in RRF
    RELEVANCE_SCORE_THRESHOLD: float = 0.45
    MAX_CONTEXT_TOKENS: int = 4000
    MAX_AGENT_RETRIES: int = 2
    RERANKING_ENABLED: bool = False

    # Redis Cache (Optional)
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
