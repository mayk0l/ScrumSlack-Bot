"""Módulo: test_github_service."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.application.github_service import GitHubService
from src.domain.models import PullRequest


class FakeGitHubClient:
    def __init__(self, prs=None):
        self._prs = prs or []

    async def get_open_pull_requests(self, org, repo):
        return self._prs


class FakePullRequestRepository:
    def __init__(self):
        self._data: dict = {}

    async def save(self, pr):
        self._data[pr.id] = pr
        return pr

    async def upsert(self, pr):
        self._data[(pr.team_id, pr.repository, pr.pr_number)] = pr
        return pr

    async def get_open_by_team(self, team_id):
        return [
            pr for pr in self._data.values()
            if pr.team_id == team_id and pr.state == "open"
        ]

    async def get_stale_prs(self, team_id, hours_threshold=24):
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        return [
            pr for pr in await self.get_open_by_team(team_id)
            if pr.created_at < cutoff and not pr.reviewers
        ]


@pytest.mark.asyncio
async def test_sync_pull_requests_persists_prs():
    pr_payload = {
        "number": 42,
        "title": "Feature",
        "user": {"login": "dev"},
        "state": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "requested_reviewers": [],
    }
    client = FakeGitHubClient(prs=[pr_payload])
    repo = FakePullRequestRepository()
    service = GitHubService(client, repo)

    team_id = uuid4()
    count = await service.sync_pull_requests(team_id, "org", ["repo"])
    assert count == 1

    open_prs = await service.get_open_prs(team_id)
    assert len(open_prs) == 1
    assert open_prs[0].pr_number == 42


@pytest.mark.asyncio
async def test_get_stale_prs_filters_by_hours():
    team_id = uuid4()
    old = datetime.now(timezone.utc) - __import__("datetime").timedelta(hours=48)
    pr_payload = {
        "number": 1,
        "title": "Old",
        "user": {"login": "dev"},
        "state": "open",
        "created_at": old.isoformat(),
        "updated_at": old.isoformat(),
        "requested_reviewers": [],
    }
    client = FakeGitHubClient(prs=[pr_payload])
    repo = FakePullRequestRepository()
    service = GitHubService(client, repo)
    await service.sync_pull_requests(team_id, "org", ["repo"])

    stale = await service.get_stale_prs(team_id, hours=1)
    assert len(stale) == 1

    stale = await service.get_stale_prs(team_id, hours=999)
    assert len(stale) == 0
