"""Módulo: jobs.

Tareas en segundo plano (cron/scheduler).
"""

from __future__ import annotations

from uuid import UUID
from slack_sdk.web.async_client import AsyncWebClient

from src.config import settings
from src.application.github_service import GitHubService
from src.application.notification_service import NotificationService
from src.application.risk_service import RiskService
from src.application.standup_service import StandupService
from src.infrastructure.slack_client import SlackNotifier
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


async def send_standup_reminder(maker) -> None:
    async with maker() as session:
        team_repo = TeamRepositoryImpl(session)
        teams = await team_repo.get_all()
        for team in teams:
            slack = AsyncWebClient(token=team.slack_bot_token)
            notifier = SlackNotifier(slack)
            service = NotificationService(notifier)
            await service.send_standup_reminder(team.standup_channel_id)


async def send_daily_summary(maker, github_client) -> None:
    async with maker() as session:
        team_repo = TeamRepositoryImpl(session)
        standup_repo = StandupSessionRepositoryImpl(session)
        response_repo = StandupResponseRepositoryImpl(session)
        member_repo = MemberRepositoryImpl(session)
        pr_repo = PullRequestRepositoryImpl(session)
        risk_repo = RiskRepositoryImpl(session)
        metric_repo = MetricRepositoryImpl(session)

        standup_service = StandupService(
            session_repo=standup_repo,
            response_repo=response_repo,
            member_repo=member_repo,
        )
        github_service = GitHubService(github_client, pr_repo)
        risk_service = RiskService(risk_repo, pr_repo, response_repo, standup_repo)
        sprint_service = __import__(
            "src.application.sprint_service", fromlist=["SprintService"]
        ).SprintService(sprint_repo=SprintRepositoryImpl(session), metric_repo=metric_repo)
        
        valuelist_svc = __import__(
            "src.application.valuelist_excel_service", fromlist=["ValuelistExcelService"]
        ).ValuelistExcelService(settings.excel_file_path)
        
        report_service = __import__(
            "src.application.report_service", fromlist=["ReportService"]
        ).ReportService(standup_service, github_service, risk_service, ai_client=None, valuelist_service=valuelist_svc)

        teams = await team_repo.get_all()
        for team in teams:
            slack = AsyncWebClient(token=team.slack_bot_token)
            notifier = SlackNotifier(slack)
            notification_service = NotificationService(notifier)
            summary = await report_service.generate_daily_summary(
                team.id, team.standup_channel_id
            )
            await notification_service.send_daily_summary(
                team.standup_channel_id, summary
            )


async def sync_github(maker, github_client) -> None:
    async with maker() as session:
        team_repo = TeamRepositoryImpl(session)
        pr_repo = PullRequestRepositoryImpl(session)
        github_service = GitHubService(github_client, pr_repo)
        teams = await team_repo.get_all()
        for team in teams:
            if settings.github_default_org:
                await github_service.sync_pull_requests(
                    team.id,
                    settings.github_default_org,
                    [settings.github_default_org],
                )


async def detect_risks(maker) -> None:
    async with maker() as session:
        standup_repo = StandupSessionRepositoryImpl(session)
        response_repo = StandupResponseRepositoryImpl(session)
        pr_repo = PullRequestRepositoryImpl(session)
        risk_repo = RiskRepositoryImpl(session)
        team_repo = TeamRepositoryImpl(session)
        risk_service = RiskService(risk_repo, pr_repo, response_repo, standup_repo)
        teams = await team_repo.get_all()
        for team in teams:
            await risk_service.detect_risks(team.id)
