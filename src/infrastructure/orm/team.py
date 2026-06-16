"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    Team as TeamDomain,
)

class TeamORM(Base):
    """Modelo ORM para equipos."""

    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slack_bot_token: Mapped[str] = mapped_column(String(255), nullable=False)
    github_token: Mapped[str] = mapped_column(String(255), nullable=False)
    standup_channel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    standup_schedule_time: Mapped[str] = mapped_column(String(5), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Santiago")

    members: Mapped[list["MemberORM"]] = relationship(back_populates="team")
    sprints: Mapped[list["SprintORM"]] = relationship(back_populates="team")
    standup_sessions: Mapped[list["StandupSessionORM"]] = relationship(back_populates="team")
    pull_requests: Mapped[list["PullRequestORM"]] = relationship(back_populates="team")
    issues: Mapped[list["IssueORM"]] = relationship(back_populates="team")
    risks: Mapped[list["RiskORM"]] = relationship(back_populates="team")
    metric_snapshots: Mapped[list["MetricSnapshotORM"]] = relationship(back_populates="team")

    def to_domain(self) -> TeamDomain:
        return TeamDomain(
            id=self.id,
            name=self.name,
            slack_bot_token=self.slack_bot_token,
            github_token=self.github_token,
            standup_channel_id=self.standup_channel_id,
            standup_schedule_time=self.standup_schedule_time,
            timezone=self.timezone,
        )

    @classmethod
    def from_domain(cls, team: TeamDomain) -> "TeamORM":
        return cls(
            id=team.id,
            name=team.name,
            slack_bot_token=team.slack_bot_token,
            github_token=team.github_token,
            standup_channel_id=team.standup_channel_id,
            standup_schedule_time=team.standup_schedule_time,
            timezone=team.timezone,
        )
