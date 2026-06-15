"""Módulo: test_standup_service."""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from src.application.standup_service import StandupService
from src.domain.exceptions import StandupAlreadyRespondedError
from src.domain.models import Member, SessionStatus, StandupResponse, StandupSession


class FakeMemberRepository:
    def __init__(self):
        self._data: dict = {}

    async def get_by_id(self, member_id):
        return self._data.get(member_id)

    async def get_by_slack_user_id(self, team_id, slack_user_id):
        for member in self._data.values():
            if member.slack_user_id == slack_user_id and member.team_id == team_id:
                return member
        return None

    async def get_by_team(self, team_id):
        return [m for m in self._data.values() if m.team_id == team_id]

    async def save(self, member):
        self._data[member.id] = member
        return member


class FakeSessionRepository:
    def __init__(self):
        self._data: dict = {}

    async def get_by_id(self, session_id):
        return self._data.get(session_id)

    async def get_today_session(self, team_id, date):
        for session in self._data.values():
            if session.team_id == team_id and session.date.date() == date:
                return session
        return None

    async def save(self, session):
        self._data[session.id] = session
        return session

    async def update_status(self, session_id, status):
        session = self._data.get(session_id)
        if session:
            session.status = status


class FakeResponseRepository:
    def __init__(self):
        self._data: dict = {}

    async def save(self, response):
        self._data[response.id] = response
        return response

    async def get_by_session(self, session_id):
        return [r for r in self._data.values() if r.session_id == session_id]

    async def get_by_member_and_session(self, member_id, session_id):
        for r in self._data.values():
            if r.member_id == member_id and r.session_id == session_id:
                return r
        return None


@pytest.fixture
def service():
    return StandupService(
        session_repo=FakeSessionRepository(),
        response_repo=FakeResponseRepository(),
        member_repo=FakeMemberRepository(),
    )


@pytest.mark.asyncio
async def test_submit_response_creates_member_and_session(service):
    team_id = uuid4()
    response = await service.submit_response(
        team_id=team_id,
        slack_user_id="U1",
        yesterday="Ayer",
        today="Hoy",
        blockers="",
        slack_channel_id="C1",
    )
    assert response.yesterday == "Ayer"
    assert response.today == "Hoy"


@pytest.mark.asyncio
async def test_double_submit_raises(service):
    team_id = uuid4()
    await service.submit_response(
        team_id=team_id,
        slack_user_id="U1",
        yesterday="Ayer",
        today="Hoy",
        blockers="",
        slack_channel_id="C1",
    )
    with pytest.raises(StandupAlreadyRespondedError):
        await service.submit_response(
            team_id=team_id,
            slack_user_id="U1",
            yesterday="Ayer 2",
            today="Hoy 2",
            blockers="",
            slack_channel_id="C1",
        )


@pytest.mark.asyncio
async def test_get_missing_members(service):
    team_id = uuid4()
    await service.submit_response(
        team_id=team_id,
        slack_user_id="U1",
        yesterday="Ayer",
        today="Hoy",
        blockers="",
        slack_channel_id="C1",
    )

    member2 = Member(team_id=team_id, slack_user_id="U2", display_name="Bob")
    await service._member_repo.save(member2)

    missing = await service.get_missing_members(team_id, "C1")
    assert len(missing) == 1
    assert missing[0].slack_user_id == "U2"


@pytest.mark.asyncio
async def test_close_session(service):
    team_id = uuid4()
    await service.submit_response(
        team_id=team_id,
        slack_user_id="U1",
        yesterday="Ayer",
        today="Hoy",
        blockers="",
        slack_channel_id="C1",
    )
    await service.close_session(team_id, "C1")
    session = await service.get_or_create_today_session(team_id, "C1")
    assert session.status == SessionStatus.CLOSED
