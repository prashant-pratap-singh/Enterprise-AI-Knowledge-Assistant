"""Organization and membership management endpoints."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user, RequireRole
from app.repositories.organization_repo import OrganizationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    OrganizationCreateRequest,
    OrganizationResponse,
    MemberAddRequest,
    MembershipResponse,
)

router = APIRouter()


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """Create a new organization and assign the authenticated creator as ADMIN."""
    org_repo = OrganizationRepository(db)
    org = await org_repo.create_organization(payload.name)
    await org_repo.add_member(
        organization_id=org.id,
        user_id=current_user.id,
        role="ADMIN",
    )
    return OrganizationResponse.model_validate(org)


@router.get("", response_model=List[OrganizationResponse], status_code=status.HTTP_200_OK)
async def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrganizationResponse]:
    """List all organizations the authenticated user belongs to."""
    org_repo = OrganizationRepository(db)
    orgs = await org_repo.list_user_organizations(current_user.id)
    return [OrganizationResponse.model_validate(o) for o in orgs]


@router.get("/{organization_id}/members", response_model=List[MembershipResponse], status_code=status.HTTP_200_OK)
async def list_organization_members(
    organization_id: uuid.UUID,
    membership=Depends(RequireRole("VIEWER")),
    db: AsyncSession = Depends(get_db),
) -> List[MembershipResponse]:
    """List members belonging to an organization (requires VIEWER role)."""
    org_repo = OrganizationRepository(db)
    members = await org_repo.list_members(organization_id)
    return [MembershipResponse.model_validate(m) for m in members]


@router.post("/{organization_id}/members", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    organization_id: uuid.UUID,
    payload: MemberAddRequest,
    membership=Depends(RequireRole("ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> MembershipResponse:
    """Add a user to the organization with a specific role (requires ADMIN role)."""
    user_repo = UserRepository(db)
    target_user = await user_repo.get_by_email(payload.email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{payload.email}' not found. The user must register first.",
        )

    org_repo = OrganizationRepository(db)
    existing = await org_repo.get_membership(organization_id, target_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User is already a member with role '{existing.role}'",
        )

    new_member = await org_repo.add_member(
        organization_id=organization_id,
        user_id=target_user.id,
        role=payload.role,
    )
    return MembershipResponse.model_validate(new_member)
