"""Módulo: modals.

Construcción y registro de modales de Slack.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp


def build_standup_modal() -> dict:
    """Construye el modal con 3 campos de texto."""
    return {
        "type": "modal",
        "callback_id": "standup_submission",
        "title": {"type": "plain_text", "text": "Daily Standup"},
        "submit": {"type": "plain_text", "text": "Enviar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "yesterday_block",
                "label": {"type": "plain_text", "text": "¿Qué hiciste ayer?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "yesterday_input",
                    "multiline": True,
                },
            },
            {
                "type": "input",
                "block_id": "today_block",
                "label": {"type": "plain_text", "text": "¿Qué harás hoy?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "today_input",
                    "multiline": True,
                },
            },
            {
                "type": "input",
                "block_id": "blockers_block",
                "label": {"type": "plain_text", "text": "¿Tienes bloqueos?"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "blockers_input",
                    "multiline": True,
                },
                "optional": True,
            },
        ],
    }


def register_modals(app: AsyncApp, services: dict) -> None:
    """Registra el handler de envío del modal de standup."""
    standup_service = services["standup_service"]

    @app.view("standup_submission")
    async def handle_standup_submission(ack, body, view):
        await ack()
        values = view["state"]["values"]
        yesterday = values["yesterday_block"]["yesterday_input"]["value"]
        today = values["today_block"]["today_input"]["value"]
        blockers = values["blockers_block"]["blockers_input"]["value"] or ""
        user_id = body["user"]["id"]

        # TODO: Resolver team_id desde contexto (cookie/db lookup)
        from uuid import UUID
        team_id = UUID(services.get("default_team_id", "00000000-0000-0000-0000-000000000000"))
        channel_id = services.get("default_channel_id", "C000")

        await standup_service.submit_response(
            team_id=team_id,
            slack_user_id=user_id,
            yesterday=yesterday,
            today=today,
            blockers=blockers,
            slack_channel_id=channel_id,
        )
