"""Módulo: commands.

Registro de slash commands de Slack.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.modals import build_standup_modal


def register_commands(app: AsyncApp, services: dict) -> None:
    """Registra todos los slash commands."""
    standup_service = services["standup_service"]
    report_service = services["report_service"]
    risk_service = services["risk_service"]
    default_team_id = services.get("default_team_id")
    default_channel_id = services.get("default_channel_id")

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
        risks = await risk_service.get_active_risks(default_team_id)
        if risks:
            lines = [f"• [{r.severity.value}] {r.description}" for r in risks]
            text = "⚠️ Riesgos activos:\n" + "\n".join(lines)
        else:
            text = "No hay riesgos activos. 🎉"
        await say(text)

    @app.command("/bloqueos")
    async def handle_bloqueos_command(ack, say):
        await ack()
        text = "Comando /bloqueos: implementación pendiente de filtro por día."
        await say(text)

    @app.command("/sprint")
    async def handle_sprint_command(ack, say):
        await ack()
        text = "Comando /sprint: implementación pendiente."
        await say(text)

    @app.command("/metricas")
    async def handle_metricas_command(ack, say):
        await ack()
        text = "Comando /metricas: implementación pendiente."
        await say(text)

    @app.command("/reporte")
    async def handle_reporte_command(ack, say):
        await ack()
        summary = await report_service.generate_daily_summary(
            default_team_id, default_channel_id
        )
        await say(summary)

    @app.command("/progreso")
    async def handle_progreso_command(ack, say):
        await ack()
        text = "Comando /progreso: implementación pendiente."
        await say(text)
