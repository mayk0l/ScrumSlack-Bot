"""Módulo: sprint_repo.

Implementación concreta del repositorio de sprints con SQLAlchemy async.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import Sprint, SprintStatus
from src.domain.repositories import SprintRepository
from src.infrastructure.orm_models import SprintORM


class SprintRepositoryImpl(SprintRepository):
    """Repositorio de sprints usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active(self, team_id: UUID) -> Sprint | None:
        """Obtiene el sprint activo de un equipo."""
        result = await self._session.execute(
            select(SprintORM).where(
                SprintORM.team_id == team_id,
                SprintORM.status == SprintStatus.ACTIVE.value,
            )
        )
        orm = result.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def save(self, sprint: Sprint) -> Sprint:
        """Guarda o actualiza un sprint."""
        orm = SprintORM.from_domain(sprint)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def update_status(self, sprint_id: UUID, status: SprintStatus) -> None:
        """Actualiza el estado de un sprint."""
        orm = await self._session.get(SprintORM, sprint_id)
        if orm is not None:
            orm.status = status.value
