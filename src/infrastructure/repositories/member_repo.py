"""Módulo: member_repo.

Implementación concreta del repositorio de miembros con SQLAlchemy async.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import Member
from src.domain.repositories import MemberRepository
from src.infrastructure.orm_models import MemberORM


class MemberRepositoryImpl(MemberRepository):
    """Repositorio de miembros usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, member_id: UUID) -> Member | None:
        """Obtiene un miembro por su ID."""
        result = await self._session.get(MemberORM, member_id)
        return result.to_domain() if result else None

    async def get_by_slack_user_id(
        self, team_id: UUID, slack_user_id: str
    ) -> Member | None:
        """Obtiene un miembro por su ID de Slack dentro de un equipo."""
        result = await self._session.execute(
            select(MemberORM).where(
                MemberORM.team_id == team_id,
                MemberORM.slack_user_id == slack_user_id,
            )
        )
        orm = result.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def get_by_team(self, team_id: UUID) -> list[Member]:
        """Obtiene todos los miembros de un equipo."""
        result = await self._session.execute(
            select(MemberORM).where(MemberORM.team_id == team_id)
        )
        return [member.to_domain() for member in result.scalars().all()]

    async def save(self, member: Member) -> Member:
        """Guarda o actualiza un miembro."""
        orm = MemberORM.from_domain(member)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()
