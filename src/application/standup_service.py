"""Módulo: standup_service.

Servicio de aplicación para gestionar sesiones y respuestas de standup.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from src.domain.exceptions import StandupAlreadyRespondedError
from src.domain.models import Member, StandupResponse, StandupSession
from src.domain.repositories import (
    MemberRepository,
    StandupResponseRepository,
    StandupSessionRepository,
)


class StandupService:
    """Orquesta la lógica de negocio del standup diario."""

    def __init__(
        self,
        session_repo: StandupSessionRepository,
        response_repo: StandupResponseRepository,
        member_repo: MemberRepository,
    ):
        self._session_repo = session_repo
        self._response_repo = response_repo
        self._member_repo = member_repo

    async def get_or_create_today_session(
        self, team_id: UUID, slack_channel_id: str
    ) -> StandupSession:
        """Obtiene o crea la sesión de standup del día para un equipo."""
        today = date.today()
        session = await self._session_repo.get_today_session(team_id, today)
        if session is not None:
            return session
        new_session = StandupSession(
            team_id=team_id,
            date=datetime.now(timezone.utc),
            slack_channel_id=slack_channel_id,
        )
        return await self._session_repo.save(new_session)

    async def submit_response(
        self,
        team_id: UUID,
        slack_user_id: str,
        yesterday: str,
        today: str,
        blockers: str,
        slack_channel_id: str,
    ) -> StandupResponse:
        """Registra la respuesta de un miembro al standup de hoy."""
        member = await self._member_repo.get_by_slack_user_id(
            team_id, slack_user_id
        )
        if member is None:
            member = Member(
                team_id=team_id,
                slack_user_id=slack_user_id,
                display_name=slack_user_id,
            )
            member = await self._member_repo.save(member)

        session = await self.get_or_create_today_session(team_id, slack_channel_id)
        existing = await self._response_repo.get_by_member_and_session(
            member.id, session.id
        )
        if existing is not None:
            raise StandupAlreadyRespondedError()

        response = StandupResponse(
            session_id=session.id,
            member_id=member.id,
            yesterday=yesterday,
            today=today,
            blockers=blockers,
        )
        return await self._response_repo.save(response)

    async def get_today_responses(self, team_id: UUID, slack_channel_id: str) -> list[StandupResponse]:
        """Obtiene las respuestas del standup de hoy."""
        session = await self.get_or_create_today_session(team_id, slack_channel_id)
        return await self._response_repo.get_by_session(session.id)

    async def get_missing_members(
        self, team_id: UUID, slack_channel_id: str
    ) -> list[Member]:
        """Retorna los miembros del equipo que aún no responden hoy."""
        session = await self.get_or_create_today_session(team_id, slack_channel_id)
        responses = await self._response_repo.get_by_session(session.id)
        responded_member_ids = {response.member_id for response in responses}
        members = await self._member_repo.get_by_team(team_id)
        return [
            member for member in members if member.id not in responded_member_ids
        ]

    async def close_session(self, team_id: UUID, slack_channel_id: str) -> None:
        """Cierra la sesión de standup del día."""
        session = await self.get_or_create_today_session(team_id, slack_channel_id)
        from src.domain.models import SessionStatus
        await self._session_repo.update_status(session.id, SessionStatus.CLOSED)
