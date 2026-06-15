"""Módulo: standup_repo.

Implementación concreta de repositorios de sesiones y respuestas de standup.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import SessionStatus, StandupResponse, StandupSession
from src.domain.repositories import (
    StandupResponseRepository,
    StandupSessionRepository,
)
from src.infrastructure.orm_models import StandupResponseORM, StandupSessionORM


class StandupSessionRepositoryImpl(StandupSessionRepository):
    """Repositorio de sesiones de standup usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, session_id: UUID) -> StandupSession | None:
        """Obtiene una sesión por su ID."""
        result = await self._session.get(StandupSessionORM, session_id)
        return result.to_domain() if result else None

    async def get_today_session(
        self, team_id: UUID, date: date
    ) -> StandupSession | None:
        """Obtiene la sesión de standup de un equipo para una fecha específica."""
        result = await self._session.execute(
            select(StandupSessionORM).where(
                StandupSessionORM.team_id == team_id,
                StandupSessionORM.date == date,
            )
        )
        orm = result.scalar_one_or_none()
        return orm.to_domain() if orm else None

    async def save(self, session: StandupSession) -> StandupSession:
        """Guarda o actualiza una sesión de standup."""
        orm = StandupSessionORM.from_domain(session)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def update_status(self, session_id: UUID, status: SessionStatus) -> None:
        """Actualiza el estado de una sesión de standup."""
        orm = await self._session.get(StandupSessionORM, session_id)
        if orm is not None:
            orm.status = status.value


class StandupResponseRepositoryImpl(StandupResponseRepository):
    """Repositorio de respuestas de standup usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, response: StandupResponse) -> StandupResponse:
        """Guarda o actualiza una respuesta de standup."""
        orm = StandupResponseORM.from_domain(response)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def get_by_session(self, session_id: UUID) -> list[StandupResponse]:
        """Obtiene todas las respuestas de una sesión."""
        result = await self._session.execute(
            select(StandupResponseORM).where(
                StandupResponseORM.session_id == session_id
            )
        )
        return [response.to_domain() for response in result.scalars().all()]

    async def get_by_member_and_session(
        self, member_id: UUID, session_id: UUID
    ) -> StandupResponse | None:
        """Obtiene la respuesta de un miembro en una sesión específica."""
        result = await self._session.execute(
            select(StandupResponseORM).where(
                StandupResponseORM.member_id == member_id,
                StandupResponseORM.session_id == session_id,
            )
        )
        orm = result.scalar_one_or_none()
        return orm.to_domain() if orm else None
