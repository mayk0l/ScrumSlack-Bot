"""Módulo: metric_repo.

Implementación concreta del repositorio de métricas con SQLAlchemy async.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import MetricSnapshot
from src.domain.repositories import MetricRepository
from src.infrastructure.orm_models import MetricSnapshotORM


class MetricRepositoryImpl(MetricRepository):
    """Repositorio de métricas usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, snapshot: MetricSnapshot) -> MetricSnapshot:
        """Guarda o actualiza un snapshot de métrica."""
        orm = MetricSnapshotORM.from_domain(snapshot)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def get_by_sprint(
        self, team_id: UUID, sprint_id: UUID
    ) -> list[MetricSnapshot]:
        """Obtiene métricas de un equipo filtradas por sprint en metadata."""
        result = await self._session.execute(
            select(MetricSnapshotORM).where(
                MetricSnapshotORM.team_id == team_id,
                MetricSnapshotORM.snapshot_metadata.contains({"sprint_id": str(sprint_id)}),
            )
        )
        return [snapshot.to_domain() for snapshot in result.scalars().all()]

    async def get_latest(
        self, team_id: UUID, metric_type: str
    ) -> MetricSnapshot | None:
        """Obtiene el snapshot más reciente de un tipo de métrica."""
        result = await self._session.execute(
            select(MetricSnapshotORM)
            .where(
                MetricSnapshotORM.team_id == team_id,
                MetricSnapshotORM.metric_type == metric_type,
            )
            .order_by(MetricSnapshotORM.date.desc())
            .limit(1)
        )
        orm = result.scalar_one_or_none()
        return orm.to_domain() if orm else None
