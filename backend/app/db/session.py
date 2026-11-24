"""Async database engine and session management."""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Engine configuration with resilient initialization
try:
    engine: Optional[AsyncEngine] = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
except Exception:
    engine = None
    async_session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator yielding an active async database session."""
    if async_session_factory is None:
        raise RuntimeError("Database session factory is not initialized. Verify database driver and connection URL.")

    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
