"""Módulo: team_repo.

Implementación concreta del repositorio de equipos con SQLAlchemy async.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import Team
from src.domain.repositories import TeamRepository
from src.infrastructure.orm_models import TeamORM


class TeamRepositoryImpl(TeamRepository):
    """Repositorio de equipos usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, team_id: UUID) -> Team | None:
        """Obtiene un equipo por su ID."""
        result = await self._session.get(TeamORM, team_id)
        return result.to_domain() if result else None

    async def save(self, team: Team) -> Team:
        """Guarda o actualiza un equipo."""
        orm = TeamORM.from_domain(team)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def get_all(self) -> list[Team]:
        """Obtiene todos los equipos."""
        result = await self._session.execute(select(TeamORM))
        return [team.to_domain() for team in result.scalars().all()]
