"""Módulo: dependencies.

Inyección de dependencias para FastAPI.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.container import get_container
from src.domain.repositories import (
    MemberRepository,
    MetricRepository,
    PullRequestRepository,
    RiskRepository,
    SprintRepository,
    StandupResponseRepository,
    StandupSessionRepository,
    TeamRepository,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provee una sesión de DB con commit/rollback automático usando el contenedor global."""
    container = get_container()
    async with container.session() as session:
        yield session


def get_team_repo(session: AsyncSession = Depends(get_db_session)) -> TeamRepository:
    from src.infrastructure.repositories.team_repo import TeamRepositoryImpl
    return TeamRepositoryImpl(session)


def get_member_repo(session: AsyncSession = Depends(get_db_session)) -> MemberRepository:
    from src.infrastructure.repositories.member_repo import MemberRepositoryImpl
    return MemberRepositoryImpl(session)


def get_standup_session_repo(session: AsyncSession = Depends(get_db_session)) -> StandupSessionRepository:
    from src.infrastructure.repositories.standup_repo import StandupSessionRepositoryImpl
    return StandupSessionRepositoryImpl(session)


def get_standup_response_repo(session: AsyncSession = Depends(get_db_session)) -> StandupResponseRepository:
    from src.infrastructure.repositories.standup_repo import StandupResponseRepositoryImpl
    return StandupResponseRepositoryImpl(session)


def get_pr_repo(session: AsyncSession = Depends(get_db_session)) -> PullRequestRepository:
    from src.infrastructure.repositories.pr_repo import PullRequestRepositoryImpl
    return PullRequestRepositoryImpl(session)


def get_sprint_repo(session: AsyncSession = Depends(get_db_session)) -> SprintRepository:
    from src.infrastructure.repositories.sprint_repo import SprintRepositoryImpl
    return SprintRepositoryImpl(session)


def get_risk_repo(session: AsyncSession = Depends(get_db_session)) -> RiskRepository:
    from src.infrastructure.repositories.risk_repo import RiskRepositoryImpl
    return RiskRepositoryImpl(session)


def get_metric_repo(session: AsyncSession = Depends(get_db_session)) -> MetricRepository:
    from src.infrastructure.repositories.metric_repo import MetricRepositoryImpl
    return MetricRepositoryImpl(session)
