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

maker = __import__("src.infrastructure.database", fromlist=["get_async_session_maker"]).get_async_session_maker()
global_github_client = GitHubClient(settings.github_token)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    await init_db()

    from src.infrastructure.database import get_async_session_maker
    maker = get_async_session_maker()
    
    # Crear equipo por defecto para evitar errores de Foreign Key
    async with maker() as session:
        from src.infrastructure.orm_models import TeamORM
        from sqlalchemy import select
        from uuid import UUID
        
        default_team_id = UUID("00000000-0000-0000-0000-000000000000")
        stmt = select(TeamORM).where(TeamORM.id == default_team_id)
        result = await session.execute(stmt)
        if not result.scalars().first():
            new_team = TeamORM(
                id=default_team_id,
                name="Default Team",
                slack_bot_token=settings.slack_bot_token,
                github_token=settings.github_token,
                standup_channel_id=settings.standup_channel_id,
                standup_schedule_time=settings.standup_time
            )
            session.add(new_team)
            await session.commit()

    github_client = global_github_client
    scheduler = SchedulerService()

    from src.infrastructure.jobs import (
        send_standup_reminder,
        send_daily_summary,
        sync_github,
        detect_risks,
    )
    import functools

    if settings.standup_time:
        hour, minute = map(int, settings.standup_time.split(":"))
        scheduler.add_daily_job(
            functools.partial(send_standup_reminder, maker),
            hour=hour,
            minute=minute,
            timezone=settings.timezone,
            job_id="standup_reminder",
        )

    if settings.summary_time:
        hour, minute = map(int, settings.summary_time.split(":"))
        scheduler.add_daily_job(
            functools.partial(send_daily_summary, maker, github_client),
            hour=hour,
            minute=minute,
            timezone=settings.timezone,
            job_id="daily_summary",
        )

    scheduler.start()

    socket_mode_handler = None
    if settings.slack_app_token and settings.slack_app_token.startswith("xapp-"):
        from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
        socket_mode_handler = AsyncSocketModeHandler(slack_app, settings.slack_app_token)
        await socket_mode_handler.connect_async()

    yield

    if socket_mode_handler:
        await socket_mode_handler.close_async()
        
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
    "session_maker": maker,
    "github_client": global_github_client,
    "default_team_id": UUID("00000000-0000-0000-0000-000000000000"),
    "default_channel_id": settings.standup_channel_id,
}
register_handlers(slack_app, services)


@app.post("/slack/events")
async def slack_events(req: Request):
    """Endpoint para eventos de Slack."""
    return await slack_handler.handle(req)
