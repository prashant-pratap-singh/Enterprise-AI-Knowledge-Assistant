"""Authentication and account lifecycle service."""

import uuid
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import (
    DuplicateEntityException,
    EntityNotFoundException,
    PermissionDeniedException,
)
from app.db.models.user import User
from app.db.models.organization import Organization, Membership
from app.repositories.user_repo import UserRepository
from app.repositories.organization_repo import OrganizationRepository


class AuthService:
    """Handles user registration, authentication, tokens, and default organization setup."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: Optional[str] = None,
    ) -> Tuple[User, Organization, str, str]:
        """
        Registers a new user, optionally creates an initial organization,
        assigns the user as ADMIN of that organization, and issues tokens.
        """
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise DuplicateEntityException(f"User with email '{email}' already exists.")

        hashed = hash_password(password)
        user = await self.user_repo.create_user(
            email=email,
            hashed_password=hashed,
            full_name=full_name,
            is_active=True,
        )

        # Create default organization for new user if specified or default
        org_name = organization_name.strip() if organization_name else f"{full_name}'s Organization"
        org = await self.org_repo.create_organization(name=org_name)
        await self.org_repo.add_member(
            organization_id=org.id,
            user_id=user.id,
            role="ADMIN",
        )

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "org_id": str(org.id)},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return user, org, access_token, refresh_token

    async def login(
        self,
        email: str,
        password: str,
    ) -> Tuple[User, str, str]:
        """Authenticate user by email and password, returning tokens."""
        user = await self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            raise PermissionDeniedException("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            raise PermissionDeniedException("Invalid email or password.")

        # Find primary organization if any
        orgs = await self.org_repo.list_user_organizations(user.id)
        org_id = str(orgs[0].id) if orgs else None

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "org_id": org_id},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> Tuple[str, str]:
        """Validate refresh token and issue a fresh token pair."""
        try:
            claims = decode_token(refresh_token)
        except Exception:
            raise PermissionDeniedException("Invalid or expired refresh token.")

        if claims.get("type") != "refresh":
            raise PermissionDeniedException("Token is not a refresh token.")

        user_id_str = claims.get("sub")
        if not user_id_str:
            raise PermissionDeniedException("Malformed token claims.")

        user = await self.user_repo.get(uuid.UUID(user_id_str))
        if not user or not user.is_active:
            raise PermissionDeniedException("User is inactive or not found.")

        orgs = await self.org_repo.list_user_organizations(user.id)
        org_id = str(orgs[0].id) if orgs else None

        new_access = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "org_id": org_id},
        )
        new_refresh = create_refresh_token(subject=str(user.id))

        return new_access, new_refresh
