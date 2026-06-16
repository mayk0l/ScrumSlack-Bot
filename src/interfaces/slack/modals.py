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

def build_editar_selector_modal(grouped_options: dict) -> dict:
    option_groups = []
    
    # Asegurar máximo 100 opciones por grupo
    if grouped_options.get("tareas"):
        option_groups.append({
            "label": {"type": "plain_text", "text": "Tareas"},
            "options": grouped_options["tareas"][:100]
        })
        
    if grouped_options.get("bitacora"):
        option_groups.append({
            "label": {"type": "plain_text", "text": "Bitácora"},
            "options": grouped_options["bitacora"][:100]
        })
        
    # Fallback si está todo vacío
    if not option_groups:
        option_groups.append({
            "label": {"type": "plain_text", "text": "Vacío"},
            "options": [{"text": {"type": "plain_text", "text": "No hay elementos editables"}, "value": "none|none"}]
        })

    return {
        "type": "modal",
        "callback_id": "editar_selector_submission",
        "title": {"type": "plain_text", "text": "Centro de Edición"},
        "submit": {"type": "plain_text", "text": "Siguiente"},
        "blocks": [
            {
                "type": "input",
                "block_id": "seleccion_block",
                "label": {"type": "plain_text", "text": "¿Qué elemento deseas editar?"},
                "element": {
                    "type": "static_select",
                    "action_id": "seleccion_input",
                    "option_groups": option_groups
                }
            }
        ]
    }

def build_editar_tarea_modal(task: dict) -> dict:
    return {
        "type": "modal",
        "callback_id": "editar_tarea_submission",
        "private_metadata": task["id"],
        "title": {"type": "plain_text", "text": f"Editar {task['id']}"},
        "submit": {"type": "plain_text", "text": "Guardar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "desc_block",
                "label": {"type": "plain_text", "text": "Descripción"},
                "element": {"type": "plain_text_input", "action_id": "desc_input", "initial_value": task["desc"]},
            },
            {
                "type": "input",
                "block_id": "resp_block",
                "label": {"type": "plain_text", "text": "Responsable"},
                "element": {
                    "type": "static_select",
                    "action_id": "resp_input",
                    "initial_option": {"text": {"type": "plain_text", "text": task["resp"]}, "value": task["resp"]} if task["resp"] else None,
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
                "element": {"type": "plain_text_input", "action_id": "start_input", "initial_value": task["start"]},
            },
            {
                "type": "input",
                "block_id": "end_block",
                "label": {"type": "plain_text", "text": "Fecha Fin (YYYY-MM-DD)"},
                "element": {"type": "plain_text_input", "action_id": "end_input", "initial_value": task["end"]},
            },
            {
                "type": "input",
                "block_id": "delete_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Opciones de Peligro"},
                "element": {
                    "type": "checkboxes",
                    "action_id": "delete_input",
                    "options": [
                        {"text": {"type": "plain_text", "text": "🗑️ Eliminar esta tarea"}, "value": "delete"}
                    ]
                }
            }
        ],
    }

def build_editar_bitacora_modal(obj_id: str, current_desc: str) -> dict:
    return {
        "type": "modal",
        "callback_id": "editar_bitacora_submission",
        "private_metadata": obj_id,
        "title": {"type": "plain_text", "text": f"Editar {obj_id}"},
        "submit": {"type": "plain_text", "text": "Guardar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "desc_block",
                "label": {"type": "plain_text", "text": "Descripción"},
                "element": {
                    "type": "plain_text_input", 
                    "action_id": "desc_input", 
                    "initial_value": current_desc,
                    "multiline": True
                },
            }
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
        from src.config import settings
        valuelist_svc = ValuelistExcelService(settings.excel_file_path)
        
        success = await valuelist_svc.create_task(act_id, desc, resp, start, end)
        
        # Opcional: enviar mensaje al usuario o al canal de la creación
        # slack_client = app.client
        # user_id = body["user"]["id"]
        # await slack_client.chat_postMessage(channel=user_id, text=f"Tarea {act_id} creada." if success else "Error")

    @app.view("editar_selector_submission")
    async def handle_editar_selector_submission(ack, body, view):
        values = view["state"]["values"]
        seleccion = values["seleccion_block"]["seleccion_input"]["selected_option"]["value"]
        
        if seleccion == "none|none":
            await ack(response_action="errors", errors={"seleccion_block": "No hay nada válido para editar."})
            return
            
        tipo, item_id = seleccion.split("|")
        
        if tipo == "tarea":
            from src.application.valuelist_excel_service import ValuelistExcelService
            from src.config import settings
            valuelist_svc = ValuelistExcelService(settings.excel_file_path)
            task = await valuelist_svc.get_task_by_id(item_id)
            
            if task:
                await ack(
                    response_action="push",
                    view=build_editar_tarea_modal(task)
                )
            else:
                await ack(
                    response_action="errors",
                    errors={"seleccion_block": "No se encontró la tarea seleccionada."}
                )
        elif tipo == "bitacora":
            from src.application.valuelist_excel_service import ValuelistExcelService
            from src.config import settings
            valuelist_svc = ValuelistExcelService(settings.excel_file_path)
            bitacora = await valuelist_svc.get_bitacora_summary()
            current_desc = bitacora.get(item_id.lower())
            
            if current_desc is not None:
                await ack(
                    response_action="push",
                    view=build_editar_bitacora_modal(item_id, current_desc)
                )
            else:
                await ack(
                    response_action="errors",
                    errors={"seleccion_block": "ID inválido para Bitácora."}
                )
        else:
            await ack(
                response_action="errors",
                errors={"tipo_block": "Edición de Evidencia en desarrollo."}
            )

    @app.view("editar_tarea_submission")
    async def handle_editar_tarea_submission(ack, body, view):
        await ack()
        task_id = view["private_metadata"]
        values = view["state"]["values"]
        
        delete_opts = values["delete_block"]["delete_input"].get("selected_options", [])
        should_delete = len(delete_opts) > 0 and delete_opts[0]["value"] == "delete"
        
        from src.application.valuelist_excel_service import ValuelistExcelService
        from src.config import settings
        valuelist_svc = ValuelistExcelService(settings.excel_file_path)
        
        if should_delete:
            await valuelist_svc.delete_task_by_id(task_id)
        else:
            desc = values["desc_block"]["desc_input"]["value"]
            resp = values["resp_block"]["resp_input"]["selected_option"]["value"]
            start = values["start_block"]["start_input"]["value"]
            end = values["end_block"]["end_input"]["value"]
            await valuelist_svc.update_task_details(task_id, desc, resp, start, end)

    @app.view("editar_bitacora_submission")
    async def handle_editar_bitacora_submission(ack, body, view):
        await ack()
        obj_id = view["private_metadata"]
        values = view["state"]["values"]
        new_desc = values["desc_block"]["desc_input"]["value"]
        
        from src.application.valuelist_excel_service import ValuelistExcelService
        from src.config import settings
        valuelist_svc = ValuelistExcelService(settings.excel_file_path)
        await valuelist_svc.update_bitacora(obj_id, new_desc)
