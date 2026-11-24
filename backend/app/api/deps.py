"""FastAPI security dependencies: authentication, RBAC, and tenant workspace scoping."""

import uuid
from typing import Optional

try:
    from fastapi import Depends, Header, status
    from starlette.exceptions import HTTPException
except Exception:
    class Depends:  # type: ignore
        def __init__(self, dependency=None, use_cache=True):
            self.dependency = dependency
            self.use_cache = use_cache

    class Header:  # type: ignore
        def __init__(self, default=None, **kwargs):
            self.default = default

    from starlette import status  # type: ignore
    from starlette.exceptions import HTTPException  # type: ignore

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.organization import Membership
from app.db.models.workspace import Workspace
from app.core.security import decode_token
from app.repositories.user_repo import UserRepository
from app.repositories.organization_repo import OrganizationRepository
from app.repositories.workspace_repo import WorkspaceRepository

ROLE_HIERARCHY = {
    "VIEWER": 1,
    "EDITOR": 2,
    "ADMIN": 3,
}


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extracts and verifies JWT token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1].strip()
    try:
        claims = decode_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = claims.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get(uuid.UUID(user_id_str))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


class RequireRole:
    """Dependency verifying that the user holds at least min_role within the organization."""

    def __init__(self, min_role: str):
        self.min_role = min_role.upper()

    async def __call__(
        self,
        organization_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Membership:
        org_repo = OrganizationRepository(db)
        membership = await org_repo.get_membership(organization_id, user.id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this organization",
            )

        user_level = ROLE_HIERARCHY.get(membership.role.upper(), 0)
        required_level = ROLE_HIERARCHY.get(self.min_role, 3)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires minimum '{self.min_role}' role in this organization",
            )

        return membership


class RequireWorkspaceAccess:
    """Dependency verifying workspace existence and user authorization within workspace parent org."""

    def __init__(self, min_role: str = "VIEWER"):
        self.min_role = min_role.upper()

    async def __call__(
        self,
        workspace_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Workspace:
        ws_repo = WorkspaceRepository(db)
        workspace = await ws_repo.get(workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        org_repo = OrganizationRepository(db)
        membership = await org_repo.get_membership(workspace.organization_id, user.id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace's organization",
            )

        user_level = ROLE_HIERARCHY.get(membership.role.upper(), 0)
        required_level = ROLE_HIERARCHY.get(self.min_role, 1)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Workspace action requires '{self.min_role}' role",
            )

        return workspace
