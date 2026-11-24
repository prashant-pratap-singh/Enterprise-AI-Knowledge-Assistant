"""Pydantic schemas for authentication, authorization, and organization membership."""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    """Payload for new user registration."""
    email: str = Field(..., description="Valid corporate email address", min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of user")


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Standardized JWT authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Payload to refresh an access token."""
    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile schema."""
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationCreateRequest(BaseModel):
    """Payload for creating a new organization."""
    name: str = Field(..., min_length=2, max_length=255)


class OrganizationResponse(BaseModel):
    """Organization schema."""
    id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MemberAddRequest(BaseModel):
    """Payload for adding or inviting a member to an organization."""
    email: str = Field(..., min_length=5, max_length=255)
    role: str = Field(default="VIEWER", pattern="^(ADMIN|EDITOR|VIEWER)$")


class MembershipResponse(BaseModel):
    """Organization membership schema with user and role details."""
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
