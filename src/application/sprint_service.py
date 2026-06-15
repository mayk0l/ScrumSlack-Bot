"""Módulo: sprint_service.

Servicio de aplicación para gestión de sprints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.domain.models import MetricSnapshot, Sprint, SprintStatus
from src.domain.repositories import MetricRepository, SprintRepository


class SprintService:
    """Orquesta la lógica de negocio de sprints."""

    def __init__(
        self,
        sprint_repo: SprintRepository,
        metric_repo: MetricRepository,
    ):
        self._sprint_repo = sprint_repo
        self._metric_repo = metric_repo

    async def get_active_sprint(self, team_id: UUID) -> Sprint | None:
        """Obtiene el sprint activo de un equipo."""
        return await self._sprint_repo.get_active(team_id)

    async def create_sprint(
        self,
        team_id: UUID,
        name: str,
        start: datetime,
        end: datetime,
        goals: str = "",
    ) -> Sprint:
        """Crea un nuevo sprint para el equipo."""
        sprint = Sprint(
            team_id=team_id,
            name=name,
            start_date=start,
            end_date=end,
            goals=goals,
            status=SprintStatus.PLANNING,
        )
        return await self._sprint_repo.save(sprint)

    async def complete_sprint(self, team_id: UUID) -> Sprint:
        """Completa el sprint activo del equipo."""
        sprint = await self._sprint_repo.get_active(team_id)
        if sprint is None:
            from src.domain.exceptions import SprintNotActiveError
            raise SprintNotActiveError()
        await self._sprint_repo.update_status(sprint.id, SprintStatus.COMPLETED)
        sprint.status = SprintStatus.COMPLETED
        return sprint

    async def get_sprint_metrics(self, team_id: UUID, sprint_id: UUID) -> dict:
        """Retorna métricas asociadas a un sprint."""
        metrics = await self._metric_repo.get_by_sprint(team_id, sprint_id)
        return {
            "sprint_id": str(sprint_id),
            "metrics": [
                {"type": m.metric_type, "value": m.value, "date": m.date.isoformat()}
                for m in metrics
            ],
        }
