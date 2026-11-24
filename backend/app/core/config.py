"""Application configuration management with Pydantic Settings and pure-Python fallback."""

import os
from typing import List, Union

try:
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _PYDANTIC_AVAILABLE = True
except (ImportError, Exception):
    _PYDANTIC_AVAILABLE = False
    BaseSettings = object  # type: ignore
    SettingsConfigDict = dict  # type: ignore


if _PYDANTIC_AVAILABLE:
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
        HYBRID_SEARCH_ALPHA: float = 0.6
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

else:
    # Pure-Python fallback for restricted Windows environments
    class PurePythonSettings:
        def __init__(self):
            # Load .env manually if exists
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

            self.APP_NAME: str = os.getenv("APP_NAME", "Enterprise AI Knowledge Assistant")
            self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
            self.DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
            self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
            self.API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
            self.HOST: str = os.getenv("HOST", "0.0.0.0")
            self.PORT: int = int(os.getenv("PORT", "8000"))

            self.SECRET_KEY: str = os.getenv("SECRET_KEY", "default-insecure-secret-key-change-in-production-min-32-chars")
            self.ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
            self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
            self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

            raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
            self.CORS_ORIGINS: List[str] = [i.strip() for i in raw_cors.split(",") if i.strip()]

            self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
            self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
            self.POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
            self.POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
            self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "enterprise_knowledge")
            self.DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/enterprise_knowledge")
            self.ASYNC_DATABASE_URL: str = os.getenv("ASYNC_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_knowledge")

            self.CHROMA_MODE: str = os.getenv("CHROMA_MODE", "local")
            self.CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_data")
            self.CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
            self.CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8001"))

            self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
            self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
            self.GEMINI_FLASH_MODEL: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash")
            self.EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "google")
            self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
            self.EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

            self.STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
            self.LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "./storage/documents")
            self.GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")

            self.MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
            self.DEFAULT_CHUNK_SIZE_TOKENS: int = int(os.getenv("DEFAULT_CHUNK_SIZE_TOKENS", "1000"))
            self.DEFAULT_CHUNK_OVERLAP_TOKENS: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP_TOKENS", "150"))
            self.ALLOWED_MIME_TYPES: List[str] = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain",
                "text/csv",
            ]

            self.RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "8"))
            self.HYBRID_SEARCH_ALPHA: float = float(os.getenv("HYBRID_SEARCH_ALPHA", "0.6"))
            self.RELEVANCE_SCORE_THRESHOLD: float = float(os.getenv("RELEVANCE_SCORE_THRESHOLD", "0.45"))
            self.MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
            self.MAX_AGENT_RETRIES: int = int(os.getenv("MAX_AGENT_RETRIES", "2"))
            self.RERANKING_ENABLED: bool = os.getenv("RERANKING_ENABLED", "false").lower() in ("true", "1", "yes")

            self.REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    settings = PurePythonSettings()
