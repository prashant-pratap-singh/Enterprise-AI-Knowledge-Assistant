"""Workspace repository for managing knowledge partitions."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workspace import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Data operations for Workspaces scoped by organization."""

    def __init__(self, session: AsyncSession):
        super().__init__(Workspace, session)

    async def create_workspace(
        self,
        organization_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
    ) -> Workspace:
        """Create a workspace within an organization."""
        workspace = Workspace(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=name.strip(),
            description=description,
        )
        return await self.create(workspace)

    async def get_by_org_and_name(
        self,
        organization_id: uuid.UUID,
        name: str,
    ) -> Optional[Workspace]:
        """Fetch workspace by organization and name."""
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.organization_id == organization_id,
                Workspace.name == name.strip(),
            )
        )
        return result.scalars().first()

    async def list_for_organization(
        self,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Workspace]:
        """List all workspaces within an organization."""
        result = await self.session.execute(
            select(Workspace)
            .where(Workspace.organization_id == organization_id)
            .order_by(Workspace.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
