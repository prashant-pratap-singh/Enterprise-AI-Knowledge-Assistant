"""EvaluationRun ORM entity for storing RAG evaluation benchmarks."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.types import JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class EvaluationRun(Base, UUIDPrimaryKeyMixin):
    """Stores benchmark metrics and configuration for an automated RAG evaluation run."""

    __tablename__ = "evaluation_runs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="evaluation_runs",
    )
