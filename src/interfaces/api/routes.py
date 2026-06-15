"""Módulo: routes.

Endpoints REST de la API.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.interfaces.api.dependencies import (
    get_db_session,
    get_member_repo,
    get_metric_repo,
    get_pr_repo,
    get_risk_repo,
    get_standup_session_repo,
)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=dict)
async def health() -> dict:
    """Health check básico."""
    return {"status": "ok"}


@router.get("/teams/{team_id}/standup/today", response_model=dict)
async def get_today_standup(
    team_id: UUID,
    session_repo=Depends(get_standup_session_repo),
):
    """Obtiene la sesión de standup del día."""
    from datetime import date

    session = await session_repo.get_today_session(team_id, date.today())
    return {
        "team_id": str(team_id),
        "session": session.to_domain() if session else None,
    }


@router.get("/teams/{team_id}/risks", response_model=dict)
async def get_risks(
    team_id: UUID,
    risk_repo=Depends(get_risk_repo),
):
    """Obtiene los riesgos activos del equipo."""
    risks = await risk_repo.get_active_by_team(team_id)
    return {"team_id": str(team_id), "risks": [r.to_domain() for r in risks]}


@router.get("/teams/{team_id}/prs", response_model=dict)
async def get_pull_requests(
    team_id: UUID,
    pr_repo=Depends(get_pr_repo),
):
    """Obtiene los PRs abiertos del equipo."""
    prs = await pr_repo.get_open_by_team(team_id)
    return {"team_id": str(team_id), "prs": [p.to_domain() for p in prs]}


@router.get("/teams/{team_id}/members", response_model=dict)
async def get_members(
    team_id: UUID,
    member_repo=Depends(get_member_repo),
):
    """Obtiene los miembros del equipo."""
    members = await member_repo.get_by_team(team_id)
    return {"team_id": str(team_id), "members": [m.to_domain() for m in members]}


@router.get("/teams/{team_id}/metrics", response_model=dict)
async def get_metrics(
    team_id: UUID,
    metric_type: str = "velocity",
    metric_repo=Depends(get_metric_repo),
):
    """Obtiene la última métrica del tipo indicado."""
    latest = await metric_repo.get_latest(team_id, metric_type)
    return {
        "team_id": str(team_id),
        "metric_type": metric_type,
        "latest": latest.to_domain() if latest else None,
    }
