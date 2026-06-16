"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    Sprint as SprintDomain,
    SprintStatus,
)

class SprintORM(Base):
    """Modelo ORM para sprints."""

    __tablename__ = "sprints"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SprintStatus.PLANNING.value,
    )
    goals: Mapped[str] = mapped_column(String(1000), default="")

    team: Mapped["TeamORM"] = relationship(back_populates="sprints")
    standup_sessions: Mapped[list["StandupSessionORM"]] = relationship(back_populates="sprint")

    def to_domain(self) -> SprintDomain:
        return SprintDomain(
            id=self.id,
            team_id=self.team_id,
            name=self.name,
            start_date=datetime.combine(self.start_date, datetime.min.time()),
            end_date=datetime.combine(self.end_date, datetime.min.time()),
            status=SprintStatus(self.status),
            goals=self.goals,
        )

    @classmethod
    def from_domain(cls, sprint: SprintDomain) -> "SprintORM":
        return cls(
            id=sprint.id,
            team_id=sprint.team_id,
            name=sprint.name,
            start_date=sprint.start_date.date(),
            end_date=sprint.end_date.date(),
            status=sprint.status.value,
            goals=sprint.goals,
        )
