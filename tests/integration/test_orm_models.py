"""Módulo: test_orm_models."""

import os
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Asegurar DATABASE_URL apunte a localhost para tests locales.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://scrum_bot:scrum_bot_pass@db:5432/scrum_bot_db",
)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("SLACK_SIGNING_SECRET", "test")
os.environ.setdefault("STANDUP_CHANNEL_ID", "Ctest")
os.environ.setdefault("GITHUB_TOKEN", "ghp_test")

from src.config import settings
from src.domain.models import (
    Issue,
    Member,
    MemberRole,
    MetricSnapshot,
    PullRequest,
    Risk,
    RiskType,
    Severity,
    Sprint,
    SprintStatus,
    StandupResponse,
    StandupSession,
    Team,
)
from src.infrastructure.database import Base
from src.infrastructure.orm_models import (
    IssueORM,
    MemberORM,
    MetricSnapshotORM,
    PullRequestORM,
    RiskORM,
    SprintORM,
    StandupResponseORM,
    StandupSessionORM,
    TeamORM,
)


def _create_local_engine():
    """Crea un engine local sin pool para evitar conflictos de event loop."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        """Hook reservado; no aplica para PostgreSQL."""
        pass

    return engine


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def db_session() -> AsyncSession:
    """Proporciona una sesión limpia con tablas recreadas por test."""
    engine = _create_local_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_team_orm_round_trip(db_session: AsyncSession) -> None:
    """Team se persiste y recupera correctamente."""
    team = Team(
        name="Squad Beta",
        slack_bot_token="xoxb-test",
        github_token="ghp-test",
        standup_channel_id="C999",
    )
    db_session.add(TeamORM.from_domain(team))
    await db_session.commit()

    loaded = await db_session.get(TeamORM, team.id)
    assert loaded is not None
    assert loaded.to_domain().name == "Squad Beta"


@pytest.mark.asyncio
async def test_member_orm_round_trip(db_session: AsyncSession) -> None:
    """Member se persiste y recupera correctamente."""
    team = Team(name="Squad Beta", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    member = Member(
        team_id=team.id,
        slack_user_id="U42",
        display_name="Bob",
        role=MemberRole.TECH_LEAD,
    )
    db_session.add(MemberORM.from_domain(member))
    await db_session.commit()

    loaded = await db_session.get(MemberORM, member.id)
    assert loaded is not None
    assert loaded.to_domain().role == MemberRole.TECH_LEAD


@pytest.mark.asyncio
async def test_sprint_orm_round_trip(db_session: AsyncSession) -> None:
    """Sprint se persiste y recupera correctamente."""
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    now = datetime.now(timezone.utc)
    sprint = Sprint(
        team_id=team.id,
        name="Sprint 2",
        start_date=now,
        end_date=now,
        status=SprintStatus.ACTIVE,
    )
    db_session.add(SprintORM.from_domain(sprint))
    await db_session.commit()

    loaded = await db_session.get(SprintORM, sprint.id)
    assert loaded is not None
    assert loaded.to_domain().status == SprintStatus.ACTIVE


@pytest.mark.asyncio
async def test_standup_response_orm_round_trip(db_session: AsyncSession) -> None:
    """StandupResponse se persiste y recupera correctamente."""
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    member = Member(
        team_id=team.id,
        slack_user_id="U42",
        display_name="Bob",
        role=MemberRole.DEVELOPER,
    )
    db_session.add(MemberORM.from_domain(member))

    now = datetime.now(timezone.utc)
    standup_session = StandupSession(team_id=team.id, date=now, slack_channel_id="C123")
    db_session.add(StandupSessionORM.from_domain(standup_session))

    response = StandupResponse(
        session_id=standup_session.id,
        member_id=member.id,
        yesterday="Ayer",
        today="Hoy",
        blockers="Ninguno",
    )
    db_session.add(StandupResponseORM.from_domain(response))
    await db_session.commit()

    loaded = await db_session.get(StandupResponseORM, response.id)
    assert loaded is not None
    assert loaded.to_domain().yesterday == "Ayer"


@pytest.mark.asyncio
async def test_pull_request_orm_round_trip(db_session: AsyncSession) -> None:
    """PullRequest se persiste y recupera correctamente."""
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    now = datetime.now(timezone.utc)
    pr = PullRequest(
        team_id=team.id,
        repository="repo",
        pr_number=42,
        title="Feature X",
        author="dev",
        state="open",
        created_at=now,
        updated_at=now,
        reviewers=["alice"],
    )
    db_session.add(PullRequestORM.from_domain(pr))
    await db_session.commit()

    loaded = await db_session.get(PullRequestORM, pr.id)
    assert loaded is not None
    assert loaded.to_domain().reviewers == ["alice"]


@pytest.mark.asyncio
async def test_issue_orm_round_trip(db_session: AsyncSession) -> None:
    """Issue se persiste y recupera correctamente."""
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    issue = Issue(
        team_id=team.id,
        repository="repo",
        issue_number=7,
        title="Bug Y",
        state="open",
        labels=["bug"],
    )
    db_session.add(IssueORM.from_domain(issue))
    await db_session.commit()

    loaded = await db_session.get(IssueORM, issue.id)
    assert loaded is not None
    assert loaded.to_domain().title == "Bug Y"
    assert loaded.labels == ["bug"]


@pytest.mark.asyncio
async def test_risk_orm_round_trip(db_session: AsyncSession) -> None:
    """Risk se persiste y recupera correctamente."""
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    risk = Risk(
        team_id=team.id,
        type=RiskType.BLOCKER,
        description="Bloqueo",
        severity=Severity.CRITICAL,
        source_ref={"pr": 1},
    )
    db_session.add(RiskORM.from_domain(risk))
    await db_session.commit()

    loaded = await db_session.get(RiskORM, risk.id)
    assert loaded is not None
    assert loaded.to_domain().severity == Severity.CRITICAL
    assert loaded.to_domain().source_ref == {"pr": 1}


@pytest.mark.asyncio
async def test_metric_snapshot_orm_round_trip(db_session: AsyncSession) -> None:
    """MetricSnapshot se persiste y recupera correctamente."""
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    db_session.add(TeamORM.from_domain(team))

    now = datetime.now(timezone.utc)
    snapshot = MetricSnapshot(
        team_id=team.id,
        metric_type="velocity",
        date=now,
        value=25.0,
        metadata={"sprint": "S1"},
    )
    db_session.add(MetricSnapshotORM.from_domain(snapshot))
    await db_session.commit()

    loaded = await db_session.get(MetricSnapshotORM, snapshot.id)
    assert loaded is not None
    assert loaded.to_domain().value == 25.0
    assert loaded.to_domain().metadata == {"sprint": "S1"}
