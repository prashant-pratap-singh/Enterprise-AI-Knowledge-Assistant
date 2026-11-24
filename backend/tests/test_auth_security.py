"""Unit and security tests for authentication, password hashing, JWT tokens, and RBAC."""

import uuid
from datetime import timedelta
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
try:
    from fastapi import HTTPException
except Exception:
    from starlette.exceptions import HTTPException

from app.db.base import Base
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.auth_service import AuthService
from app.core.exceptions import DuplicateEntityException, PermissionDeniedException
from app.api.deps import RequireRole, ROLE_HIERARCHY
from app.repositories.organization_repo import OrganizationRepository
from app.repositories.user_repo import UserRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_session():
    """Provides an isolated database session for each auth test."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


def test_password_hashing_and_verification():
    """Verify password hashing produces unreadable hashes and validates correctly."""
    plain = "SuperSecurePassword#2026"
    hashed = hash_password(plain)

    assert hashed != plain
    assert not hashed.startswith(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_token_lifecycle_and_tamper_protection():
    """Verify JWT generation, claim parsing, expiration, and cryptographic signature check."""
    user_id = str(uuid.uuid4())
    access_token = create_access_token(
        subject=user_id,
        extra_claims={"email": "sde@company.com", "role": "ADMIN"},
    )
    claims = decode_token(access_token)
    assert claims["sub"] == user_id
    assert claims["email"] == "sde@company.com"
    assert claims["type"] == "access"

    # Test refresh token
    refresh_token = create_refresh_token(subject=user_id)
    refresh_claims = decode_token(refresh_token)
    assert refresh_claims["sub"] == user_id
    assert refresh_claims["type"] == "refresh"

    # Test expired token
    expired_token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    with pytest.raises(ValueError, match="expired"):
        decode_token(expired_token)

    # Test tampered payload
    parts = access_token.split(".")
    tampered_token = f"{parts[0]}.eyJhZG1pbiI6dHJ1ZX0.{parts[2]}"
    with pytest.raises(ValueError, match="signature"):
        decode_token(tampered_token)


@pytest.mark.asyncio
async def test_auth_service_registration_and_login(test_session: AsyncSession):
    """Verify complete registration, default org assignment, and credential check."""
    service = AuthService(test_session)

    # 1. Register new user
    user, org, access_token, refresh_token = await service.register(
        email="lead@enterprise.com",
        password="MySecretPassword123!",
        full_name="Lead Engineer",
        organization_name="Core Infra Corp",
    )
    assert user.id is not None
    assert user.email == "lead@enterprise.com"
    assert org.name == "Core Infra Corp"
    assert access_token is not None

    # Check user is admin of created organization
    org_repo = OrganizationRepository(test_session)
    membership = await org_repo.get_membership(org.id, user.id)
    assert membership is not None
    assert membership.role == "ADMIN"

    # 2. Reject duplicate registration
    with pytest.raises(DuplicateEntityException):
        await service.register(
            email="lead@enterprise.com",
            password="AnotherPassword456!",
            full_name="Duplicate Attempt",
        )

    # 3. Successful login
    logged_user, login_access, login_refresh = await service.login(
        email="lead@enterprise.com",
        password="MySecretPassword123!",
    )
    assert logged_user.id == user.id
    assert login_access is not None

    # 4. Reject invalid password
    with pytest.raises(PermissionDeniedException):
        await service.login(
            email="lead@enterprise.com",
            password="WrongPassword!",
        )


@pytest.mark.asyncio
async def test_auth_service_token_refresh(test_session: AsyncSession):
    """Verify refresh token exchange for new access and refresh tokens."""
    service = AuthService(test_session)
    user, org, access_token, refresh_token = await service.register(
        email="refresher@enterprise.com",
        password="Password123456",
        full_name="Token Refresher",
    )

    new_access, new_refresh = await service.refresh(refresh_token)
    assert new_access is not None
    assert new_refresh is not None

    claims = decode_token(new_access)
    assert claims["sub"] == str(user.id)

    # Attempt refresh with an access token (must be rejected)
    with pytest.raises(PermissionDeniedException):
        await service.refresh(access_token)


@pytest.mark.asyncio
async def test_rbac_permissions_hierarchy(test_session: AsyncSession):
    """Verify role-based access control enforces ADMIN, EDITOR, and VIEWER privileges."""
    user_repo = UserRepository(test_session)
    org_repo = OrganizationRepository(test_session)

    org = await org_repo.create_organization("RBAC Enterprise")

    # Create users with different roles
    admin = await user_repo.create_user("admin@rbac.com", "hash", "Admin User")
    editor = await user_repo.create_user("editor@rbac.com", "hash", "Editor User")
    viewer = await user_repo.create_user("viewer@rbac.com", "hash", "Viewer User")
    outsider = await user_repo.create_user("outsider@rbac.com", "hash", "Outsider User")

    await org_repo.add_member(org.id, admin.id, "ADMIN")
    await org_repo.add_member(org.id, editor.id, "EDITOR")
    await org_repo.add_member(org.id, viewer.id, "VIEWER")

    admin_checker = RequireRole("ADMIN")
    editor_checker = RequireRole("EDITOR")
    viewer_checker = RequireRole("VIEWER")

    # 1. Admin checks (should succeed for ADMIN, EDITOR, and VIEWER operations)
    admin_mem = await admin_checker(org.id, user=admin, db=test_session)
    assert admin_mem.role == "ADMIN"
    assert (await editor_checker(org.id, user=admin, db=test_session)).role == "ADMIN"
    assert (await viewer_checker(org.id, user=admin, db=test_session)).role == "ADMIN"

    # 2. Editor checks (should succeed for EDITOR and VIEWER, fail for ADMIN)
    assert (await editor_checker(org.id, user=editor, db=test_session)).role == "EDITOR"
    assert (await viewer_checker(org.id, user=editor, db=test_session)).role == "EDITOR"
    with pytest.raises(HTTPException) as exc_info:
        await admin_checker(org.id, user=editor, db=test_session)
    assert exc_info.value.status_code == 403

    # 3. Viewer checks (should succeed for VIEWER, fail for EDITOR and ADMIN)
    assert (await viewer_checker(org.id, user=viewer, db=test_session)).role == "VIEWER"
    with pytest.raises(HTTPException) as exc_info:
        await editor_checker(org.id, user=viewer, db=test_session)
    assert exc_info.value.status_code == 403

    # 4. Outsider checks (not a member of the organization -> 403)
    with pytest.raises(HTTPException) as exc_info:
        await viewer_checker(org.id, user=outsider, db=test_session)
    assert exc_info.value.status_code == 403
