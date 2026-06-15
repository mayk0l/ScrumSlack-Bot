"""Módulo: models.

Entidades de dominio para el Scrum Master Bot.
Esta capa no depende de ningún framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class SprintStatus(str, Enum):
    """Estados posibles de un sprint."""

    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"


class SessionStatus(str, Enum):
    """Estados posibles de una sesión de standup."""

    OPEN = "open"
    CLOSED = "closed"


class RiskType(str, Enum):
    """Tipos de riesgo detectables automáticamente."""

    PR_NO_REVIEW = "pr_no_review"
    CI_FAILURE = "ci_failure"
    BLOCKER = "blocker"
    STALE_BRANCH = "stale_branch"


class Severity(str, Enum):
    """Niveles de severidad de un riesgo."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemberRole(str, Enum):
    """Roles posibles de un miembro del equipo."""

    DEVELOPER = "developer"
    TECH_LEAD = "tech_lead"
    SCRUM_MASTER = "scrum_master"
    PRODUCT_OWNER = "product_owner"


@dataclass
class Team:
    """Agregado raíz que representa un equipo de trabajo."""

    name: str
    slack_bot_token: str
    github_token: str
    standup_channel_id: str
    standup_schedule_time: str = "09:00"
    timezone: str = "America/Santiago"
    id: UUID = field(default_factory=uuid4)


@dataclass
class Member:
    """Miembro de un equipo vinculado a Slack."""

    team_id: UUID
    slack_user_id: str
    display_name: str
    role: MemberRole = MemberRole.DEVELOPER
    id: UUID = field(default_factory=uuid4)


@dataclass
class Sprint:
    """Sprint activo o histórico de un equipo."""

    team_id: UUID
    name: str
    start_date: datetime
    end_date: datetime
    goals: str = ""
    status: SprintStatus = SprintStatus.PLANNING
    id: UUID = field(default_factory=uuid4)


@dataclass
class StandupSession:
    """Sesión diaria de standup para un equipo."""

    team_id: UUID
    date: datetime
    slack_channel_id: str
    status: SessionStatus = SessionStatus.OPEN
    sprint_id: UUID | None = None
    slack_thread_ts: str = ""
    id: UUID = field(default_factory=uuid4)


@dataclass
class StandupResponse:
    """Respuesta individual de un miembro en una sesión de standup."""

    session_id: UUID
    member_id: UUID
    yesterday: str
    today: str
    blockers: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)


@dataclass
class PullRequest:
    """Pull request sincronizado desde GitHub."""

    team_id: UUID
    repository: str
    pr_number: int
    title: str
    author: str
    state: str
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None = None
    reviewers: list[str] = field(default_factory=list)
    lead_time_hours: float | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class Issue:
    """Issue sincronizado desde GitHub."""

    team_id: UUID
    repository: str
    issue_number: int
    title: str
    state: str
    labels: list[str] = field(default_factory=list)
    assignee: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class Risk:
    """Riesgo detectado para un equipo."""

    team_id: UUID
    type: RiskType
    description: str
    severity: Severity
    source_ref: dict = field(default_factory=dict)
    resolved: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)


@dataclass
class MetricSnapshot:
    """Snapshot histórico de una métrica del equipo."""

    team_id: UUID
    metric_type: str
    date: datetime
    value: float
    metadata: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
