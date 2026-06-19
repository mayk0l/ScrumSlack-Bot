"""Módulo: test_report_service."""

from uuid import uuid4

import pytest

from src.application.report_service import ReportService
from src.domain.models import PullRequest, Risk, RiskType, Severity, StandupResponse


class FakeStandupService:
    def __init__(self, responses=None, missing=None):
        self._responses = responses or []
        self._missing = missing or []

    async def get_today_responses(self, team_id, slack_channel_id):
        return self._responses

    async def get_missing_members(self, team_id, slack_channel_id):
        return self._missing


class FakeGitHubService:
    def __init__(self, prs=None):
        self._prs = prs or []

    async def get_open_prs(self, team_id):
        return self._prs


class FakeRiskService:
    def __init__(self, risks=None):
        self._risks = risks or []

    async def get_active_risks(self, team_id):
        return self._risks


@pytest.mark.asyncio
async def test_generate_daily_summary_contains_sections():
    team_id = uuid4()
    response = StandupResponse(
        session_id=uuid4(),
        member_id=uuid4(),
        yesterday="Ayer",
        today="Hoy",
        blockers="",
    )
    pr = PullRequest(
        team_id=team_id,
        repository="repo",
        pr_number=1,
        title="PR",
        author="dev",
        state="open",
        created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )
    risk = Risk(
        team_id=team_id,
        type=RiskType.BLOCKER,
        description="Bloqueo",
        severity=Severity.HIGH,
    )

    service = ReportService(
        standup_service=FakeStandupService(responses=[response]),
        github_service=FakeGitHubService(prs=[pr]),
        risk_service=FakeRiskService(risks=[risk]),
    )

    summary = await service.generate_daily_summary(team_id, "C1")
    assert "Resumen Diario" in summary
    assert "Standup" in summary
    assert "Pull Requests Abiertos" in summary
    assert "Riesgos Activos" in summary
    assert "Miembros sin responder" in summary


@pytest.mark.asyncio
async def test_generate_daily_summary_handles_empty_data():
    team_id = uuid4()
    service = ReportService(
        standup_service=FakeStandupService(),
        github_service=FakeGitHubService(),
        risk_service=FakeRiskService(),
    )

    summary = await service.generate_daily_summary(team_id, "C1")
    assert "Sin respuestas de standup" in summary
    assert "Sin PRs abiertos" in summary
    assert "Sin riesgos activos" in summary

class FakeAIClient:
    async def generate_summary(self, prompt, context):
        return f"AI_PROMPT_WAS: {prompt}"

class FakeValuelistService:
    async def get_bitacora_summary(self):
        return {"og": "Terminar todo"}

    async def get_objective_progress(self):
        return [{"id": "OE1", "desc": "Primer objetivo", "progress": 0.5, "total": 2, "done": 1}]


@pytest.mark.asyncio
async def test_generate_daily_summary_includes_excel_progress():
    service = ReportService(
        standup_service=FakeStandupService(),
        github_service=FakeGitHubService(),
        risk_service=FakeRiskService(),
        valuelist_service=FakeValuelistService(),
    )
    summary = await service.generate_daily_summary(uuid4(), "C1")
    assert "Progreso del proyecto" in summary
    assert "OE1" in summary


class FakeMemberRepo:
    def __init__(self, members):
        self._members = members

    async def get_by_team(self, team_id):
        return self._members


@pytest.mark.asyncio
async def test_daily_summary_uses_slack_mentions_and_valid_mrkdwn():
    from src.domain.models import Member

    mid = uuid4()
    member = Member(team_id=uuid4(), slack_user_id="U999", display_name="U999", id=mid)
    response = StandupResponse(
        session_id=uuid4(), member_id=mid, yesterday="a", today="b", blockers=""
    )
    service = ReportService(
        standup_service=FakeStandupService(responses=[response]),
        github_service=FakeGitHubService(),
        risk_service=FakeRiskService(),
        member_repo=FakeMemberRepo([member]),
    )
    summary = await service.generate_daily_summary(uuid4(), "C1")
    # Menciona al usuario en lugar de mostrar su UUID.
    assert "<@U999>" in summary
    assert str(mid) not in summary
    # mrkdwn de Slack válido: sin encabezados '#' ni negrita '**'.
    assert "##" not in summary
    assert "**" not in summary


def test_to_slack_mrkdwn_converts_markdown():
    from src.application.report_service import _to_slack_mrkdwn

    out = _to_slack_mrkdwn("## Título\n**Negrita** normal\n- item\n* otro")
    assert "##" not in out
    assert "**" not in out
    assert "*Título*" in out
    assert "*Negrita*" in out
    assert "• item" in out
    assert "• otro" in out


class FakeMarkdownAIClient:
    async def generate_summary(self, prompt, context):
        return "**Resumen**\n## Sección\n- punto importante"


@pytest.mark.asyncio
async def test_ai_summary_converts_markdown_to_slack():
    service = ReportService(
        standup_service=FakeStandupService(),
        github_service=FakeGitHubService(),
        risk_service=FakeRiskService(),
        ai_client=FakeMarkdownAIClient(),
    )
    result = await service.generate_ai_summary(uuid4(), "C1")
    ai_part = result.split("Análisis del Scrum Master")[-1]
    assert "**" not in ai_part
    assert "##" not in ai_part
    assert "*Resumen*" in ai_part
    assert "• punto importante" in ai_part

@pytest.mark.asyncio
async def test_generate_ai_summary_with_context():
    team_id = uuid4()
    service = ReportService(
        standup_service=FakeStandupService(),
        github_service=FakeGitHubService(),
        risk_service=FakeRiskService(),
        ai_client=FakeAIClient(),
        valuelist_service=FakeValuelistService()
    )

    result = await service.generate_ai_summary(team_id, "C1")
    assert "AI_PROMPT_WAS" in result
    assert "Terminar todo" in result
