"""Módulo: test_models."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.domain.models import (
    Issue,
    Member,
    MemberRole,
    MetricSnapshot,
    PullRequest,
    Risk,
    RiskType,
    SessionStatus,
    Severity,
    Sprint,
    SprintStatus,
    StandupResponse,
    StandupSession,
    Team,
)


def test_team_can_be_instantiated() -> None:
    """Un equipo puede crearse con los campos obligatorios."""
    team = Team(
        name="Squad Alpha",
        slack_bot_token="xoxb-token",
        github_token="ghp-token",
        standup_channel_id="C123",
    )
    assert isinstance(team.id, UUID)
    assert team.name == "Squad Alpha"
    assert team.timezone == "America/Santiago"


def test_member_defaults_to_developer_role() -> None:
    """El rol por defecto de un miembro es developer."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    member = Member(team_id=team.id, slack_user_id="U1", display_name="Alice")
    assert member.role == MemberRole.DEVELOPER
    assert isinstance(member.id, UUID)


def test_sprint_status_defaults_to_planning() -> None:
    """Un sprint nuevo inicia en planning."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    now = datetime.now(timezone.utc)
    sprint = Sprint(
        team_id=team.id,
        name="Sprint 1",
        start_date=now,
        end_date=now,
    )
    assert sprint.status == SprintStatus.PLANNING


def test_standup_session_defaults_to_open() -> None:
    """Una sesión de standup nueva inicia abierta."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    now = datetime.now(timezone.utc)
    session = StandupSession(team_id=team.id, date=now, slack_channel_id="C123")
    assert session.status == SessionStatus.OPEN
    assert session.sprint_id is None


def test_standup_response_has_required_fields() -> None:
    """Una respuesta de standup requiere session_id, member_id y avances."""
    session_id = UUID("12345678-1234-5678-1234-567812345678")
    member_id = UUID("87654321-4321-8765-4321-876543218765")
    response = StandupResponse(
        session_id=session_id,
        member_id=member_id,
        yesterday="Trabajé en X",
        today="Trabajaré en Y",
    )
    assert response.blockers == ""
    assert response.yesterday == "Trabajé en X"


def test_pull_request_defaults() -> None:
    """Un PR tiene listas vacías y campos opcionales nulos por defecto."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    now = datetime.now(timezone.utc)
    pr = PullRequest(
        team_id=team.id,
        repository="repo",
        pr_number=1,
        title="Feature",
        author="dev",
        state="open",
        created_at=now,
        updated_at=now,
    )
    assert pr.reviewers == []
    assert pr.merged_at is None
    assert pr.lead_time_hours is None


def test_issue_defaults() -> None:
    """Un issue tiene campos opcionales por defecto."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    issue = Issue(
        team_id=team.id,
        repository="repo",
        issue_number=1,
        title="Bug",
        state="open",
    )
    assert issue.labels == []
    assert issue.assignee is None


def test_risk_defaults() -> None:
    """Un riesgo nuevo no está resuelto y tiene severidad asignada."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    risk = Risk(
        team_id=team.id,
        type=RiskType.BLOCKER,
        description="Bloqueo en API",
        severity=Severity.HIGH,
    )
    assert risk.resolved is False
    assert risk.severity == Severity.HIGH
    assert risk.source_ref == {}


def test_metric_snapshot_defaults() -> None:
    """Un snapshot de métrica tiene metadatos vacíos por defecto."""
    team = Team(name="Squad", slack_bot_token="t", github_token="t", standup_channel_id="C")
    now = datetime.now(timezone.utc)
    snapshot = MetricSnapshot(
        team_id=team.id,
        metric_type="velocity",
        date=now,
        value=10.5,
    )
    assert snapshot.metadata == {}
    assert snapshot.value == 10.5


@pytest.mark.parametrize(
    "enum_class, expected_members",
    [
        (SprintStatus, {"PLANNING", "ACTIVE", "COMPLETED"}),
        (SessionStatus, {"OPEN", "CLOSED"}),
        (RiskType, {"PR_NO_REVIEW", "CI_FAILURE", "BLOCKER", "STALE_BRANCH"}),
        (Severity, {"LOW", "MEDIUM", "HIGH", "CRITICAL"}),
        (MemberRole, {"DEVELOPER", "TECH_LEAD", "SCRUM_MASTER", "PRODUCT_OWNER"}),
    ],
)
def test_enum_values(enum_class, expected_members) -> None:
    """Los enums contienen exactamente los valores esperados."""
    assert {m.name for m in enum_class} == expected_members


def test_models_module_has_no_framework_imports() -> None:
    """El módulo de dominio no debe importar frameworks."""
    from pathlib import Path

    source = (Path(__file__).resolve().parent.parent.parent / "src" / "domain" / "models.py").read_text(
        encoding="utf-8"
    )
    forbidden_imports = ["sqlalchemy", "fastapi", "slack", "pydantic"]
    for name in forbidden_imports:
        import_patterns = [f"import {name}", f"from {name}"]
        assert not any(pattern in source for pattern in import_patterns), (
            f"Import prohibido encontrado: {name}"
        )
