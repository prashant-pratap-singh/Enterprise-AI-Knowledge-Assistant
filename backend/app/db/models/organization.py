"""Organization and Membership ORM entities for multi-tenancy and RBAC."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.workspace import Workspace
    from app.db.models.evaluation import EvaluationRun


class Organization(Base, UUIDPrimaryKeyMixin):
    """Organization entity serving as the primary multi-tenant boundary."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    memberships: Mapped[List["Membership"]] = relationship(
        "Membership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    evaluation_runs: Mapped[List["EvaluationRun"]] = relationship(
        "EvaluationRun",
        back_populates="organization",
        cascade="all, delete-orphan",
    )


class Membership(Base, UUIDPrimaryKeyMixin):
    """Associates a User with an Organization and assigns an RBAC role."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="VIEWER",
        nullable=False,
    )  # "ADMIN", "EDITOR", "VIEWER"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="memberships",
    )
