"""Módulo: risk_repo.

Implementación concreta del repositorio de riesgos con SQLAlchemy async.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import Risk
from src.domain.repositories import RiskRepository
from src.infrastructure.orm_models import RiskORM


class RiskRepositoryImpl(RiskRepository):
    """Repositorio de riesgos usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, risk: Risk) -> Risk:
        """Guarda o actualiza un riesgo."""
        orm = RiskORM.from_domain(risk)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def get_active_by_team(self, team_id: UUID) -> list[Risk]:
        """Obtiene los riesgos no resueltos de un equipo."""
        result = await self._session.execute(
            select(RiskORM).where(
                RiskORM.team_id == team_id,
                RiskORM.resolved.is_(False),
            )
        )
        return [risk.to_domain() for risk in result.scalars().all()]

    async def resolve(self, risk_id: UUID) -> None:
        """Marca un riesgo como resuelto."""
        orm = await self._session.get(RiskORM, risk_id)
        if orm is not None:
            orm.resolved = True
