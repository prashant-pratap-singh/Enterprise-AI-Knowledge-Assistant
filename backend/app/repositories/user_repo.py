"""User repository for authentication and account queries."""

import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data operations for the User entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by case-insensitive email address."""
        result = await self.session.execute(
            select(User).where(User.email == email.strip().lower())
        )
        return result.scalars().first()

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        is_active: bool = True,
    ) -> User:
        """Create and persist a new user."""
        user = User(
            id=uuid.uuid4(),
            email=email.strip().lower(),
            hashed_password=hashed_password,
            full_name=full_name.strip(),
            is_active=is_active,
        )
        return await self.create(user)
