"""Módulo: modals.

Construcción y registro de modales de Slack.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp


from src.interfaces.slack.template_loader import (
    build_standup_modal,
    build_crear_tarea_modal,
    build_editar_selector_modal,
    build_editar_tarea_modal,
    build_bitacora_completa_modal
)

from src.application.standup_service import StandupService
from src.infrastructure.repositories.standup_repo import StandupSessionRepositoryImpl, StandupResponseRepositoryImpl
from src.infrastructure.repositories.member_repo import MemberRepositoryImpl

def register_modals(app: AsyncApp, services: dict) -> None:
    """Registra el handler de envío del modal de standup."""


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

        from src.container import get_container
        container = get_container()
        async with container.uow() as uow:
            await uow.standup_svc.submit_response(
                team_id=team_id,
                slack_user_id=user_id,
                yesterday=yesterday,
                today=today,
                blockers=blockers,
                slack_channel_id=channel_id,
            )
            await session.commit()

    @app.view("crear_tarea_submission")
    async def handle_crear_tarea_submission(ack, body, view, client):
        await ack()
        values = view["state"]["values"]
        oe_id = values["oe_block"]["oe_input"]["selected_option"]["value"]
        desc = values["desc_block"]["desc_input"]["value"]
        resp_id = values["resp_block"]["resp_input"]["selected_user"]
        
        try:
            user_info = await client.users_info(user=resp_id)
            resp = user_info["user"].get("real_name") or user_info["user"].get("name")
        except Exception as e:
            # Fallback if users:read scope is missing
            print(f"Error fetching user info: {e}")
            resp = f"<@{resp_id}>"
            
        start = values["start_block"]["start_input"]["value"]
        end = values["end_block"]["end_input"]["value"]
        
        entregable = ""
        if "entregable_block" in values and "entregable_input" in values["entregable_block"]:
            entregable = values["entregable_block"]["entregable_input"].get("value") or ""
            
        comentarios = ""
        if "comentarios_block" in values and "comentarios_input" in values["comentarios_block"]:
            comentarios = values["comentarios_block"]["comentarios_input"].get("value") or ""

        from src.container import get_container
        valuelist_svc = get_container().valuelist_svc
        
        success = await valuelist_svc.create_task(oe_id, desc, resp, start, end, entregable, comentarios)
        
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
            from src.container import get_container
            valuelist_svc = get_container().valuelist_svc
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
            await ack(
                response_action="errors",
                errors={"seleccion_block": "La bitácora ahora se edita con el comando /editar-bitacora."}
            )
        else:
            await ack(
                response_action="errors",
                errors={"tipo_block": "Edición de Evidencia en desarrollo."}
            )

    @app.view("editar_tarea_submission")
    async def handle_editar_tarea_submission(ack, body, view, client):
        await ack()
        task_id = view["private_metadata"]
        values = view["state"]["values"]
        
        delete_opts = values["delete_block"]["delete_input"].get("selected_options", [])
        should_delete = len(delete_opts) > 0 and delete_opts[0]["value"] == "delete"
        
        from src.container import get_container
        valuelist_svc = get_container().valuelist_svc
        
        if should_delete:
            await valuelist_svc.delete_task_by_id(task_id)
        else:
            desc = values["desc_block"]["desc_input"]["value"]
            resp_id = values["resp_block"]["resp_input"]["selected_user"]
            
            try:
                user_info = await client.users_info(user=resp_id)
                resp = user_info["user"].get("real_name") or user_info["user"].get("name")
            except Exception as e:
                print(f"Error fetching user info: {e}")
                resp = f"<@{resp_id}>"
                
            start = values["start_block"]["start_input"]["value"]
            end = values["end_block"]["end_input"]["value"]
            
            entregable = ""
            if "entregable_block" in values and "entregable_input" in values["entregable_block"]:
                entregable = values["entregable_block"]["entregable_input"].get("value") or ""
                
            comentarios = ""
            if "comentarios_block" in values and "comentarios_input" in values["comentarios_block"]:
                comentarios = values["comentarios_block"]["comentarios_input"].get("value") or ""
                
            await valuelist_svc.update_task_details(task_id, desc, resp, start, end, entregable, comentarios)

    @app.view("bitacora_completa_submission")
    async def handle_bitacora_completa_submission(ack, body, view, client):
        await ack()
        values = view["state"]["values"]
        
        updates = {}
        new_oe = ""
        
        for block_id, block_data in values.items():
            for action_id, action_data in block_data.items():
                val = action_data.get("value", "")
                
                if action_id == "proyecto_input":
                    updates["PROYECTO"] = val
                elif action_id == "og_input":
                    updates["OG"] = val
                elif action_id == "nuevo_oe_input":
                    new_oe = val
                elif action_id.endswith("_input") and action_id.startswith("OE"):
                    # action_id looks like "OE1_input"
                    oe_id = action_id.replace("_input", "")
                    updates[oe_id] = val
                    
        from src.container import get_container
        valuelist_svc = get_container().valuelist_svc
        
        success = await valuelist_svc.update_bitacora_full(updates, new_oe)
        
        # Optional notify
        # user_id = body["user"]["id"]
        # await client.chat_postMessage(channel=user_id, text="✅ Bitácora actualizada y estilos aplicados.")
