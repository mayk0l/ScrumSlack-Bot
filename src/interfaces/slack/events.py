"""Módulo: events.

Registro de eventos y acciones de Slack.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.modals import build_standup_modal


def register_events(app: AsyncApp, services: dict) -> None:
    """Registra eventos y acciones de Slack."""

    @app.event("app_mention")
    async def handle_mention(event, say):
        await say(
            "¡Hola! Usa `/scrum` para enviar tu standup o `/riesgos` para ver riesgos activos. 🤖"
        )

    @app.action("standup_button_click")
    async def handle_standup_button(ack, body, client):
        await ack()
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_standup_modal(),
        )
