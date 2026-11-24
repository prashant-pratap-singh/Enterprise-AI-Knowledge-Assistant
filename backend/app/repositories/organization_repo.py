"""Organization repository for tenancy and membership operations."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.organization import Organization, Membership
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Data operations for Organizations and multi-tenant Memberships."""

    def __init__(self, session: AsyncSession):
        super().__init__(Organization, session)

    async def create_organization(self, name: str) -> Organization:
        """Create a new organization."""
        org = Organization(id=uuid.uuid4(), name=name.strip())
        return await self.create(org)

    async def add_member(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "VIEWER",
    ) -> Membership:
        """Add a member to an organization with a specific role."""
        membership = Membership(
            id=uuid.uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            role=role.upper(),
        )
        self.session.add(membership)
        await self.session.flush()
        await self.session.refresh(membership)
        return membership

    async def get_membership(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Membership]:
        """Fetch user membership within a specific organization."""
        result = await self.session.execute(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def list_user_organizations(self, user_id: uuid.UUID) -> List[Organization]:
        """List all organizations that a user belongs to."""
        result = await self.session.execute(
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_members(self, organization_id: uuid.UUID) -> List[Membership]:
        """List all members belonging to an organization."""
        result = await self.session.execute(
            select(Membership)
            .options(selectinload(Membership.user))
            .where(Membership.organization_id == organization_id)
        )
        return list(result.scalars().all())
