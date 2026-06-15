"""Módulo: notification_service.

Servicio de aplicación para enviar notificaciones a Slack.
"""

from __future__ import annotations

from uuid import UUID

from src.domain.models import PullRequest, Risk
from src.infrastructure.slack_client import SlackNotifier


class NotificationService:
    """Envía recordatorios, resúmenes y alertas a Slack."""

    def __init__(self, slack_notifier: SlackNotifier):
        self._notifier = slack_notifier

    async def send_standup_reminder(self, channel_id: str) -> str:
        """Envía recordatorio de standup con botón."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "¡Buenos días! Es hora del daily standup. 🤖",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Responder Standup",
                        },
                        "action_id": "standup_button_click",
                        "style": "primary",
                    }
                ],
            },
        ]
        result = await self._notifier.send_message(
            channel=channel_id,
            text="¡Buenos días! Es hora del daily standup.",
            blocks=blocks,
        )
        return result.get("ts", "")

    async def send_daily_summary(self, channel_id: str, summary: str) -> None:
        """Envía el resumen diario al canal."""
        await self._notifier.send_message(
            channel=channel_id,
            text=summary,
        )

    async def notify_risk(self, channel_id: str, risk: Risk) -> None:
        """Envía una alerta de riesgo."""
        text = f"⚠️ Riesgo [{risk.severity.value}]: {risk.description}"
        await self._notifier.send_message(channel=channel_id, text=text)

    async def send_stale_pr_alert(
        self, channel_id: str, pr: PullRequest
    ) -> None:
        """Envía una alerta de PR stale."""
        text = (
            f"🚨 PR stale: #{pr.pr_number} {pr.title} en {pr.repository} "
            f"— @{pr.author}"
        )
        await self._notifier.send_message(channel=channel_id, text=text)
