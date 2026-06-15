"""Módulo: github_service.

Servicio de aplicación para sincronizar PRs desde GitHub.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.domain.models import PullRequest
from src.domain.repositories import PullRequestRepository
from src.infrastructure.github_client import GitHubClient


class GitHubService:
    """Orquesta la sincronización y consulta de pull requests."""

    def __init__(
        self,
        github_client: GitHubClient,
        pr_repo: PullRequestRepository,
    ):
        self._github_client = github_client
        self._pr_repo = pr_repo

    async def sync_pull_requests(
        self, team_id: UUID, org: str, repos: list[str]
    ) -> int:
        """Sincroniza PRs abiertos de los repositorios indicados."""
        count = 0
        for repo in repos:
            prs = await self._github_client.get_open_pull_requests(org, repo)
            for pr_data in prs:
                pr = self._map_pr(team_id, repo, pr_data)
                await self._pr_repo.upsert(pr)
                count += 1
        return count

    async def get_open_prs(self, team_id: UUID) -> list[PullRequest]:
        """Obtiene los PRs abiertos persistidos de un equipo."""
        return await self._pr_repo.get_open_by_team(team_id)

    async def get_stale_prs(
        self, team_id: UUID, hours: int = 24
    ) -> list[PullRequest]:
        """Obtiene PRs abiertos sin reviewers por más de N horas."""
        return await self._pr_repo.get_stale_prs(team_id, hours)

    def _map_pr(
        self, team_id: UUID, repository: str, data: dict
    ) -> PullRequest:
        """Mapea un payload de GitHub API a modelo de dominio."""
        now = datetime.now(timezone.utc)
        created_at = data.get("created_at") or now.isoformat()
        updated_at = data.get("updated_at") or now.isoformat()
        merged_at = data.get("merged_at")
        reviewers = [
            r.get("login", "")
            for r in data.get("requested_reviewers", [])
            if r.get("login")
        ]
        return PullRequest(
            team_id=team_id,
            repository=repository,
            pr_number=int(data["number"]),
            title=data.get("title", ""),
            author=data.get("user", {}).get("login", ""),
            state=data.get("state", "open"),
            created_at=self._parse_dt(created_at),
            updated_at=self._parse_dt(updated_at),
            merged_at=self._parse_dt(merged_at) if merged_at else None,
            reviewers=reviewers,
        )

    @staticmethod
    def _parse_dt(value: str) -> datetime:
        """Parsea una fecha ISO de GitHub a datetime con timezone UTC."""
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
