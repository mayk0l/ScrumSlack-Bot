"""Módulo ORM."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base

from src.domain.models import (
    Member as MemberDomain,
    MemberRole,
)

class MemberORM(Base):
    """Modelo ORM para miembros de un equipo."""

    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("team_id", "slack_user_id"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    slack_user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=MemberRole.DEVELOPER.value)

    team: Mapped["TeamORM"] = relationship(back_populates="members")
    standup_responses: Mapped[list["StandupResponseORM"]] = relationship(back_populates="member")

    def to_domain(self) -> MemberDomain:
        return MemberDomain(
            id=self.id,
            team_id=self.team_id,
            slack_user_id=self.slack_user_id,
            display_name=self.display_name,
            role=MemberRole(self.role),
        )

    @classmethod
    def from_domain(cls, member: MemberDomain) -> "MemberORM":
        return cls(
            id=member.id,
            team_id=member.team_id,
            slack_user_id=member.slack_user_id,
            display_name=member.display_name,
            role=member.role.value,
        )
