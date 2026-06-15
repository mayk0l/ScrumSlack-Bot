"""Módulo: main.

Punto de entrada de la aplicación: FastAPI + Slack Bolt + Scheduler.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Request

from src.config import settings
from src.infrastructure.database import close_db, init_db
from src.infrastructure.github_client import GitHubClient
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
from src.infrastructure.scheduler import SchedulerService
from src.infrastructure.slack_client import create_slack_app, create_slack_handler
from src.interfaces.api.routes import router as api_router
from src.interfaces.slack.bolt_app import register_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    await init_db()

    github_client = GitHubClient(settings.github_token)
    scheduler = SchedulerService()

    # Inyección manual de dependencias para handlers programados.
    # En producción se recomienda un contenedor DI más robusto.
    from src.application.github_service import GitHubService
    from src.application.notification_service import NotificationService
    from src.application.risk_service import RiskService
    from src.application.standup_service import StandupService
    from src.infrastructure.database import get_async_session_maker
    from src.infrastructure.slack_client import SlackNotifier
    from slack_sdk.web.async_client import AsyncWebClient

    maker = get_async_session_maker()

    async def send_standup_reminder() -> None:
        async with maker() as session:
            team_repo = TeamRepositoryImpl(session)
            teams = await team_repo.get_all()
            for team in teams:
                slack = AsyncWebClient(token=team.slack_bot_token)
                notifier = SlackNotifier(slack)
                service = NotificationService(notifier)
                await service.send_standup_reminder(team.standup_channel_id)

    async def send_daily_summary() -> None:
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
            risk_service = RiskService(risk_repo, pr_repo, response_repo)
            sprint_service = __import__(
                "src.application.sprint_service", fromlist=["SprintService"]
            ).SprintService(sprint_repo=SprintRepositoryImpl(session), metric_repo=metric_repo)
            report_service = __import__(
                "src.application.report_service", fromlist=["ReportService"]
            ).ReportService(standup_service, github_service, risk_service)

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

    async def sync_github() -> None:
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

    async def detect_risks() -> None:
        async with maker() as session:
            standup_repo = StandupSessionRepositoryImpl(session)
            response_repo = StandupResponseRepositoryImpl(session)
            pr_repo = PullRequestRepositoryImpl(session)
            risk_repo = RiskRepositoryImpl(session)
            team_repo = TeamRepositoryImpl(session)
            risk_service = RiskService(risk_repo, pr_repo, response_repo)
            teams = await team_repo.get_all()
            for team in teams:
                await risk_service.detect_risks(team.id)

    if settings.standup_time:
        hour, minute = map(int, settings.standup_time.split(":"))
        scheduler.add_daily_job(
            send_standup_reminder,
            hour=hour,
            minute=minute,
            timezone=settings.timezone,
            job_id="standup_reminder",
        )

    if settings.summary_time:
        hour, minute = map(int, settings.summary_time.split(":"))
        scheduler.add_daily_job(
            send_daily_summary,
            hour=hour,
            minute=minute,
            timezone=settings.timezone,
            job_id="daily_summary",
        )

    scheduler.start()

    yield

    scheduler.shutdown(wait=False)
    await github_client.close()
    await close_db()


app = FastAPI(title="Scrum Master Bot", lifespan=lifespan)
app.include_router(api_router)

slack_app = create_slack_app(
    settings.slack_bot_token, settings.slack_signing_secret
)
slack_handler = create_slack_handler(slack_app)

services = {
    "standup_service": None,
    "report_service": None,
    "risk_service": None,
    "default_team_id": UUID("00000000-0000-0000-0000-000000000000"),
    "default_channel_id": settings.standup_channel_id,
}
register_handlers(slack_app, services)


@app.post("/slack/events")
async def slack_events(req: Request):
    """Endpoint para eventos de Slack."""
    return await slack_handler.handle(req)
