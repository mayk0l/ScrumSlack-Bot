"""Módulo: test_db_repos."""

import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

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
    SessionStatus,
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


@pytest_asyncio.fixture(scope="function", loop_scope="function")
async def db_session() -> AsyncSession:
    """Proporciona una sesión limpia con tablas recreadas por test."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_team_repository(db_session: AsyncSession) -> None:
    """CRUD básico de TeamRepositoryImpl."""
    repo = TeamRepositoryImpl(db_session)

    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    saved = await repo.save(team)
    assert saved.id == team.id

    fetched = await repo.get_by_id(team.id)
    assert fetched is not None
    assert fetched.name == "Squad"

    all_teams = await repo.get_all()
    assert len(all_teams) == 1


@pytest.mark.asyncio
async def test_member_repository(db_session: AsyncSession) -> None:
    """CRUD y consultas de MemberRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    repo = MemberRepositoryImpl(db_session)
    member = Member(
        team_id=team.id,
        slack_user_id="U42",
        display_name="Bob",
        role=MemberRole.DEVELOPER,
    )
    saved = await repo.save(member)
    assert saved.id == member.id

    fetched = await repo.get_by_id(member.id)
    assert fetched is not None
    assert fetched.slack_user_id == "U42"

    by_slack = await repo.get_by_slack_user_id(team.id, "U42")
    assert by_slack is not None
    assert by_slack.display_name == "Bob"

    by_team = await repo.get_by_team(team.id)
    assert len(by_team) == 1


@pytest.mark.asyncio
async def test_sprint_repository(db_session: AsyncSession) -> None:
    """CRUD y consultas de SprintRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    repo = SprintRepositoryImpl(db_session)
    now = datetime.now(timezone.utc)
    sprint = Sprint(
        team_id=team.id,
        name="S1",
        start_date=now,
        end_date=now,
        status=SprintStatus.ACTIVE,
    )
    saved = await repo.save(sprint)
    assert saved.id == sprint.id

    active = await repo.get_active(team.id)
    assert active is not None
    assert active.name == "S1"

    await repo.update_status(sprint.id, SprintStatus.COMPLETED)
    await db_session.commit()

    active_after = await repo.get_active(team.id)
    assert active_after is None


@pytest.mark.asyncio
async def test_standup_session_repository(db_session: AsyncSession) -> None:
    """CRUD y consultas de StandupSessionRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    repo = StandupSessionRepositoryImpl(db_session)
    today = date.today()
    session = StandupSession(
        team_id=team.id,
        date=datetime.now(timezone.utc),
        slack_channel_id="C1",
    )
    saved = await repo.save(session)
    assert saved.id == session.id

    fetched = await repo.get_by_id(session.id)
    assert fetched is not None

    today_session = await repo.get_today_session(team.id, today)
    assert today_session is not None
    assert today_session.slack_channel_id == "C1"

    await repo.update_status(session.id, SessionStatus.CLOSED)
    await db_session.commit()

    closed = await repo.get_by_id(session.id)
    assert closed is not None
    assert closed.status == SessionStatus.CLOSED


@pytest.mark.asyncio
async def test_standup_response_repository(db_session: AsyncSession) -> None:
    """CRUD y consultas de StandupResponseRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    member_repo = MemberRepositoryImpl(db_session)
    member = Member(
        team_id=team.id,
        slack_user_id="U42",
        display_name="Bob",
        role=MemberRole.DEVELOPER,
    )
    await member_repo.save(member)

    session_repo = StandupSessionRepositoryImpl(db_session)
    session = StandupSession(team_id=team.id, date=datetime.now(timezone.utc), slack_channel_id="C1")
    await session_repo.save(session)

    repo = StandupResponseRepositoryImpl(db_session)
    response = StandupResponse(
        session_id=session.id,
        member_id=member.id,
        yesterday="Ayer",
        today="Hoy",
        blockers="",
    )
    saved = await repo.save(response)
    assert saved.id == response.id

    by_session = await repo.get_by_session(session.id)
    assert len(by_session) == 1

    by_member_session = await repo.get_by_member_and_session(member.id, session.id)
    assert by_member_session is not None
    assert by_member_session.yesterday == "Ayer"


@pytest.mark.asyncio
async def test_pull_request_repository(db_session: AsyncSession) -> None:
    """CRUD, upsert y consultas de PullRequestRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    repo = PullRequestRepositoryImpl(db_session)
    now = datetime.now(timezone.utc)
    pr = PullRequest(
        team_id=team.id,
        repository="repo",
        pr_number=1,
        title="PR 1",
        author="dev",
        state="open",
        created_at=now,
        updated_at=now,
        reviewers=[],
    )
    saved = await repo.save(pr)
    assert saved.id == pr.id

    pr.title = "PR 1 updated"
    upserted = await repo.upsert(pr)
    assert upserted.title == "PR 1 updated"

    open_prs = await repo.get_open_by_team(team.id)
    assert len(open_prs) == 1

    stale = await repo.get_stale_prs(team.id, hours_threshold=0)
    assert len(stale) == 1

    fresh = await repo.get_stale_prs(team.id, hours_threshold=9999)
    assert len(fresh) == 0


@pytest.mark.asyncio
async def test_risk_repository(db_session: AsyncSession) -> None:
    """CRUD y consultas de RiskRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    repo = RiskRepositoryImpl(db_session)
    risk = Risk(
        team_id=team.id,
        type=RiskType.BLOCKER,
        description="Bloqueo",
        severity=Severity.HIGH,
        source_ref={"pr": 1},
    )
    saved = await repo.save(risk)
    assert saved.id == risk.id

    active = await repo.get_active_by_team(team.id)
    assert len(active) == 1

    await repo.resolve(risk.id)
    await db_session.commit()

    active_after = await repo.get_active_by_team(team.id)
    assert len(active_after) == 0


@pytest.mark.asyncio
async def test_metric_repository(db_session: AsyncSession) -> None:
    """CRUD y consultas de MetricRepositoryImpl."""
    team_repo = TeamRepositoryImpl(db_session)
    team = Team(name="Squad", slack_bot_token="xoxb", github_token="ghp", standup_channel_id="C1")
    await team_repo.save(team)

    sprint_id = uuid4()
    repo = MetricRepositoryImpl(db_session)
    snapshot = MetricSnapshot(
        team_id=team.id,
        metric_type="velocity",
        date=datetime.now(timezone.utc),
        value=25.0,
        metadata={"sprint_id": str(sprint_id)},
    )
    saved = await repo.save(snapshot)
    assert saved.id == snapshot.id

    latest = await repo.get_latest(team.id, "velocity")
    assert latest is not None
    assert latest.value == 25.0

    by_sprint = await repo.get_by_sprint(team.id, sprint_id)
    assert len(by_sprint) == 1
