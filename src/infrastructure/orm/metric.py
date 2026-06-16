"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    MetricSnapshot as MetricSnapshotDomain,
)

class MetricSnapshotORM(Base):
    """Modelo ORM para snapshots de métricas."""

    __tablename__ = "metric_snapshots"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(nullable=False)
    snapshot_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    team: Mapped["TeamORM"] = relationship(back_populates="metric_snapshots")

    def to_domain(self) -> MetricSnapshotDomain:
        return MetricSnapshotDomain(
            id=self.id,
            team_id=self.team_id,
            metric_type=self.metric_type,
            date=datetime.combine(self.date, datetime.min.time()),
            value=self.value,
            metadata=dict(self.snapshot_metadata or {}),
        )

    @classmethod
    def from_domain(cls, snapshot: MetricSnapshotDomain) -> "MetricSnapshotORM":
        return cls(
            id=snapshot.id,
            team_id=snapshot.team_id,
            metric_type=snapshot.metric_type,
            date=snapshot.date.date(),
            value=snapshot.value,
            snapshot_metadata=dict(snapshot.metadata or {}),
        )
