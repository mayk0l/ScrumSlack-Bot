"""Módulo: jobs.

Tareas en segundo plano (cron/scheduler).
"""

from __future__ import annotations

from uuid import UUID
from slack_sdk.web.async_client import AsyncWebClient

from src.config import settings
from src.container import get_container
from src.application.notification_service import NotificationService
from src.infrastructure.slack_client import SlackNotifier


async def send_standup_reminder() -> None:
    container = get_container()
    async with container.uow() as uow:
        teams = await uow.team_repo.get_all()
        for team in teams:
            slack = AsyncWebClient(token=team.slack_bot_token)
            notifier = SlackNotifier(slack)
            service = NotificationService(notifier)
            await service.send_standup_reminder(team.standup_channel_id)


async def send_daily_summary() -> None:
    container = get_container()
    async with container.uow() as uow:
        teams = await uow.team_repo.get_all()
        for team in teams:
            slack = AsyncWebClient(token=team.slack_bot_token)
            notifier = SlackNotifier(slack)
            notification_service = NotificationService(notifier)
            summary = await uow.report_svc.generate_ai_summary(
                team.id, team.standup_channel_id
            )
            await notification_service.send_daily_summary(
                team.standup_channel_id, summary
            )


async def sync_github() -> None:
    container = get_container()
    async with container.uow() as uow:
        teams = await uow.team_repo.get_all()
        for team in teams:
            if settings.github_default_org:
                await uow.github_svc.sync_pull_requests(
                    team.id,
                    settings.github_default_org,
                    [settings.github_default_org],
                )


async def detect_risks() -> None:
    container = get_container()
    async with container.uow() as uow:
        teams = await uow.team_repo.get_all()
        for team in teams:
            await uow.risk_svc.detect_risks(team.id)
