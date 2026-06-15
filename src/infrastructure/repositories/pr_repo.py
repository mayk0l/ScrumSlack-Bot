"""Módulo: pr_repo.

Implementación concreta del repositorio de pull requests con SQLAlchemy async.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.models import PullRequest
from src.domain.repositories import PullRequestRepository
from src.infrastructure.orm_models import PullRequestORM


class PullRequestRepositoryImpl(PullRequestRepository):
    """Repositorio de pull requests usando SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, pr: PullRequest) -> PullRequest:
        """Guarda o actualiza un pull request."""
        orm = PullRequestORM.from_domain(pr)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()

    async def upsert(self, pr: PullRequest) -> PullRequest:
        """Inserta o actualiza un PR por (team_id, repository, pr_number)."""
        values = {
            "id": pr.id,
            "team_id": pr.team_id,
            "repository": pr.repository,
            "pr_number": pr.pr_number,
            "title": pr.title,
            "author": pr.author,
            "state": pr.state,
            "created_at": pr.created_at,
            "updated_at": pr.updated_at,
            "merged_at": pr.merged_at,
            "reviewers": list(pr.reviewers or []),
            "lead_time_hours": pr.lead_time_hours,
        }
        stmt = (
            insert(PullRequestORM)
            .values(values)
            .on_conflict_do_update(
                index_elements=["team_id", "repository", "pr_number"],
                set_={
                    "title": values["title"],
                    "author": values["author"],
                    "state": values["state"],
                    "updated_at": values["updated_at"],
                    "merged_at": values["merged_at"],
                    "reviewers": values["reviewers"],
                    "lead_time_hours": values["lead_time_hours"],
                },
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

        result = await self._session.execute(
            select(PullRequestORM).where(
                PullRequestORM.team_id == pr.team_id,
                PullRequestORM.repository == pr.repository,
                PullRequestORM.pr_number == pr.pr_number,
            )
        )
        return result.scalar_one().to_domain()

    async def get_open_by_team(self, team_id: UUID) -> list[PullRequest]:
        """Obtiene los PRs abiertos de un equipo."""
        result = await self._session.execute(
            select(PullRequestORM).where(
                PullRequestORM.team_id == team_id,
                PullRequestORM.state == "open",
            )
        )
        return [pr.to_domain() for pr in result.scalars().all()]

    async def get_stale_prs(
        self, team_id: UUID, hours_threshold: int = 24
    ) -> list[PullRequest]:
        """Obtiene PRs abiertos sin reviewers creados hace más de N horas."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        result = await self._session.execute(
            select(PullRequestORM).where(
                PullRequestORM.team_id == team_id,
                PullRequestORM.state == "open",
                PullRequestORM.created_at < cutoff,
                PullRequestORM.reviewers == [],
            )
        )
        return [pr.to_domain() for pr in result.scalars().all()]
