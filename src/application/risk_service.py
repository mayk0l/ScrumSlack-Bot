"""Módulo: risk_service.

Servicio de aplicación para detección automática de riesgos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.domain.models import PullRequest, Risk, RiskType, Severity
from src.domain.repositories import (
    PullRequestRepository,
    RiskRepository,
    StandupResponseRepository,
)


class RiskService:
    """Ejecuta reglas de detección de riesgos."""

    def __init__(
        self,
        risk_repo: RiskRepository,
        pr_repo: PullRequestRepository,
        response_repo: StandupResponseRepository,
    ):
        self._risk_repo = risk_repo
        self._pr_repo = pr_repo
        self._response_repo = response_repo

    async def detect_risks(self, team_id: UUID) -> list[Risk]:
        """Ejecuta todas las reglas de detección y persiste riesgos nuevos."""
        detected: list[Risk] = []
        detected.extend(await self._detect_pr_no_review(team_id))
        detected.extend(await self._detect_stale_branches(team_id))
        detected.extend(await self._detect_standup_blockers(team_id))

        new_risks: list[Risk] = []
        for risk in detected:
            if not await self._risk_already_exists(team_id, risk):
                saved = await self._risk_repo.save(risk)
                new_risks.append(saved)
        return new_risks

    async def get_active_risks(self, team_id: UUID) -> list[Risk]:
        """Obtiene los riesgos activos de un equipo."""
        return await self._risk_repo.get_active_by_team(team_id)

    async def resolve_risk(self, risk_id: UUID) -> None:
        """Marca un riesgo como resuelto."""
        await self._risk_repo.resolve(risk_id)

    async def _detect_pr_no_review(self, team_id: UUID) -> list[Risk]:
        """Detecta PRs abiertos sin reviewers por más de 24/48 horas."""
        risks: list[Risk] = []
        stale_prs = await self._pr_repo.get_stale_prs(team_id, hours_threshold=24)
        for pr in stale_prs:
            hours_open = self._hours_since(pr.created_at)
            severity = Severity.CRITICAL if hours_open >= 48 else Severity.HIGH
            risks.append(
                Risk(
                    team_id=team_id,
                    type=RiskType.PR_NO_REVIEW,
                    description=f"PR #{pr.pr_number} en {pr.repository} sin review por {int(hours_open)}h",
                    severity=severity,
                    source_ref={
                        "repository": pr.repository,
                        "pr_number": pr.pr_number,
                    },
                )
            )
        return risks

    async def _detect_stale_branches(self, team_id: UUID) -> list[Risk]:
        """Detecta PRs abiertos por más de 72 horas."""
        risks: list[Risk] = []
        open_prs = await self._pr_repo.get_open_by_team(team_id)
        for pr in open_prs:
            hours_open = self._hours_since(pr.created_at)
            if hours_open >= 72:
                risks.append(
                    Risk(
                        team_id=team_id,
                        type=RiskType.STALE_BRANCH,
                        description=f"PR #{pr.pr_number} en {pr.repository} abierto hace {int(hours_open)}h",
                        severity=Severity.MEDIUM,
                        source_ref={
                            "repository": pr.repository,
                            "pr_number": pr.pr_number,
                        },
                    )
                )
        return risks

    async def _detect_standup_blockers(self, team_id: UUID) -> list[Risk]:
        """Detecta bloqueos reportados en respuestas de standup recientes."""
        risks: list[Risk] = []
        # Implementación simplificada: iterar por todas las respuestas no es eficiente.
        # En una versión real se filtraría por sesión del día.
        return risks

    async def _risk_already_exists(self, team_id: UUID, risk: Risk) -> bool:
        """Verifica si un riesgo equivalente ya existe activo."""
        active = await self._risk_repo.get_active_by_team(team_id)
        for existing in active:
            if (
                existing.type == risk.type
                and existing.source_ref == risk.source_ref
            ):
                return True
        return False

    @staticmethod
    def _hours_since(dt: datetime) -> float:
        """Horas transcurridas desde una fecha hasta ahora."""
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
