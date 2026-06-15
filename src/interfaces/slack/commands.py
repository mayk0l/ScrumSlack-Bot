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
from src.application.excel_sync_service import ExcelSyncService
from src.infrastructure.repositories.sprint_repo import SprintRepositoryImpl
from src.infrastructure.repositories.metric_repo import MetricRepositoryImpl


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
        report_svc = ReportService(standup_svc, github_svc, risk_svc)
        sprint_svc = SprintService(sprint_repo, metric_repo)
        excel_svc = ExcelSyncService(
            "project_tracking.xlsx",
            metric_repo,
            risk_repo,
            sprint_repo
        )
        
        return {"standup": standup_svc, "risk": risk_svc, "report": report_svc, "sprint": sprint_svc, "excel": excel_svc, "member": member_repo}, session

    @app.command("/scrum")
    async def handle_scrum_command(ack, body, client):
        await ack()
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
        await say(text)

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
        await say(text)

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
        await say(text)

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
        await say(text)

    @app.command("/reporte")
    async def handle_reporte_command(ack, say):
        await ack()
        svcs, session = await _get_services()
        async with session:
            summary = await svcs["report"].generate_daily_summary(
                default_team_id, default_channel_id
            )
        await say(summary)

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
        await say(text)
