"""Módulo: orm_models.

Modelos ORM de SQLAlchemy que mapean las entidades de dominio a tablas PostgreSQL.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.models import (
    Issue as IssueDomain,
    Member as MemberDomain,
    MemberRole,
    MetricSnapshot as MetricSnapshotDomain,
    PullRequest as PullRequestDomain,
    Risk as RiskDomain,
    RiskType,
    Severity,
    SessionStatus,
    Sprint as SprintDomain,
    SprintStatus,
    StandupResponse as StandupResponseDomain,
    StandupSession as StandupSessionDomain,
    Team as TeamDomain,
)
from src.infrastructure.database import Base


class TeamORM(Base):
    """Modelo ORM para equipos."""

    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slack_bot_token: Mapped[str] = mapped_column(String(255), nullable=False)
    github_token: Mapped[str] = mapped_column(String(255), nullable=False)
    standup_channel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    standup_schedule_time: Mapped[str] = mapped_column(String(5), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="America/Santiago")

    members: Mapped[list["MemberORM"]] = relationship(back_populates="team")
    sprints: Mapped[list["SprintORM"]] = relationship(back_populates="team")
    standup_sessions: Mapped[list["StandupSessionORM"]] = relationship(back_populates="team")
    pull_requests: Mapped[list["PullRequestORM"]] = relationship(back_populates="team")
    issues: Mapped[list["IssueORM"]] = relationship(back_populates="team")
    risks: Mapped[list["RiskORM"]] = relationship(back_populates="team")
    metric_snapshots: Mapped[list["MetricSnapshotORM"]] = relationship(back_populates="team")

    def to_domain(self) -> TeamDomain:
        return TeamDomain(
            id=self.id,
            name=self.name,
            slack_bot_token=self.slack_bot_token,
            github_token=self.github_token,
            standup_channel_id=self.standup_channel_id,
            standup_schedule_time=self.standup_schedule_time,
            timezone=self.timezone,
        )

    @classmethod
    def from_domain(cls, team: TeamDomain) -> "TeamORM":
        return cls(
            id=team.id,
            name=team.name,
            slack_bot_token=team.slack_bot_token,
            github_token=team.github_token,
            standup_channel_id=team.standup_channel_id,
            standup_schedule_time=team.standup_schedule_time,
            timezone=team.timezone,
        )


class MemberORM(Base):
    """Modelo ORM para miembros de un equipo."""

    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("team_id", "slack_user_id"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    slack_user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=MemberRole.DEVELOPER.value)

    team: Mapped[TeamORM] = relationship(back_populates="members")
    standup_responses: Mapped[list["StandupResponseORM"]] = relationship(back_populates="member")

    def to_domain(self) -> MemberDomain:
        return MemberDomain(
            id=self.id,
            team_id=self.team_id,
            slack_user_id=self.slack_user_id,
            display_name=self.display_name,
            role=MemberRole(self.role),
        )

    @classmethod
    def from_domain(cls, member: MemberDomain) -> "MemberORM":
        return cls(
            id=member.id,
            team_id=member.team_id,
            slack_user_id=member.slack_user_id,
            display_name=member.display_name,
            role=member.role.value,
        )


class SprintORM(Base):
    """Modelo ORM para sprints."""

    __tablename__ = "sprints"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SprintStatus.PLANNING.value,
    )
    goals: Mapped[str] = mapped_column(String(1000), default="")

    team: Mapped[TeamORM] = relationship(back_populates="sprints")
    standup_sessions: Mapped[list["StandupSessionORM"]] = relationship(back_populates="sprint")

    def to_domain(self) -> SprintDomain:
        return SprintDomain(
            id=self.id,
            team_id=self.team_id,
            name=self.name,
            start_date=datetime.combine(self.start_date, datetime.min.time()),
            end_date=datetime.combine(self.end_date, datetime.min.time()),
            status=SprintStatus(self.status),
            goals=self.goals,
        )

    @classmethod
    def from_domain(cls, sprint: SprintDomain) -> "SprintORM":
        return cls(
            id=sprint.id,
            team_id=sprint.team_id,
            name=sprint.name,
            start_date=sprint.start_date.date(),
            end_date=sprint.end_date.date(),
            status=sprint.status.value,
            goals=sprint.goals,
        )


class StandupSessionORM(Base):
    """Modelo ORM para sesiones de standup."""

    __tablename__ = "standup_sessions"
    __table_args__ = (
        UniqueConstraint("team_id", "date"),
        {"comment": "Índice para búsqueda por equipo y fecha"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    sprint_id: Mapped[UUID | None] = mapped_column(ForeignKey("sprints.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SessionStatus.OPEN.value,
    )
    slack_channel_id: Mapped[str] = mapped_column(String(50), nullable=False)
    slack_thread_ts: Mapped[str] = mapped_column(String(50), default="")

    team: Mapped[TeamORM] = relationship(back_populates="standup_sessions")
    sprint: Mapped[SprintORM | None] = relationship(back_populates="standup_sessions")
    responses: Mapped[list["StandupResponseORM"]] = relationship(back_populates="session")

    def to_domain(self) -> StandupSessionDomain:
        return StandupSessionDomain(
            id=self.id,
            team_id=self.team_id,
            sprint_id=self.sprint_id,
            date=datetime.combine(self.date, datetime.min.time()),
            status=SessionStatus(self.status),
            slack_channel_id=self.slack_channel_id,
            slack_thread_ts=self.slack_thread_ts,
        )

    @classmethod
    def from_domain(cls, session: StandupSessionDomain) -> "StandupSessionORM":
        return cls(
            id=session.id,
            team_id=session.team_id,
            sprint_id=session.sprint_id,
            date=session.date.date(),
            status=session.status.value,
            slack_channel_id=session.slack_channel_id,
            slack_thread_ts=session.slack_thread_ts,
        )


class StandupResponseORM(Base):
    """Modelo ORM para respuestas de standup."""

    __tablename__ = "standup_responses"
    __table_args__ = (UniqueConstraint("session_id", "member_id"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    session_id: Mapped[UUID] = mapped_column(ForeignKey("standup_sessions.id"), nullable=False)
    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    yesterday: Mapped[str] = mapped_column(String(2000), nullable=False)
    today: Mapped[str] = mapped_column(String(2000), nullable=False)
    blockers: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    session: Mapped[StandupSessionORM] = relationship(back_populates="responses")
    member: Mapped[MemberORM] = relationship(back_populates="standup_responses")

    def to_domain(self) -> StandupResponseDomain:
        return StandupResponseDomain(
            id=self.id,
            session_id=self.session_id,
            member_id=self.member_id,
            yesterday=self.yesterday,
            today=self.today,
            blockers=self.blockers,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, response: StandupResponseDomain) -> "StandupResponseORM":
        return cls(
            id=response.id,
            session_id=response.session_id,
            member_id=response.member_id,
            yesterday=response.yesterday,
            today=response.today,
            blockers=response.blockers,
            created_at=response.created_at,
        )


class PullRequestORM(Base):
    """Modelo ORM para pull requests."""

    __tablename__ = "pull_requests"
    __table_args__ = (
        UniqueConstraint("team_id", "repository", "pr_number"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    pr_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    lead_time_hours: Mapped[float | None] = mapped_column(nullable=True)

    team: Mapped[TeamORM] = relationship(back_populates="pull_requests")

    def to_domain(self) -> PullRequestDomain:
        return PullRequestDomain(
            id=self.id,
            team_id=self.team_id,
            repository=self.repository,
            pr_number=self.pr_number,
            title=self.title,
            author=self.author,
            state=self.state,
            created_at=self.created_at,
            updated_at=self.updated_at,
            merged_at=self.merged_at,
            reviewers=list(self.reviewers or []),
            lead_time_hours=self.lead_time_hours,
        )

    @classmethod
    def from_domain(cls, pr: PullRequestDomain) -> "PullRequestORM":
        return cls(
            id=pr.id,
            team_id=pr.team_id,
            repository=pr.repository,
            pr_number=pr.pr_number,
            title=pr.title,
            author=pr.author,
            state=pr.state,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
            merged_at=pr.merged_at,
            reviewers=list(pr.reviewers or []),
            lead_time_hours=pr.lead_time_hours,
        )


class IssueORM(Base):
    """Modelo ORM para issues de GitHub."""

    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("team_id", "repository", "issue_number"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_number: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    labels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    assignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped[TeamORM] = relationship(back_populates="issues")

    def to_domain(self) -> IssueDomain:
        return IssueDomain(
            id=self.id,
            team_id=self.team_id,
            repository=self.repository,
            issue_number=self.issue_number,
            title=self.title,
            state=self.state,
            labels=list(self.labels or []),
            assignee=self.assignee,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, issue: IssueDomain) -> "IssueORM":
        return cls(
            id=issue.id,
            team_id=issue.team_id,
            repository=issue.repository,
            issue_number=issue.issue_number,
            title=issue.title,
            state=issue.state,
            labels=list(issue.labels or []),
            assignee=issue.assignee,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )


class RiskORM(Base):
    """Modelo ORM para riesgos detectados."""

    __tablename__ = "risks"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ref: Mapped[dict] = mapped_column(JSONB, default=dict)
    resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    team: Mapped[TeamORM] = relationship(back_populates="risks")

    def to_domain(self) -> RiskDomain:
        return RiskDomain(
            id=self.id,
            team_id=self.team_id,
            type=RiskType(self.type),
            description=self.description,
            severity=Severity(self.severity),
            source_ref=dict(self.source_ref or {}),
            resolved=self.resolved,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, risk: RiskDomain) -> "RiskORM":
        return cls(
            id=risk.id,
            team_id=risk.team_id,
            type=risk.type.value,
            description=risk.description,
            severity=risk.severity.value,
            source_ref=dict(risk.source_ref or {}),
            resolved=risk.resolved,
            created_at=risk.created_at,
        )


class MetricSnapshotORM(Base):
    """Modelo ORM para snapshots de métricas."""

    __tablename__ = "metric_snapshots"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(nullable=False)
    snapshot_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    team: Mapped[TeamORM] = relationship(back_populates="metric_snapshots")

    def to_domain(self) -> MetricSnapshotDomain:
        return MetricSnapshotDomain(
            id=self.id,
            team_id=self.team_id,
            metric_type=self.metric_type,
            date=datetime.combine(self.date, datetime.min.time()),
            value=self.value,
            metadata=dict(self.snapshot_metadata or {}),
        )

    @classmethod
    def from_domain(cls, snapshot: MetricSnapshotDomain) -> "MetricSnapshotORM":
        return cls(
            id=snapshot.id,
            team_id=snapshot.team_id,
            metric_type=snapshot.metric_type,
            date=snapshot.date.date(),
            value=snapshot.value,
            snapshot_metadata=dict(snapshot.metadata or {}),
        )
