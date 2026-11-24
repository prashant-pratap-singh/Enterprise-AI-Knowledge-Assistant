"""Generic async repository pattern for SQLAlchemy models."""

import uuid
from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing standardized async CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """Fetch entity by primary key UUID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """List entities with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total entities in table."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def create(self, entity: ModelType) -> ModelType:
        """Add new entity and flush."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete entity by ID triggering ORM relationships and cascade rules."""
        entity = await self.get(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False
