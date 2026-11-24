"""Workspace ORM entity."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.document import Document
    from app.db.models.conversation import Conversation


class Workspace(Base, UUIDPrimaryKeyMixin):
    """Logical knowledge partition within an Organization."""

    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_organization_workspace_name"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="workspaces",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
