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
        user_id = body["user"]["id"]
        from src.container import get_container
        container = get_container()
        try:
            user_info = await client.users_info(user=user_id)
            real_name = user_info["user"].get("real_name") or user_info["user"].get("name")
            tasks = await container.valuelist_svc.get_my_tasks(real_name)
        except Exception:
            tasks = []
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_standup_modal(tasks),
        )

    @app.event("app_home_opened")
    async def handle_app_home_opened(event, client):
        user_id = event["user"]
        
        from src.container import get_container
        container = get_container()
        
        try:
            user_info = await client.users_info(user=user_id)
            real_name = user_info["user"].get("real_name") or user_info["user"].get("name")
            tasks = await container.valuelist_svc.get_my_tasks(real_name)
        except Exception:
            tasks = []
            
        summary = await container.valuelist_svc.get_bitacora_summary()
        proyecto = summary.get("proyecto", "ScrumSlack Bot")
        
        from src.interfaces.slack.template_loader import build_app_home
        view = build_app_home(proyecto, tasks)
        
        await client.views_publish(
            user_id=user_id,
            view=view
        )

    @app.action("home_crear_tarea")
    async def handle_home_crear_tarea(ack, body, client):
        await ack()
        from src.container import get_container
        summary = await get_container().valuelist_svc.get_bitacora_summary()
        oes = summary.get("oe", [])
        from src.interfaces.slack.template_loader import build_crear_tarea_modal
        await client.views_open(trigger_id=body["trigger_id"], view=build_crear_tarea_modal(oes))

    @app.action("home_actualizar_avance")
    async def handle_home_actualizar_avance(ack, body, client):
        await ack()
        from src.container import get_container
        options = await get_container().valuelist_svc.get_all_edit_options()
        tareas = options.get("tareas", [])
        from src.interfaces.slack.template_loader import build_avance_modal
        await client.views_open(trigger_id=body["trigger_id"], view=build_avance_modal(tareas))
        
    @app.action("home_hacer_standup")
    async def handle_home_hacer_standup(ack, body, client):
        await ack()
        user_id = body["user"]["id"]
        from src.container import get_container
        container = get_container()
        try:
            user_info = await client.users_info(user=user_id)
            real_name = user_info["user"].get("real_name") or user_info["user"].get("name")
            tasks = await container.valuelist_svc.get_my_tasks(real_name)
        except Exception:
            tasks = []
        from src.interfaces.slack.template_loader import build_standup_modal
        await client.views_open(trigger_id=body["trigger_id"], view=build_standup_modal(tasks))

    @app.action("update_task_click")
    async def handle_update_task_click(ack, body, client):
        await ack()
        val = body["actions"][0]["value"]
        task_id, progress_str = val.split("|")
        progress = float(progress_str)
        
        from src.interfaces.slack.template_loader import build_avance_individual_modal
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_avance_individual_modal(task_id, progress)
        )

    @app.event("message")
    async def handle_message_events(event, say, client, logger):
        # Prevent bot from responding to its own messages or normal text
        if event.get("bot_id"):
            return
            
        files = event.get("files", [])
        if files:
            for f in files:
                name = f.get("name", "")
                if name.endswith(".xlsx") or "project_tracking" in name:
                    channel_type = event.get("channel_type")
                    if channel_type == "im":
                        file_url = f.get("url_private_download")
                        if not file_url:
                            continue
                            
                        import httpx
                        from src.config import settings
                        
                        try:
                            # Slack requires Bearer token for file downloads
                            headers = {"Authorization": f"Bearer {client.token}"}
                            async with httpx.AsyncClient() as http_client:
                                resp = await http_client.get(file_url, headers=headers)
                                resp.raise_for_status()
                                
                            from src.container import get_container
                            container = get_container()
                            is_valid, err_msg = await container.valuelist_svc.validate_excel_file(resp.content)
                            
                            if not is_valid:
                                await say(f"⚠️ *Excel no válido:* Tu archivo no pudo ser importado debido al siguiente error:\n\n> `{err_msg}`\n\nPor favor, corrígelo y vuelve a intentarlo para evitar dañar la base de datos.")
                                return
                                
                            with open(settings.excel_file_path, "wb") as file_out:
                                file_out.write(resp.content)
                            await say("✅ *¡Éxito!* He actualizado mi base de datos interna con el archivo Excel que me enviaste. Los modales y comandos ya están sincronizados y usaré esta versión como la principal.")
                        except Exception as e:
                            logger.error(f"Error downloading file: {e}")
                            await say(f"❌ Ocurrió un error descargando el archivo: {e}")
