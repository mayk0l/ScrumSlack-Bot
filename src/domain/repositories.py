"""Módulo: repositories.

Puertos (interfaces abstractas) que la infraestructura implementará.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.domain.models import (
    Member,
    MetricSnapshot,
    PullRequest,
    Risk,
    Sprint,
    SprintStatus,
    StandupResponse,
    StandupSession,
    SessionStatus,
    Team,
)


class TeamRepository(ABC):
    """Puerto para persistencia de equipos."""

    @abstractmethod
    async def get_by_id(self, team_id: UUID) -> Team | None: ...

    @abstractmethod
    async def save(self, team: Team) -> Team: ...

    @abstractmethod
    async def get_all(self) -> list[Team]: ...


class MemberRepository(ABC):
    """Puerto para persistencia de miembros."""

    @abstractmethod
    async def get_by_id(self, member_id: UUID) -> Member | None: ...

    @abstractmethod
    async def get_by_slack_user_id(self, team_id: UUID, slack_user_id: str) -> Member | None: ...

    @abstractmethod
    async def get_by_team(self, team_id: UUID) -> list[Member]: ...

    @abstractmethod
    async def save(self, member: Member) -> Member: ...


class StandupSessionRepository(ABC):
    """Puerto para persistencia de sesiones de standup."""

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> StandupSession | None: ...

    @abstractmethod
    async def get_today_session(self, team_id: UUID, date: date) -> StandupSession | None: ...

    @abstractmethod
    async def save(self, session: StandupSession) -> StandupSession: ...

    @abstractmethod
    async def update_status(self, session_id: UUID, status: SessionStatus) -> None: ...


class StandupResponseRepository(ABC):
    """Puerto para persistencia de respuestas de standup."""

    @abstractmethod
    async def save(self, response: StandupResponse) -> StandupResponse: ...

    @abstractmethod
    async def get_by_session(self, session_id: UUID) -> list[StandupResponse]: ...

    @abstractmethod
    async def get_by_member_and_session(
        self, member_id: UUID, session_id: UUID
    ) -> StandupResponse | None: ...


class PullRequestRepository(ABC):
    """Puerto para persistencia de pull requests."""

    @abstractmethod
    async def save(self, pr: PullRequest) -> PullRequest: ...

    @abstractmethod
    async def upsert(self, pr: PullRequest) -> PullRequest: ...

    @abstractmethod
    async def get_open_by_team(self, team_id: UUID) -> list[PullRequest]: ...

    @abstractmethod
    async def get_stale_prs(self, team_id: UUID, hours_threshold: int = 24) -> list[PullRequest]: ...


class SprintRepository(ABC):
    """Puerto para persistencia de sprints."""

    @abstractmethod
    async def get_active(self, team_id: UUID) -> Sprint | None: ...

    @abstractmethod
    async def save(self, sprint: Sprint) -> Sprint: ...

    @abstractmethod
    async def update_status(self, sprint_id: UUID, status: SprintStatus) -> None: ...


class RiskRepository(ABC):
    """Puerto para persistencia de riesgos."""

    @abstractmethod
    async def save(self, risk: Risk) -> Risk: ...

    @abstractmethod
    async def get_active_by_team(self, team_id: UUID) -> list[Risk]: ...

    @abstractmethod
    async def resolve(self, risk_id: UUID) -> None: ...


class MetricRepository(ABC):
    """Puerto para persistencia de métricas."""

    @abstractmethod
    async def save(self, snapshot: MetricSnapshot) -> MetricSnapshot: ...

    @abstractmethod
    async def get_by_sprint(self, team_id: UUID, sprint_id: UUID) -> list[MetricSnapshot]: ...

    @abstractmethod
    async def get_latest(self, team_id: UUID, metric_type: str) -> MetricSnapshot | None: ...
