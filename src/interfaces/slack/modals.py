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

def build_crear_tarea_modal() -> dict:
    """Construye el modal para crear una nueva tarea en Valuelist."""
    return {
        "type": "modal",
        "callback_id": "crear_tarea_submission",
        "title": {"type": "plain_text", "text": "Crear Tarea"},
        "submit": {"type": "plain_text", "text": "Guardar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "id_block",
                "label": {"type": "plain_text", "text": "ID Tarea (Ej. A2.5)"},
                "element": {"type": "plain_text_input", "action_id": "id_input"},
            },
            {
                "type": "input",
                "block_id": "desc_block",
                "label": {"type": "plain_text", "text": "Descripción"},
                "element": {"type": "plain_text_input", "action_id": "desc_input"},
            },
            {
                "type": "input",
                "block_id": "resp_block",
                "label": {"type": "plain_text", "text": "Responsable"},
                "element": {
                    "type": "static_select",
                    "action_id": "resp_input",
                    "placeholder": {"type": "plain_text", "text": "Selecciona responsable"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Emiliano J."}, "value": "Emiliano J."},
                        {"text": {"type": "plain_text", "text": "Diego C."}, "value": "Diego C."}
                    ]
                },
            },
            {
                "type": "input",
                "block_id": "start_block",
                "label": {"type": "plain_text", "text": "Fecha Inicio (YYYY-MM-DD)"},
                "element": {"type": "plain_text_input", "action_id": "start_input"},
            },
            {
                "type": "input",
                "block_id": "end_block",
                "label": {"type": "plain_text", "text": "Fecha Fin (YYYY-MM-DD)"},
                "element": {"type": "plain_text_input", "action_id": "end_input"},
            },
        ],
    }

from src.application.standup_service import StandupService
from src.infrastructure.repositories.standup_repo import StandupSessionRepositoryImpl, StandupResponseRepositoryImpl
from src.infrastructure.repositories.member_repo import MemberRepositoryImpl

def register_modals(app: AsyncApp, services: dict) -> None:
    """Registra el handler de envío del modal de standup."""
    maker = services["session_maker"]

    async def _get_standup_service():
        session = maker()
        return StandupService(
            session_repo=StandupSessionRepositoryImpl(session),
            response_repo=StandupResponseRepositoryImpl(session),
            member_repo=MemberRepositoryImpl(session),
        ), session

    @app.view("standup_submission")
    async def handle_standup_submission(ack, body, view):
        await ack()
        values = view["state"]["values"]
        yesterday = values["yesterday_block"]["yesterday_input"]["value"]
        today = values["today_block"]["today_input"]["value"]
        blockers = values["blockers_block"]["blockers_input"]["value"] or ""
        user_id = body["user"]["id"]

        team_id = services.get("default_team_id", "00000000-0000-0000-0000-000000000000")
        if isinstance(team_id, str):
            from uuid import UUID
            team_id = UUID(team_id)
        channel_id = services.get("default_channel_id", "C000")

        svc, session = await _get_standup_service()
        async with session:
            await svc.submit_response(
                team_id=team_id,
                slack_user_id=user_id,
                yesterday=yesterday,
                today=today,
                blockers=blockers,
                slack_channel_id=channel_id,
            )
            await session.commit()

    @app.view("crear_tarea_submission")
    async def handle_crear_tarea_submission(ack, body, view):
        await ack()
        values = view["state"]["values"]
        act_id = values["id_block"]["id_input"]["value"]
        desc = values["desc_block"]["desc_input"]["value"]
        resp = values["resp_block"]["resp_input"]["selected_option"]["value"]
        start = values["start_block"]["start_input"]["value"]
        end = values["end_block"]["end_input"]["value"]

        from src.application.valuelist_excel_service import ValuelistExcelService
        valuelist_svc = ValuelistExcelService("excel/Bitacora-Rentabilidad-Valuelist.xlsx")
        
        success = await valuelist_svc.create_task(act_id, desc, resp, start, end)
        
        # Opcional: enviar mensaje al usuario o al canal de la creación
        # slack_client = app.client
        # user_id = body["user"]["id"]
        # await slack_client.chat_postMessage(channel=user_id, text=f"Tarea {act_id} creada." if success else "Error")
