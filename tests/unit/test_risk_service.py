"""Módulo: test_risk_service."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.application.risk_service import RiskService
from src.domain.models import PullRequest, Risk, RiskType, Severity


class FakeRiskRepository:
    def __init__(self):
        self._data: dict = {}

    async def save(self, risk):
        self._data[risk.id] = risk
        return risk

    async def get_active_by_team(self, team_id):
        return [r for r in self._data.values() if r.team_id == team_id and not r.resolved]

    async def resolve(self, risk_id):
        risk = self._data.get(risk_id)
        if risk:
            risk.resolved = True


class FakePullRequestRepository:
    def __init__(self, prs=None):
        self._prs = prs or []

    async def save(self, pr):
        return pr

    async def upsert(self, pr):
        return pr

    async def get_open_by_team(self, team_id):
        return [pr for pr in self._prs if pr.state == "open"]

    async def get_stale_prs(self, team_id, hours_threshold=24):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
        return [
            pr for pr in self._prs
            if pr.state == "open" and pr.created_at < cutoff and not pr.reviewers
        ]


class FakeResponseRepository:
    async def save(self, response):
        return response

    async def get_by_session(self, session_id):
        return []

    async def get_by_member_and_session(self, member_id, session_id):
        return None


@pytest.mark.asyncio
async def test_detect_risks_creates_pr_no_review():
    team_id = uuid4()
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    pr = PullRequest(
        team_id=team_id,
        repository="repo",
        pr_number=1,
        title="Old PR",
        author="dev",
        state="open",
        created_at=old,
        updated_at=old,
        reviewers=[],
    )
    risk_repo = FakeRiskRepository()
    service = RiskService(
        risk_repo=risk_repo,
        pr_repo=FakePullRequestRepository([pr]),
        response_repo=FakeResponseRepository(),
    )

    risks = await service.detect_risks(team_id)
    assert len(risks) == 1
    assert risks[0].type == RiskType.PR_NO_REVIEW
    assert risks[0].severity == Severity.CRITICAL


@pytest.mark.asyncio
async def test_detect_risks_does_not_duplicate():
    team_id = uuid4()
    old = datetime.now(timezone.utc) - timedelta(hours=25)
    pr = PullRequest(
        team_id=team_id,
        repository="repo",
        pr_number=1,
        title="Old PR",
        author="dev",
        state="open",
        created_at=old,
        updated_at=old,
        reviewers=[],
    )
    risk_repo = FakeRiskRepository()
    service = RiskService(
        risk_repo=risk_repo,
        pr_repo=FakePullRequestRepository([pr]),
        response_repo=FakeResponseRepository(),
    )

    await service.detect_risks(team_id)
    risks = await service.detect_risks(team_id)
    assert len(risks) == 0
