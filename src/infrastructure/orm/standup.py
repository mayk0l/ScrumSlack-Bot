"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    StandupSession as StandupSessionDomain,
    SessionStatus,
    StandupResponse as StandupResponseDomain,
)

class StandupSessionORM(Base):
    """Modelo ORM para sesiones de standup."""

    __tablename__ = "standup_sessions"
    __table_args__ = (
        UniqueConstraint("team_id", "date"),
        {"comment": "Índice para búsqueda por equipo y fecha"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    sprint_id: Mapped[UUID | None] = mapped_column(ForeignKey("sprints.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SessionStatus.OPEN.value,
    )
    slack_channel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    slack_thread_ts: Mapped[str] = mapped_column(String(50), default="")

    team: Mapped["TeamORM"] = relationship(back_populates="standup_sessions")
    sprint: Mapped["SprintORM" | None] = relationship(back_populates="standup_sessions")
    responses: Mapped[list["StandupResponseORM"]] = relationship(back_populates="session")

    def to_domain(self) -> StandupSessionDomain:
        return StandupSessionDomain(
            id=self.id,
            team_id=self.team_id,
            sprint_id=self.sprint_id,
            date=datetime.combine(self.date, datetime.min.time()),
            status=SessionStatus(self.status),
            slack_channel_id=self.slack_channel_id,
            slack_thread_ts=self.slack_thread_ts,
        )

    @classmethod
    def from_domain(cls, session: StandupSessionDomain) -> "StandupSessionORM":
        return cls(
            id=session.id,
            team_id=session.team_id,
            sprint_id=session.sprint_id,
            date=session.date.date(),
            status=session.status.value,
            slack_channel_id=session.slack_channel_id,
            slack_thread_ts=session.slack_thread_ts,
        )



class StandupResponseORM(Base):
    """Modelo ORM para respuestas de standup."""

    __tablename__ = "standup_responses"
    __table_args__ = (UniqueConstraint("session_id", "member_id"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    session_id: Mapped[UUID] = mapped_column(ForeignKey("standup_sessions.id"), nullable=False)
    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    yesterday: Mapped[str] = mapped_column(String(2000), nullable=False)
    today: Mapped[str] = mapped_column(String(2000), nullable=False)
    blockers: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    session: Mapped["StandupSessionORM"] = relationship(back_populates="responses")
    member: Mapped["MemberORM"] = relationship(back_populates="standup_responses")

    def to_domain(self) -> StandupResponseDomain:
        return StandupResponseDomain(
            id=self.id,
            session_id=self.session_id,
            member_id=self.member_id,
            yesterday=self.yesterday,
            today=self.today,
            blockers=self.blockers,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, response: StandupResponseDomain) -> "StandupResponseORM":
        return cls(
            id=response.id,
            session_id=response.session_id,
            member_id=response.member_id,
            yesterday=response.yesterday,
            today=response.today,
            blockers=response.blockers,
            created_at=response.created_at,
        )
