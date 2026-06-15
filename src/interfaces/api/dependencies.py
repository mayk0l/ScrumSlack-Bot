"""Módulo: dependencies.

Inyección de dependencias para FastAPI.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.infrastructure.database import get_session
from src.infrastructure.repositories.member_repo import MemberRepositoryImpl
from src.infrastructure.repositories.metric_repo import MetricRepositoryImpl
from src.infrastructure.repositories.pr_repo import PullRequestRepositoryImpl
from src.infrastructure.repositories.risk_repo import RiskRepositoryImpl
from src.infrastructure.repositories.sprint_repo import SprintRepositoryImpl
from src.infrastructure.repositories.standup_repo import (
    StandupResponseRepositoryImpl,
    StandupSessionRepositoryImpl,
)
from src.infrastructure.repositories.team_repo import TeamRepositoryImpl


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provee una sesión de DB con commit/rollback automático."""
    async with get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_team_repo(session: AsyncSession = Depends(get_db_session)) -> TeamRepository:
    return TeamRepositoryImpl(session)


def get_member_repo(session: AsyncSession = Depends(get_db_session)) -> MemberRepository:
    return MemberRepositoryImpl(session)


def get_standup_session_repo(session: AsyncSession = Depends(get_db_session)) -> StandupSessionRepository:
    return StandupSessionRepositoryImpl(session)


def get_standup_response_repo(session: AsyncSession = Depends(get_db_session)) -> StandupResponseRepository:
    return StandupResponseRepositoryImpl(session)


def get_pr_repo(session: AsyncSession = Depends(get_db_session)) -> PullRequestRepository:
    return PullRequestRepositoryImpl(session)


def get_sprint_repo(session: AsyncSession = Depends(get_db_session)) -> SprintRepository:
    return SprintRepositoryImpl(session)


def get_risk_repo(session: AsyncSession = Depends(get_db_session)) -> RiskRepository:
    return RiskRepositoryImpl(session)


def get_metric_repo(session: AsyncSession = Depends(get_db_session)) -> MetricRepository:
    return MetricRepositoryImpl(session)
