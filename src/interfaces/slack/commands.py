"""Módulo: commands.

Registro de slash commands de Slack.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.modals import build_standup_modal
from src.application.standup_service import StandupService
from src.application.report_service import ReportService
from src.application.risk_service import RiskService
from src.infrastructure.repositories.standup_repo import StandupSessionRepositoryImpl, StandupResponseRepositoryImpl
from src.infrastructure.repositories.member_repo import MemberRepositoryImpl
from src.infrastructure.repositories.risk_repo import RiskRepositoryImpl
from src.infrastructure.repositories.pr_repo import PullRequestRepositoryImpl
from src.application.github_service import GitHubService
from src.application.sprint_service import SprintService
from src.application.sprint_service import SprintService
from src.infrastructure.repositories.sprint_repo import SprintRepositoryImpl
from src.infrastructure.repositories.metric_repo import MetricRepositoryImpl
from src.application.valuelist_excel_service import ValuelistExcelService
from src.config import settings


def register_commands(app: AsyncApp, services: dict) -> None:
    """Registra todos los slash commands."""
    maker = services["session_maker"]
    github_client = services["github_client"]
    default_team_id = services.get("default_team_id")
    default_channel_id = services.get("default_channel_id")

    async def _get_services():
        session = maker()
        standup_repo = StandupSessionRepositoryImpl(session)
        response_repo = StandupResponseRepositoryImpl(session)
        member_repo = MemberRepositoryImpl(session)
        risk_repo = RiskRepositoryImpl(session)
        pr_repo = PullRequestRepositoryImpl(session)
        sprint_repo = SprintRepositoryImpl(session)
        metric_repo = MetricRepositoryImpl(session)
        
        standup_svc = StandupService(
            session_repo=standup_repo,
            response_repo=response_repo,
            member_repo=member_repo,
        )
        github_svc = GitHubService(github_client, pr_repo)
        risk_svc = RiskService(risk_repo, pr_repo, response_repo, standup_repo)
        sprint_svc = SprintService(sprint_repo, metric_repo)
        valuelist_svc = ValuelistExcelService(settings.excel_file_path)
        report_svc = ReportService(standup_svc, github_svc, risk_svc, ai_client=None, valuelist_service=valuelist_svc)
        
        return {
            "standup": standup_svc, 
            "risk": risk_svc, 
            "report": report_svc, 
            "sprint": sprint_svc, 
            "member": member_repo,
            "valuelist": valuelist_svc,
            "github": github_svc
        }, session

    @app.command("/ayuda-scrum")
    async def handle_ayuda_scrum_command(ack, say):
        await ack()
        ayuda_text = (
            "🚀 *Guía Rápida de ScrumSlack Bot*\n\n"
            "Aquí tienes el flujo de trabajo para dominar el proyecto sin tocar el Excel:\n\n"
            "🎯 *1. Planificación (Bitácora)*\n"
            "• `/editar` -> Define y modifica los objetivos (`OG`, `OE1`, etc.) o ajusta detalles de tus tareas.\n"
            "• `/bitacora` -> Revisa las metas del proyecto.\n\n"
            "📝 *2. Tareas*\n"
            "• `/crear-tarea` -> Crea una nueva tarea asignándole un ID (ej. A1.1).\n"
            "• `/todas-las-tareas` -> Mira el backlog completo.\n"
            "• `/mis-tareas` -> Descubre qué tareas te tocan a ti.\n\n"
            "🏃‍♂️ *3. El Día a Día*\n"
            "• `/scrum` -> Reporta tu avance diario (Daily Standup).\n"
            "• `/avance [ID] [1-100]` -> Actualiza el progreso de una tarea (Ej. `/avance A1.1 50`).\n"
            "• `/evidencia [ID] [URL]` -> Sube el link de tu PR o documento al llegar al 100%.\n\n"
            "📊 *4. Reportes y Cierre*\n"
            "• `/progreso` -> Revisa el porcentaje de avance global de cada módulo.\n"
            "• `/reporte` -> Resumen automático del trabajo del equipo.\n"
            "• `/gantt` -> Visualiza el cronograma general.\n"
            "• `/descargar-excel` -> Baja la versión maestra y más reciente del Excel.\n\n"
            "¡A darle con todo! 🦣🛠️\n\n"
        )
        await say(ayuda_text)

    @app.command("/scrum")
    async def handle_scrum_command(ack, body, client):
        await ack()
        from src.interfaces.slack.modals import build_standup_modal
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_standup_modal(),
        )

    @app.command("/riesgos")
    async def handle_riesgos_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            risks = await svcs["risk"].get_active_risks(default_team_id)
            if risks:
                lines = [f"• [{r.severity.value}] {r.description}" for r in risks]
                text = "⚠️ Riesgos activos:\n" + "\n".join(lines)
            else:
                text = "No hay riesgos activos. 🎉"
        await say(f"{text}\n\n")

    @app.command("/bloqueos")
    async def handle_bloqueos_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            responses = await svcs["standup"].get_today_responses(
                default_team_id, default_channel_id
            )
            members = await svcs["member"].get_by_team(default_team_id)
            member_map = {m.id: m.slack_user_id for m in members}
            
            blockers = [r for r in responses if r.blockers and r.blockers.strip()]
            if blockers:
                lines = [f"• <@{member_map.get(r.member_id, 'Unknown')}>: {r.blockers}" for r in blockers]
                text = "🚫 *Bloqueos reportados hoy:*\n" + "\n".join(lines)
            else:
                text = "No hay bloqueos reportados hoy. ✅"
        await say(f"{text}\n\n")

    @app.command("/sprint")
    async def handle_sprint_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            sprint = await svcs["sprint"].get_active_sprint(default_team_id)
            if sprint:
                text = (
                    f"🏃 *Sprint activo: {sprint.name}*\n"
                    f"• Inicio: {sprint.start_date}\n"
                    f"• Fin: {sprint.end_date}\n"
                    f"• Estado: {sprint.status.value}\n"
                    f"• Objetivos: {sprint.goals or 'Sin definir'}"
                )
            else:
                text = "No hay sprint activo actualmente."
        await say(f"{text}\n\n")

    @app.command("/metricas")
    async def handle_metricas_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            sprint = await svcs["sprint"].get_active_sprint(default_team_id)
            if not sprint:
                await say("No hay sprint activo. Usa `/sprint` para verificar.")
                return
            metrics = await svcs["sprint"].get_sprint_metrics(default_team_id, sprint.id)
            metric_list = metrics.get("metrics", [])
            if metric_list:
                lines = [f"• {m['type']}: {m['value']} ({m['date']})" for m in metric_list]
                text = f"📊 *Métricas del sprint {sprint.name}:*\n" + "\n".join(lines)
            else:
                text = f"📊 Sprint *{sprint.name}* activo pero sin métricas registradas aún."
        await say(f"{text}\n\n")

    @app.command("/reporte")
    async def handle_reporte_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            summary = await svcs["report"].generate_daily_summary(
                default_team_id, default_channel_id
            )
        await say(f"{summary}\n\n")

    @app.command("/github")
    async def handle_github_command(ack, say):
        await ack()
        if not settings.github_default_org:
            await say("❌ GitHub sync no configurado (falta GITHUB_DEFAULT_ORG).")
            return
        await say("⚙️ *Sincronizando Pull Requests desde GitHub...*")
        svcs, session = await _get_services()
        async with session:
            await svcs["github"].sync_pull_requests(
                default_team_id,
                settings.github_default_org,
                [settings.github_default_org],
            )
        await say("✅ Sincronización completada.")

    @app.command("/test-standup")
    async def handle_test_standup_command(ack, body, client):
        await ack()
        from src.infrastructure.slack_client import SlackNotifier
        from src.application.notification_service import NotificationService
        
        channel_id = body.get("channel_id")
        notifier = SlackNotifier(client)
        svc = NotificationService(notifier)
        await svc.send_standup_reminder(channel_id)

    @app.command("/test-resumen")
    async def handle_test_resumen_command(ack, body, client, say):
        await ack()
        await say("⚙️ *Simulando envío automático del resumen diario...*")
        svcs, session = await _get_services()
        async with session:
            # Reusa la misma lógica del reporte, pero enviada como el servicio de notificaciones
            summary = await svcs["report"].generate_daily_summary(
                default_team_id, default_channel_id
            )
            
            from src.infrastructure.slack_client import SlackNotifier
            from src.application.notification_service import NotificationService
            channel_id = body.get("channel_id")
            notifier = SlackNotifier(client)
            notif_svc = NotificationService(notifier)
            await notif_svc.send_daily_summary(channel_id, summary)

    @app.command("/progreso")
    async def handle_progreso_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            try:
                modules = await svcs["excel"].get_module_progress()
                if modules:
                    lines = [
                        f"• *{m.get('name', 'N/A')}*: {m.get('progress', '0')}% — {m.get('status', 'N/A')}"
                        for m in modules
                    ]
                    text = "📈 *Progreso de módulos:*\n" + "\n".join(lines)
                else:
                    text = "No hay módulos registrados en la planilla."
            except FileNotFoundError:
                text = "⚠️ Planilla Excel no encontrada. Ejecuta la creación del template primero."
        await say(f"{text}\n\n")

    @app.command("/mis-tareas")
    async def handle_mis_tareas_command(ack, body, client, say):
        await ack()
        svcs, session = await _get_services()
        user_id = body.get("user_id")
        
        user_info = await client.users_info(user=user_id)
        real_name = user_info["user"].get("real_name") or user_info["user"].get("name")
        
        tasks = await svcs["valuelist"].get_my_tasks(real_name)
        if tasks:
            lines = [f"• *[{t['id']}]* {t['desc']} — {t['progress'] * 100:.0f}%" for t in tasks]
            text = f"📋 *Tus tareas asignadas:*\n" + "\n".join(lines)
        else:
            text = "No tienes tareas asignadas en la Planificación."
        await say(f"{text}\n\n")

    @app.command("/bitacora")
    async def handle_bitacora_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        summary = await svcs["valuelist"].get_bitacora_summary()
        
        if summary["og"]:
            text = f"🎯 *Objetivo General:*\n{summary['og']}\n\n"
            if summary["oe"]:
                lines = [f"• *{oe['id']}*: {oe['desc']}" for oe in summary["oe"]]
                text += "📌 *Objetivos Específicos:*\n" + "\n".join(lines)
        else:
            text = "⚠️ No se pudo leer la Bitácora o está vacía."
            
        await say(f"{text}\n\n")

    @app.command("/avance")
    async def handle_avance_command(ack, body, say):
        await ack()
        text = body.get("text", "").strip()
        parts = text.split(" ")
        
        if len(parts) < 2:
            await say("⚠️ Uso incorrecto. Ejemplo: `/avance A2.1 100`")
            return
            
        task_id = parts[0]
        try:
            progress = float(parts[1]) / 100.0 if float(parts[1]) > 1 else float(parts[1])
        except ValueError:
            await say("⚠️ El porcentaje debe ser un número (Ej: 100 o 1.0)")
            return
            
        svcs, session = await _get_services()
        success = await svcs["valuelist"].update_task_progress(task_id, progress)
        
        if success:
            await say(f"✅ ¡Avance de *{task_id}* actualizado a {progress*100:.0f}%!\nSi llegaste al 100%, no olvides usar `/evidencia {task_id} [URL]`")
        else:
            await say(f"❌ No se encontró la tarea *{task_id}* en la Planificación.")

    @app.command("/evidencia")
    async def handle_evidencia_command(ack, body, say):
        await ack()
        text = body.get("text", "").strip()
        parts = text.split(" ", 1)
        
        if len(parts) < 2:
            await say("⚠️ Uso incorrecto. Ejemplo: `/evidencia A2.1 https://github.com/pull/123`")
            return
            
        task_id = parts[0]
        url = parts[1]
        
        svcs, session = await _get_services()
        success = await svcs["valuelist"].add_evidence(task_id, url)
        
        if success:
            await say(f"🔗 Evidencia guardada para *{task_id}* en la Hoja 5.")
        else:
            await say(f"❌ No se encontró la tarea *{task_id}* para adjuntar la evidencia.")

    @app.command("/crear-tarea")
    async def handle_crear_tarea_command(ack, body, client):
        await ack()
        from src.interfaces.slack.modals import build_crear_tarea_modal
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_crear_tarea_modal(),
        )

    @app.command("/gantt")
    async def handle_gantt_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        gantt_text = await svcs["valuelist"].generate_gantt()
        await say(f"📊 *Diagrama de Gantt (Planificación)*\n\n{gantt_text}")

    @app.command("/descargar-excel")
    async def handle_descargar_excel_command(ack, body, client, say):
        await ack()
        try:
            channel_id = body.get("channel_id")
            await client.files_upload_v2(
                channel=channel_id,
                file=settings.excel_file_path,
                title="project_tracking.xlsx",
                initial_comment="📂 Aquí tienes la última versión del Excel de Valuelist actualizada con los datos de Slack."
            )
        except Exception as e:
            await say(f"❌ Error al enviar el archivo: {e}")

    @app.command("/editar")
    async def handle_editar_command(ack, body, client):
        await ack()
        svcs, _ = await _get_services()
        options = await svcs["valuelist"].get_all_edit_options()
        
        from src.interfaces.slack.modals import build_editar_selector_modal
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_editar_selector_modal(options),
        )

    @app.command("/todas-las-tareas")
    async def handle_todas_las_tareas_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        grouped_tasks = await svcs["valuelist"].get_all_active_tasks()
        
        if not grouped_tasks:
            await say("🎉 ¡No hay tareas activas en el Excel!")
            return
            
        blocks = [{"type": "header", "text": {"type": "plain_text", "text": "🌐 Visión Global de Tareas Activas"}}]
        
        for resp, tasks in grouped_tasks.items():
            task_list = "\n".join(tasks)
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{resp}*\n{task_list}"}
            })
            
        blocks.append({"type": "divider"})
        await say(blocks=blocks)
