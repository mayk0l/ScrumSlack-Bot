"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    Risk as RiskDomain,
    RiskType,
    Severity,
)

class RiskORM(Base):
    """Modelo ORM para riesgos detectados."""

    __tablename__ = "risks"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ref: Mapped[dict] = mapped_column(JSONB, default=dict)
    resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    team: Mapped["TeamORM"] = relationship(back_populates="risks")

    def to_domain(self) -> RiskDomain:
        return RiskDomain(
            id=self.id,
            team_id=self.team_id,
            type=RiskType(self.type),
            description=self.description,
            severity=Severity(self.severity),
            source_ref=dict(self.source_ref or {}),
            resolved=self.resolved,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, risk: RiskDomain) -> "RiskORM":
        return cls(
            id=risk.id,
            team_id=risk.team_id,
            type=risk.type.value,
            description=risk.description,
            severity=risk.severity.value,
            source_ref=dict(risk.source_ref or {}),
            resolved=risk.resolved,
            created_at=risk.created_at,
        )
